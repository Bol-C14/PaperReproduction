"""Real egglog saturation with small external interval analysis and extraction."""
import itertools
import json
import math
import time
from collections import defaultdict
from egglog.bindings import EGraph


HEADER = '''
(datatype B (V String i64) (K i64 i64) (Add i64 B B) (Mul i64 B B)
 (Shr i64 B B) (Abs i64 B) (Mux i64 B B B) (Ult B i64)
 (Sge0 B) (Slt B i64) (And B B) (Neg i64 B) (Not B) (Assume i64 B B) (Cut i64 B) (Ext i64 B))
(rewrite (Add w a b) (Add w b a))
(rewrite (Mul w a b) (Mul w b a))
(rewrite (Add w a (K w 0)) (Ext w a))
(rewrite (Mul w a (K w 1)) (Ext w a))
(rewrite (Abs w (Abs w a)) (Abs w a))
(rewrite (Assume w (Assume w a c) c) (Assume w a c))
'''
CONTEXT = '''
(rewrite (Mux w c a b) (Mux w c (Assume w a c) (Assume w b (Not c))))
'''


def sx(t):
    if isinstance(t, str):
        return json.dumps(t)
    if isinstance(t, int):
        return str(t)
    return '(' + ' '.join([t[0], *(sx(x) for x in t[1:])]) + ')'


def width(t):
    return 1 if t[0] in ('Ult', 'Sge0', 'Slt', 'And', 'Not') else t[2] if t[0] == 'V' else t[1]


def cost(t, costs):
    op, w = t[0], width(t)
    child = [costs[sx(a)] for a in t[1:] if isinstance(a, tuple)]
    if op=='Assume':child=child[:1] # care metadata is erased, not another circuit
    area, delay = 0, 0
    lg = math.ceil(math.log2(max(2, w)))
    if op == 'Add': area, delay = w, lg + 1
    if op == 'Mul':
        p,q=width(t[2]),width(t[3])
        area,delay=p*q,math.ceil(math.log2(max(2,p)))+math.ceil(math.log2(max(2,q)))+1
    if op == 'Shr': area, delay = w*width(t[3]), width(t[3])
    if op == 'Mux': area, delay = w, 1
    if op == 'Abs': area, delay = 2*w, lg + 2
    if op == 'Neg': area, delay = w, lg + 1
    if op == 'And': area, delay = 1, 1
    if op in ('Ult', 'Sge0', 'Slt'): area, delay = width(t[1]), math.ceil(math.log2(max(2,width(t[1]))))+1
    return area + sum(a for a,d in child), delay + max([d for a,d in child] or [0])


def snapshot(e):
    data = json.loads(e.serialize([]).to_json())
    nodes = data['nodes']; groups = defaultdict(list)
    for key,n in nodes.items(): groups[n['eclass']].append((key,n))
    return data, nodes, groups


def extract(data, nodes, groups, weight):
    best = {}; costs={}
    for _ in range(200):
        changed=False
        for cl, items in sorted(groups.items()):
            for key,n in items:
                kids=[nodes[x]['eclass'] for x in n['children']]
                if any(k not in best for k in kids): continue
                if not kids:
                    try: term=json.loads(n['op'])
                    except json.JSONDecodeError: continue
                    ad=(0,0)
                else:
                    term=tuple([n['op']]+[best[k][2] for k in kids])
                    ad=cost(term,costs)
                score=ad[0]+weight*ad[1]
                entry=(score,len(sx(term)),term,ad)
                if cl not in best or entry[:2] < best[cl][:2]:
                    best[cl]=entry; costs[sx(term)]=ad;changed=True
        if not changed: break
    roots=[cl for cl,v in data['class_data'].items() if v.get('let')=='$root']
    return best, best[roots[0]][2], best[roots[0]][3]


