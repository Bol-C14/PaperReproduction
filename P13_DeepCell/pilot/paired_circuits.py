"""Explicit tiny Boolean-cell PM -> AND/NOT lowering. No EDA/library claims.

Pin order: leftmost pin is the most significant bit of the truth-table index.
The independent parent oracle does not call these truth tables or lowering.
"""
import copy
import itertools

TABLES = {
    'AND2': '0001', 'OR2': '0111', 'NAND2': '1110', 'NOT': '10',
    'XOR2': '0110', 'MUX3': '00110101', 'MAJ3': '00010111',
}
# MUX truth table uses pins [selector, a, b]: selector ? b : a.


def parent_oracle(parent, values):
    if parent == 'xor':
        a,b = values
        return (a and not b) or (not a and b)
    if parent == 'mux':
        s,a,b = values
        return b if s else a
    if parent == 'majority':
        a,b,c = values
        return int(a)+int(b)+int(c) >= 2
    raise ValueError(parent)


def node(cell, pins):
    return {'cell': cell, 'pins': list(pins), 'tt': TABLES[cell]}


def make_pm(parent, variant):
    n = 2 if parent == 'xor' else 3
    nodes = [{'cell': 'PI', 'name': f'x{i}', 'pins': []} for i in range(n)]
    if variant == 0:
        nodes.append(node({'xor':'XOR2','mux':'MUX3','majority':'MAJ3'}[parent], range(n)))
    elif parent == 'xor':
        nodes += [node('NAND2',[0,1]), node('NAND2',[0,2]),
                  node('NAND2',[1,2]), node('NAND2',[3,4])]
    elif parent == 'mux':
        nodes += [node('NOT',[0]), node('AND2',[3,1]),
                  node('AND2',[0,2]), node('OR2',[4,5])]
    else:
        nodes += [node('AND2',[0,1]), node('AND2',[0,2]),
                  node('AND2',[1,2]), node('OR2',[3,4]), node('OR2',[6,5])]
    return {'nodes':nodes, 'inputs':list(range(n)), 'outputs':[len(nodes)-1]}


def lower_pm(pm):
    nodes=[]
    pm_to_aig={}
    for p in pm['inputs']:
        pm_to_aig[p]=len(nodes)
        nodes.append({'gate':'PI','name':pm['nodes'][p]['name'],'pins':[]})
    def gate(kind,pins):
        index=len(nodes); nodes.append({'gate':kind,'pins':list(pins)}); return index
    def both(xs):
        result=xs[0]
        for x in xs[1:]: result=gate('AND',[result,x])
        return result
    def either(a,b):
        return gate('NOT',[gate('AND',[gate('NOT',[a]),gate('NOT',[b])])])
    for i,p in enumerate(pm['nodes']):
        if p['cell']=='PI': continue
        inputs=[pm_to_aig[j] for j in p['pins']]
        terms=[]
        for bits,bit in zip(itertools.product([0,1],repeat=len(inputs)),p['tt']):
            if bit=='1':
                terms.append(both([x if b else gate('NOT',[x]) for x,b in zip(inputs,bits)]))
        if not terms: raise ValueError('constant cells excluded by protocol')
        out=terms[0]
        for term in terms[1:]: out=either(out,term)
        pm_to_aig[i]=out
    aig={'nodes':nodes,'inputs':list(range(len(pm['inputs']))),
         'outputs':[pm_to_aig[i] for i in pm['outputs']]}
    return aig,{str(k):v for k,v in pm_to_aig.items()}


def validate_graph(graph, view):
    for i,n in enumerate(graph['nodes']):
        if any(not 0<=p<i for p in n['pins']): raise ValueError('not topologically ordered DAG')
        if view=='pm' and n['cell']!='PI':
            if len(n['tt'])!=2**len(n['pins']): raise ValueError('invalid cell table length')
            if 64%len(n['tt']): raise ValueError('table cannot repeat to 64 bits')
        if view=='aig':
            assert len(n['pins'])=={'PI':0,'AND':2,'NOT':1}[n['gate']]
    assert graph['inputs']==list(range(len(graph['inputs'])))
    assert all(0<=i<len(graph['nodes']) for i in graph['outputs'])


def eval_pm(pm, pattern):
    values=list(map(int,pattern))
    for n in pm['nodes'][len(pattern):]:
        index=0
        for p in n['pins']: index=2*index+values[p]
        values.append(int(n['tt'][index]))
    return values


