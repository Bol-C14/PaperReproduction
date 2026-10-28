"""Independent output checker: no training/solver imports or cell truth-table lookup.

Uses direct Boolean cell semantics, saved AND/NOT patch gates and parent truth
signatures. Covers every emitted main-run patch, not just a selected example.
"""
import argparse,copy,itertools,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent


def cell(kind,values):
    if kind=='NOT':return 1-values[0]
    if kind=='AND2':return values[0]&values[1]
    if kind=='NAND2':return 1-(values[0]&values[1])
    if kind=='OR2':return values[0]|values[1]
    if kind=='NOR2':return 1-(values[0]|values[1])
    if kind=='XOR2':return values[0]^values[1]
    if kind=='XNOR2':return 1-(values[0]^values[1])
    if kind=='MUX3':return values[2] if values[0] else values[1]
    if kind=='MAJ3':return int(sum(values)>=2)
    raise ValueError(kind)


def patch_value(patch,values):
    def evaluate(i):
        n=patch['nodes'][i]
        if n['gate']=='PI':return values[n['candidate']]
        return cell('AND2' if n['gate']=='AND' else 'NOT',[evaluate(p) for p in n['pins']])
    return evaluate(patch['output'])


def check(c,patch,signature):
    # Uses explicit cell functions, not the solver's generic table-based evaluator.
    for index,pattern in enumerate(itertools.product([0,1],repeat=6)):
        cache=dict(enumerate(pattern));visiting=set()
        class Signals:
            def __getitem__(self,i):return evaluate(i)
        def evaluate(i):
            if i in cache:return cache[i]
            if i in visiting:raise ValueError('cycle in patched graph')
            visiting.add(i);n=c['cut']['nodes'][i]
            value=patch_value(patch,Signals()) if i==c['target'] else cell(n['cell'],[evaluate(p) for p in n['pins']])
            cache[i]=value;visiting.remove(i);return value
        actual=evaluate(c['cut']['outputs'][0]);expected=int(signature[index])
        if actual!=expected:return {'passed':False,'case':c['id'],'pattern':list(pattern),'expected':expected,'actual':actual}
    return {'passed':True,'patterns':64}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',default='main');args=parser.parse_args()
    cases={c['id']:c for c in json.loads((ROOT/'results/corpus.json').read_text())}
    manifest=json.loads((ROOT/'results/corpus_manifest.json').read_text())
    truth={x['parent']:x['truth_signature'] for x in manifest['parents']}
    records=[]
    for p in sorted((ROOT/'results'/args.directory).glob('*.json')):
        data=json.loads(p.read_text())
        if 'downstream' in data:
            for split,report in data['downstream'].items():
                records.extend((p.name,split,r) for r in report['records'] if r['success'])
        elif p.name=='baselines.json':
            for mode,report in data.items():
                if 'records' in report:records.extend((p.name,mode,r) for r in report['records'] if r['success'])
    checked=[];patterns=0
    for file,arm,r in records:
        c=cases[r['id']];result=check(c,r['patch'],truth[c['parent']])
        assert result['passed'],(file,arm,result);patterns+=64
        checked.append({'file':file,'view_or_baseline':arm,'case':r['id'],'gate_count':r['patch']['gate_count'],'passed':True})
    assert checked,'no actual patches emitted'
    # Independent corruption and metadata-independence controls.
    _,_,r=records[0];c=cases[r['id']];bad=copy.deepcopy(r['patch'])
    bad['nodes'].append({'gate':'NOT','pins':[bad['output']]});bad['output']=len(bad['nodes'])-1
    negative=check(c,bad,truth[c['parent']]);assert not negative['passed']
    no_table=copy.deepcopy(r['patch']);no_table.pop('truth_table',None)
    assert check(c,no_table,truth[c['parent']])['passed']
    result={'independent_verifier':'recursive patch-gate evaluator + explicit Boolean cell semantics + saved direct-family truth signature',
            'directory':args.directory,'patches_checked':len(checked),'primary_input_assignments_checked':patterns,
            'all_passed':True,'negative_inverted_patch_control':negative,'patch_truth_table_metadata_not_used':True,'checked':checked}
    (ROOT/'results'/args.directory/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='checked'},indent=2))


if __name__=='__main__':main()