def ranges(nodes, groups, best):
    """Inclusive unsigned hull per e-class; intersect sound alternatives."""
    bounds={cl:(0,(1<<width(b[2]))-1) for cl,b in best.items() if isinstance(b[2],tuple)}
    def restrict(c, value, guard):
        for _,g in groups[guard]:
            ch=[nodes[x]['eclass'] for x in g['children']]
            if g['op']=='Ult' and ch[0]==c:
                k=best[ch[1]][2]; value=(value[0],min(value[1],k-1))
            if g['op']=='Sge0' and ch[0]==c:
                w=width(best[c][2]); value=(value[0],min(value[1],(1<<(w-1))-1))
            if g['op']=='Not':
                for _,inner in groups[ch[0]]:
                    ic=[nodes[x]['eclass'] for x in inner['children']]
                    if inner['op']=='Ult' and ic[0]==c:
                        value=(max(value[0],best[ic[1]][2]),value[1])
        return value
    for _ in range(40):
        changed=False
        for cl,items in groups.items():
            if cl not in bounds: continue
            for _,n in items:
                op=n['op']; cs=[nodes[x]['eclass'] for x in n['children']]
                args=[best[c][2] for c in cs]; old=bounds[cl]; new=old
                full=(1<<width(best[cl][2]))-1
                if op=='K': new=(args[1],args[1])
                elif op in ('Add','Mul'):
                    a,b=bounds[cs[1]],bounds[cs[2]]
                    if op=='Add': lo,hi=a[0]+b[0],a[1]+b[1]
                    else: lo,hi=a[0]*b[0],a[1]*b[1]
                    if lo//(full+1)==hi//(full+1):new=(lo%(full+1),hi%(full+1))
                elif op=='Ext':new=bounds[cs[1]]
                elif op=='Cut':
                    a=bounds[cs[1]]
                    if a[0]//(full+1)==a[1]//(full+1):new=(a[0]%(full+1),a[1]%(full+1))
                elif op=='Shr':
                    a,b=bounds[cs[1]],bounds[cs[2]];new=(a[0]>>min(b[1],64),a[1]>>min(b[0],64))
                elif op=='Assume':new=restrict(cs[1],bounds[cs[1]],cs[2])
                elif op=='Mux':new=(min(bounds[cs[2]][0],bounds[cs[3]][0]),max(bounds[cs[2]][1],bounds[cs[3]][1]))
                new=(max(old[0],new[0]),min(old[1],new[1]))
                if new[0]>new[1]: continue # empty care contributes no narrowing in this pilot
                if new!=old: bounds[cl]=new;changed=True
        if not changed:break
    return bounds


original_ranges = ranges

def conjunction(*guards):
    """Canonical total-Boolean conjunction; bound duplicate context growth."""
    atoms = {}
    def add(t):
        if t[0] == 'And':
            add(t[1]); add(t[2])
        else:
            atoms[sx(t)] = t
    for guard in guards: add(guard)
    ordered = [atoms[k] for k in sorted(atoms)]
    result = ordered[0]
    for guard in ordered[1:]: result = ('And', result, guard)
    return result


