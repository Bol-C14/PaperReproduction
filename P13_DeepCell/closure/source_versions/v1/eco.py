"""Independent exact six-input ECO solver and external-output verifier.

Inference solver needs observed PM, golden AIG output, patch site and candidates.
It never reads original target pins/function, ancestry labels or node correspondence.
"""
import itertools,time
from data import PATTERNS,simulate_patched,eval_aig,direct


def obligations(case):
    observed=case['cut'];target=case['target'];po=observed['outputs'][0]
    rows=[]
    for pattern in PATTERNS:
        gold=eval_aig(case['aig'],pattern)[case['aig']['outputs'][0]]
        zero=simulate_patched(observed,pattern,target,0);one=simulate_patched(observed,pattern,target,1)
        choices=[v for v,out in [(0,zero[po]),(1,one[po])] if out==gold]
        if not choices:raise ValueError('single-site patch cannot solve observed circuit')
        rows.append((zero,None if len(choices)==2 else choices[0]))
    return rows


def netlist_for_table(inputs,table):
    nodes=[{'gate':'PI','candidate':v,'pins':[]} for v in inputs]
    def gate(kind,pins):
        i=len(nodes);nodes.append({'gate':kind,'pins':list(pins)});return i
    def both(xs):
        v=xs[0]
        for x in xs[1:]:v=gate('AND',[v,x])
        return v
    terms=[]
    for pattern,value in zip(itertools.product([0,1],repeat=len(inputs)),table):
        if value:
            terms.append(both([i if bit else gate('NOT',[i]) for i,bit in enumerate(pattern)]))
    if not terms:out=gate('AND',[0,gate('NOT',[0])])
    else:
        out=terms[0]
        for t in terms[1:]:out=gate('NOT',[gate('AND',[gate('NOT',[out]),gate('NOT',[t])])])
    return {'inputs':inputs,'nodes':nodes,'output':out,'gate_count':len(nodes)-len(inputs),
            'truth_table':table,'implementation':'explicit SOP in AND/NOT; not optimized technology cells'}


def synthesize(case,ranking,budget=3):
    started=time.perf_counter();constraints=obligations(case);candidate_evaluations=0
    for k in range(1,min(budget,len(ranking))+1):
        inputs=ranking[:k];mapping={};conflict=False
        for values,required in constraints:
            candidate_evaluations+=1
            if required is None:continue
            key=tuple(values[i] for i in inputs)
            if key in mapping and mapping[key]!=required:conflict=True;break
            mapping[key]=required
        if conflict:continue
        table=[mapping.get(x,0) for x in itertools.product([0,1],repeat=k)]
        patch=netlist_for_table(inputs,table)
        return {'success':True,'support_budget':k,'patch':patch,
                'seconds':time.perf_counter()-started,'candidate_pattern_checks':candidate_evaluations}
    return {'success':False,'seconds':time.perf_counter()-started,'candidate_pattern_checks':candidate_evaluations}


def eval_patch(patch,signals):
    values=[]
    for n in patch['nodes']:
        if n['gate']=='PI':values.append(signals[n['candidate']])
        elif n['gate']=='NOT':values.append(1-values[n['pins'][0]])
        else:values.append(values[n['pins'][0]] & values[n['pins'][1]])
    return values[patch['output']]


def verify(case,patch):
    # No truth_table field used: independently executes synthesized AND/NOT gates.
    for pattern in PATTERNS:
        values=simulate_patched(case['cut'],pattern,case['target'],lambda v:eval_patch(patch,v))
        got=values[case['cut']['outputs'][0]];expected=direct(case['spec'],pattern)
        if got!=expected:return {'passed':False,'counterexample':{'inputs':pattern,'expected':expected,'actual':got}}
    return {'passed':True,'patterns':64,'output_disagreements':0}


def metrics(ranking,positive):
    positive=set(positive);hits=0;ap=0
    for i,n in enumerate(ranking,1):
        if n in positive:hits+=1;ap+=hits/i
    return {'average_precision':ap/len(positive),'ancestry_recall_at3':len(set(ranking[:3])&positive)/len(positive)}
