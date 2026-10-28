"""Synthetic, family-disjoint teaching corpus; two independent Boolean evaluators."""
import copy,hashlib,itertools,json,random,sys,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'pilot'))
from paired_circuits import lower_pm,eval_pm,eval_aig,validate_graph,TABLES
TT=dict(TABLES, XNOR2='1001', NOR2='1000')
PATTERNS=list(itertools.product([0,1],repeat=6))


def direct(spec,x):
    z=[bool(x[i]) for i in spec['perm']];f=spec['family'];mode=spec['mode']
    if f=='parity':
        y=sum(z[:spec['k']])%2!=0
    elif f=='muxbank':
        a=z[2] if z[0] else z[1];b=z[5] if z[3] else z[4]
        y=(a!=b) if mode==0 else ((a and b) if mode==1 else (a or b))
    elif f=='arithmetic':
        carry=(int(z[0])+int(z[2])+int(z[4]))>=2
        total=int(z[1])+int(z[3])+int(carry)
        y=(total%2!=0) != z[5]
    elif f=='conditional':
        y=(z[2] and z[3]) if (z[0]!=z[1]) else (z[4] or z[5])
    elif f=='majority':
        a=sum(z[:3])>=2;b=sum(z[3:])>=2;c=z[0]!=z[3]
        y=sum([a,b,c])>=2
    elif f=='comparator':
        a=4*int(z[0])+2*int(z[1])+int(z[2]);b=4*int(z[3])+2*int(z[4])+int(z[5]);y=a>b
    else:raise ValueError(f)
    return int(not y if spec['neg'] else y)


def make_base(spec):
    nodes=[{'cell':'PI','name':f'x{i}','pins':[]} for i in range(6)]
    z=spec['perm'];f=spec['family'];mode=spec['mode']
    def add(c,*pins):
        i=len(nodes);nodes.append({'cell':c,'pins':list(pins),'tt':TT[c]});return i
    # Unused existing logic is a legitimate distractor candidate pool.
    add('AND2',z[0],z[3]);add('OR2',z[1],z[4]);add('XOR2',z[2],z[5])
    if f=='parity':
        y=z[0]
        for v in z[1:spec['k']]:y=add('XOR2',y,v)
    elif f=='muxbank':
        a=add('MUX3',*z[:3]);b=add('MUX3',*z[3:]);y=add(['XOR2','AND2','OR2'][mode],a,b)
    elif f=='arithmetic':
        a=add('XOR2',z[0],z[2]);add('XOR2',a,z[4])
        carry=add('MAJ3',z[0],z[2],z[4]);b=add('XOR2',z[1],z[3]);y=add('XOR2',add('XOR2',b,carry),z[5])
    elif f=='conditional':
        s=add('XOR2',z[0],z[1]);a=add('AND2',z[2],z[3]);b=add('OR2',z[4],z[5]);y=add('MUX3',s,b,a)
    elif f=='majority':
        a=add('MAJ3',*z[:3]);b=add('MAJ3',*z[3:]);c=add('XOR2',z[0],z[3]);y=add('MAJ3',a,b,c)
    else:
        g2=add('AND2',z[0],add('NOT',z[3]));e2=add('XNOR2',z[0],z[3])
        g1=add('AND2',z[1],add('NOT',z[4]));e1=add('XNOR2',z[1],z[4]);g0=add('AND2',z[2],add('NOT',z[5]))
        y=add('OR2',g2,add('AND2',e2,add('OR2',g1,add('AND2',e1,g0))))
    if spec['neg']:y=add('NOT',y)
    return {'nodes':nodes,'inputs':list(range(6)),'outputs':[y]}


def ancestors(pm,target):
    out=set();stack=list(pm['nodes'][target]['pins'])
    while stack:
        p=stack.pop()
        if p not in out:out.add(p);stack.extend(pm['nodes'][p]['pins'])
    return out


def variant(pm,seed):
    rng=random.Random(seed);new=copy.deepcopy(pm['nodes'][:6]);mapping={i:i for i in range(6)}
    for i,n in enumerate(pm['nodes'][6:],6):
        n=copy.deepcopy(n);n['pins']=[mapping[p] for p in n['pins']]
        j=len(new);new.append(n)
        if rng.random()<.35:
            new.append({'cell':'NOT','pins':[j],'tt':TT['NOT']});j+=1
            new.append({'cell':'NOT','pins':[j],'tt':TT['NOT']});j+=1
        mapping[i]=j
    return {'nodes':new,'inputs':list(range(6)),'outputs':[mapping[p] for p in pm['outputs']]},mapping


def observed(pm,target):
    cut=copy.deepcopy(pm);cut['nodes'][target]={'cell':'PI','name':'unknown_patch','pins':[]}
    return cut