def optimize(term,mode,domain="union",nested="legacy"):
    if nested not in ('legacy', 'propagate', 'combine'): raise ValueError(nested)
    global ranges
    if domain == "union":
        from union_domain import ranges_union
        ranges = ranges_union
    elif domain == "hull":
        ranges = original_ranges
    else: raise ValueError(domain)
    t=time.perf_counter();e=EGraph();e.set_num_threads(1)
    program=HEADER+(CONTEXT if mode not in ('agnostic','context_live') else '')+'\n(let $root '+sx(term)+')'
    e.parse_and_run_program(program)
    history=[];unions=[]
    for round_no in range(8):
        report=e.parse_and_run_program('(run 1)')
        data,nodes,groups=snapshot(e)
        best,_,_=extract(data,nodes,groups,0)
        bounds=ranges(nodes,groups,best)
        commands=set()
        live={cl:{cl} for cl in groups}
        if mode=='context_live':
            for _ in range(len(groups)):
                changed=False
                for cl,items in groups.items():
                    new=live[cl].union(*(live[nodes[x]['eclass']] for _,n in items for x in n['children'] if nodes[x]['eclass'] in bounds))
                    if new!=live[cl]:live[cl]=new;changed=True
                if not changed:break
            for cl,items in groups.items():
                for _,n in items:
                    if n['op']!='Mux':continue
                    cs=[nodes[x]['eclass'] for x in n['children']]
                    w,condition,a,b=[best[c][2] for c in cs]
                    aa=('Assume',w,a,condition) if live[cs[1]]&live[cs[2]] else a
                    bb=('Assume',w,b,('Not',condition)) if live[cs[1]]&live[cs[3]] else b
                    if aa!=a or bb!=b:commands.add('(union '+sx(('Mux',w,condition,a,b))+' '+sx(('Mux',w,condition,aa,bb))+')')
        if mode!='agnostic':
            for cl,items in groups.items():
                for _,n in items:
                    if n['op']!='Assume':continue
                    cs=[nodes[x]['eclass'] for x in n['children']]
                    if mode=='context_live' and not (live[cs[1]]&live[cs[2]]):continue
                    condition=best[cs[2]][2]
                    for _,inner in groups[cs[1]]:
                        ic=[nodes[x]['eclass'] for x in inner['children']]
                        ops=[best[c][2] for c in ic]
                        original=('Assume',width(best[cs[1]][2]),tuple([inner['op']]+ops),condition)
                        if nested!='legacy' and inner['op']=='Mux':
                            w,c,a,b=ops
                            target=('Mux',w,c,('Assume',w,a,condition),('Assume',w,b,condition))
                            commands.add('(union '+sx(original)+' '+sx(target)+')')
                        if nested=='combine' and inner['op']=='Assume':
                            w,a,guard=ops
                            target=('Assume',w,a,conjunction(guard,condition))
                            commands.add('(union '+sx(original)+' '+sx(target)+')')
                        if inner['op'] not in ('Add','Mul','Shr','Abs','Neg'):continue
                        original=('Assume',ops[0],tuple([inner['op']]+ops),condition)
                        target=tuple([inner['op'],ops[0]]+[('Assume',width(a),a,condition) for a in ops[1:]])
                        commands.add('(union '+sx(original)+' '+sx(target)+')')
        if mode!='context_no_vra':
            for cl,items in groups.items():
                if cl not in bounds:continue
                for _,n in items:
                    cs=[nodes[x]['eclass'] for x in n['children']]
                    if not cs or n['op'] not in ('Add','Mul','Shr','Abs','Neg'):continue
                    args=[best[c][2] for c in cs];original=tuple([n['op']]+args);w=args[0]
                    target=None
                    if n['op']=='Abs' and bounds[cs[1]][1] < (1<<(w-1)):target=args[1]
                    if n['op']=='Shr':
                        bw=max(1,bounds[cs[2]][1].bit_length())
                        if bw<width(args[2]):target=('Shr',w,args[1],('Cut',bw,args[2]))
                    if n['op'] in ('Add','Mul'):
                        bw=max(1,bounds[cl][1].bit_length())
                        aw=max(1,bounds[cs[1]][1].bit_length()); bww=max(1,bounds[cs[2]][1].bit_length())
                        if bw<w or aw<width(args[1]) or bww<width(args[2]):target=('Ext',w,(n['op'],bw,('Cut',min(aw,bw),args[1]),('Cut',min(bww,bw),args[2])))
                    if target is not None:commands.add('(union '+sx(original)+' '+sx(target)+')')
        if commands:
            e.parse_and_run_program('\n'.join(sorted(commands)));unions.extend(sorted(commands))
        history.append({'round':round_no+1,'nodes':len(nodes),'dynamic_unions':len(commands),'report':str(report)})
        if len(nodes)>5000:raise RuntimeError('node budget exceeded')
    data,nodes,groups=snapshot(e)
    out=[]
    for weight in (0,8):
        _,chosen,ad=extract(data,nodes,groups,weight)
        out.append({'weight':weight,'term':chosen,'proxy_area':ad[0],'proxy_delay':ad[1]})
    return {'mode':mode,'nested':nested,'history':history,'egraph':data,'dynamic_unions':unions,'variants':out,'wall_seconds':time.perf_counter()-t,'program':program}