def eval_aig(aig, pattern):
    values=list(map(int,pattern))
    for n in aig['nodes'][len(pattern):]:
        pins=[values[p] for p in n['pins']]
        values.append(int(all(pins)) if n['gate']=='AND' else 1-pins[0])
    return values


def verify_pair(pair):
    pm,aig=pair['pm'],pair['aig']
    validate_graph(pm,'pm'); validate_graph(aig,'aig')
    if set(pair['pm_to_aig']) != {str(i) for i in range(len(pm['nodes']))}:
        raise ValueError('incomplete PM node correspondence')
    if any(not 0<=a<len(aig['nodes']) for a in pair['pm_to_aig'].values()):
        raise ValueError('out-of-range correspondence')
    if [pm['nodes'][i]['name'] for i in pm['inputs']] != [aig['nodes'][i]['name'] for i in aig['inputs']]:
        raise ValueError('PI correspondence mismatch')
    pm_rows=[]; aig_rows=[]
    for pattern in itertools.product([0,1],repeat=len(pm['inputs'])):
        pvals=eval_pm(pm,pattern);avals=eval_aig(aig,pattern)
        expected=int(parent_oracle(pair['parent'],pattern))
        if pvals[pm['outputs'][0]]!=expected or avals[aig['outputs'][0]]!=expected:
            raise ValueError('functional mismatch against independent parent oracle')
        for p,a in pair['pm_to_aig'].items():
            if pvals[int(p)]!=avals[a]: raise ValueError('internal correspondence mismatch')
        pm_rows.append(pvals);aig_rows.append(avals)
    pair['exact_probabilities']={
        'pm':[sum(col)/len(pm_rows) for col in zip(*pm_rows)],
        'aig':[sum(col)/len(aig_rows) for col in zip(*aig_rows)],
        'method':'exhaustive enumeration on synthetic cells; not paper corpus labels'}
    return len(pm_rows)


def verify_splits(pairs):
    sets={name:{p['parent'] for p in pairs if p['split']==name}
          for name in ['train','validation','test']}
    for a,b in itertools.combinations(sets,2):
        if sets[a]&sets[b]: raise ValueError('parent overlap')
    return {k:sorted(v) for k,v in sets.items()}


def build_and_validate():
    pairs=[]; results=[]
    for parent,split in [('xor','train'),('mux','validation'),('majority','test')]:
        for variant in [0,1]:
            pm=make_pm(parent,variant);aig,mapping=lower_pm(pm)
            pair={'id':f'{parent}_v{variant}','parent':parent,'split':split,
                  'provenance':'new synthetic teaching circuit, no external RTL',
                  'pm':pm,'aig':aig,'pm_to_aig':mapping}
            patterns=verify_pair(pair);pairs.append(pair)
            results.append({'id':pair['id'],'patterns':patterns,'pm_nodes':len(pm['nodes']),
                            'aig_nodes':len(aig['nodes']),'output_and_mapped_internal_disagreements':0})
    sets=verify_splits(pairs)
    negative={}
    wrong=copy.deepcopy(pairs[2]);wrong['aig']=copy.deepcopy(pairs[4]['aig'])
    wrong['pm_to_aig']=copy.deepcopy(pairs[4]['pm_to_aig'])
    try: verify_pair(wrong)
    except ValueError as e: negative['mismatched_pair_rejected']=str(e)
    else: raise AssertionError('mismatched pair accepted')
    contaminated=copy.deepcopy(pairs); contaminated[-1]['split']='train'
    try: verify_splits(contaminated)
    except ValueError as e: negative['parent_contamination_rejected']=str(e)
    else: raise AssertionError('parent overlap accepted')
    pin_corruption=copy.deepcopy(pairs[2]);pin_corruption['pm']['nodes'][-1]['pins']=[1,0,2]
    try: verify_pair(pin_corruption)
    except ValueError as e: negative['mux_pin_corruption_rejected']=str(e)
    else: raise AssertionError('corrupt port order accepted')
    return pairs,{'pairs':results,'split_parents':sets,'negative_controls':negative}


if __name__=='__main__':
    import json,pathlib
    root=pathlib.Path(__file__).resolve().parent/'results';root.mkdir(exist_ok=True)
    pairs,results=build_and_validate()
    (root/'paired_circuits.json').write_text(json.dumps(pairs,indent=2)+'\n')
    (root/'integrity_results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
