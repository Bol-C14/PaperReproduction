"""Paper-derived binary DAG selection/topology/arrival constraints via Z3."""
import time
from collections import defaultdict
import z3
from engine import extract, cost, sx


def select(data):
    nodes=data['nodes'];groups=defaultdict(list)
    for key,n in nodes.items():groups[n['eclass']].append((key,n))
    best,_,_=extract(data,nodes,groups,0)
    classes=sorted(c for c,v in data['class_data'].items() if v['type']=='B')
    root=next(c for c,v in data['class_data'].items() if v.get('let')=='$root')
    active={c:z3.Bool('active_'+c) for c in classes}
    rank={c:z3.Int('rank_'+c) for c in classes};arrival={c:z3.Int('d_'+c) for c in classes}
    chosen={k:z3.Bool('n_'+k) for c in classes for k,n in groups[c]}
    details={};constraints=[];areas=[];N=len(classes)
    # Generous valid big-M bound from number of nodes and maximum intrinsic delay.
    max_delay=1
    for c in classes:
        for key,n in groups[c]:
            cs=[nodes[k]['eclass'] for k in n['children']]
            term=tuple([n['op']]+[best[k][2] for k in cs])
            ad=cost(term,{sx(a):(0,0) for a in term[1:] if isinstance(a,tuple)})
            max_delay=max(max_delay,ad[1]);details[key]=(term,ad,[k for k in cs if k in active])
    M=max_delay*(N+1)
    for c in classes:
        constraints.extend([rank[c]>=0,rank[c]<N,arrival[c]>=0,arrival[c]<=M])
        constraints.append(z3.Sum([z3.If(chosen[k],1,0) for k,n in groups[c]])==z3.If(active[c],1,0))
        for key,n in groups[c]:
            term,(area,delay),children=details[key];sel=chosen[key]
            for child in children:
                constraints.extend([z3.Implies(sel,active[child]),z3.Implies(sel,rank[c]>rank[child])])
            data_children=children[:1] if n['op']=='Assume' else children
            for child in data_children:constraints.append(arrival[c]>=arrival[child]+delay-M*z3.If(sel,0,1))
            if not data_children:constraints.append(arrival[c]>=delay-M*z3.If(sel,0,1))
            areas.append(z3.If(sel,area,0))
    constraints.append(active[root]);area=z3.Sum(areas)
    def solve(target=None):
        t=time.perf_counter();o=z3.Optimize();o.set(timeout=5000);o.add(*constraints)
        if target is None:objective=o.minimize(arrival[root])
        else:
            o.add(arrival[root]<=target);objective=o.minimize(area)
        status=o.check();result={'status':str(status),'wall_seconds':time.perf_counter()-t,'target':target}
        if status!=z3.sat:result['reason']=o.reason_unknown();return result,None
        result.update(lower=str(o.lower(objective)),upper=str(o.upper(objective)))
        if result['lower']!=result['upper']:result['error']='optimality not established';return result,None
        model=o.model();result.update(area=model.eval(area).as_long(),delay=model.eval(arrival[root]).as_long())
        mapping={c:next(k for k,n in groups[c] if z3.is_true(model.eval(chosen[k]))) for c in classes if z3.is_true(model.eval(active[c]))}
        def build(c):
            if c not in active:return best[c][2]
            n=nodes[mapping[c]]
            return tuple([n['op']]+[build(nodes[x]['eclass']) for x in n['children']])
        result['selected_node_ids']=list(mapping.values())
        return result,build(root)
    initial,_=solve();reports=[initial];variants=[]
    if 'error' in initial or 'delay' not in initial:raise RuntimeError('minimum delay extraction failed: '+str(initial))
    for multiplier in (1,2):
        r,term=solve(initial['delay']*multiplier);reports.append(r)
        if term is None:raise RuntimeError('area extraction failed: '+str(r))
        variants.append({'weight':multiplier,'term':term,'proxy_area':r['area'],'proxy_delay':r['delay'],'delay_target':r['target']})
    return variants,reports