def simulate_patched(pm,pattern,target,value):
    # Independent scalar cell evaluator used by solver and verifier.
    v=list(pattern)
    for i,n in enumerate(pm['nodes'][6:],6):
        if i==target:v.append(int(value(v) if callable(value) else value));continue
        idx=sum(v[p]<<(len(n['pins'])-1-j) for j,p in enumerate(n['pins']))
        v.append(int(n['tt'][idx]))
    return v


def legal_candidates(pm,target):
    desc={target}
    for i,n in enumerate(pm['nodes']):
        if any(p in desc for p in n['pins']):desc.add(i)
    return [i for i in range(len(pm['nodes'])) if i not in desc]


def validate_case(case):
    pm=case['pm'];aig=case['aig'];target=case['target'];pn=[];an=[]
    validate_graph(pm,'pm');validate_graph(aig,'aig')
    affected=0
    for x in PATTERNS:
        p=eval_pm(pm,x);a=eval_aig(aig,x);truth=direct(case['spec'],x)
        assert p[pm['outputs'][0]]==a[aig['outputs'][0]]==truth
        assert all(p[int(k)]==a[v] for k,v in case['pm_to_aig'].items())
        affected+=simulate_patched(case['cut'],x,target,0)[pm['outputs'][0]]!=truth
        pn.append(p);an.append(a)
    assert affected>0,'inert patch site'
    case['prob_pm']=[sum(c)/64 for c in zip(*pn)];case['prob_aig']=[sum(c)/64 for c in zip(*an)]
    case['legal_candidates']=legal_candidates(case['cut'],target)
    case['ancestry']=sorted(ancestors(pm,target))
    assert set(case['ancestry'])<=set(case['legal_candidates'])
    return len(aig['nodes'])


def build(small=False):
    rng=random.Random(808);cases=[];seen=set();manifest=[]
    families=[('parity','train',24),('muxbank','train',24),('arithmetic','train',24),
              ('conditional','validation',12),('majority','test',12),('comparator','test',12)]
    for family,split,count in families:
        accepted=0;attempt=0
        while accepted<count:
            attempt+=1
            if attempt>10000:raise RuntimeError('family diversity bound')
            perm=list(range(6));rng.shuffle(perm)
            spec={'family':family,'perm':perm,'k':rng.choice([3,4,5]),'mode':rng.randrange(3),'neg':rng.randrange(2)}
            sig=''.join(str(direct(spec,x)) for x in PATTERNS)
            if sig in seen:continue
            pm=make_base(spec);reach=ancestors(pm,pm['outputs'][0])|set(pm['outputs'])
            candidates=[i for i in reach if i>=9 and len(pm['nodes'][i]['pins'])>=2]
            rng.shuffle(candidates)
            target=next((t for t in candidates if any(simulate_patched(observed(pm,t),x,t,0)[pm['outputs'][0]]!=direct(spec,x) for x in PATTERNS)),None)
            if target is None:continue
            seen.add(sig);parent=f'{family}_{accepted:03d}';accepted+=1
            manifest.append({'parent':parent,'family':family,'split':split,'truth_signature':sig,'spec':spec})
            for vi in [0,1]:
                if vi:pv,mapping=variant(pm,int(hashlib.sha256(parent.encode()).hexdigest()[:8],16));t=mapping[target]
                else:pv=pm;t=target
                av,pmmap=lower_pm(pv)
                c={'id':f'{parent}_v{vi}','parent':parent,'family':family,'split':split,'spec':spec,
                   'pm':pv,'aig':av,'pm_to_aig':pmmap,'target':t,'cut':observed(pv,t)}
                validate_case(c);cases.append(c)
    splitparents={s:{c['parent'] for c in cases if c['split']==s} for s in ['train','validation','test']}
    for a,b in itertools.combinations(splitparents,2):assert not(splitparents[a]&splitparents[b])
    assert len(seen)==len(manifest)
    # Negative functional/parent controls, distinct from the prior pilot fixture.
    x=copy.deepcopy(next(c for c in cases if c['family']=='conditional'))
    cell=next(n for n in x['pm']['nodes'] if n['cell']=='MUX3');cell['pins'][0],cell['pins'][1]=cell['pins'][1],cell['pins'][0]
    try:validate_case(x)
    except AssertionError:pass
    else:raise AssertionError('corrupt MUX accepted')
    if small:
        cases=[c for s in ['train','validation','test'] for c in [x for x in cases if x['split']==s][:4]]
    return cases,{'parents':manifest,'family_splits':families,'case_count':len(cases),'unique_parent_functions':len(seen),
       'all_truth_signatures_disjoint':True,'all_parent_splits_disjoint':True,'all_family_splits_disjoint':True,
       'patterns_per_case':64,'max_combined_tokens':max(len(c['pm']['nodes'])+len(c['aig']['nodes']) for c in cases),
       'negative_corrupt_mux_rejected':True}


if __name__=='__main__':
    cases,manifest=build();out=pathlib.Path(__file__).parent/'results';out.mkdir(exist_ok=True)
    (out/'corpus.json').write_text(json.dumps(cases,indent=2)+'\n');(out/'corpus_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='parents'},indent=2))
