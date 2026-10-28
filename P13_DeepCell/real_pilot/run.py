"""Frozen real Liberty / public netlist ECO pilot; never trains a model."""
import copy,hashlib,itertools,json,os,pathlib,re,resource,subprocess,sys,time
from types import SimpleNamespace
import numpy as np
import torch
ROOT=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT.parent/'closure/external'),str(ROOT.parent/'closure'),str(ROOT.parent/'pilot')]
import flow
from train import Pipeline,graph_fields,sid
from data import legal_candidates
from eco import netlist_for_table

def blocks(text,kind):
    for m in re.finditer(r'\b'+kind+r'\s*\(\s*([^()]+?)\s*\)\s*\{',text):
        depth=1;i=m.end()
        while depth:
            depth+=(text[i]=='{')-(text[i]=='}');i+=1
        yield m[1].strip('"'),text[m.end():i-1]

def boolean(expr,values):
    tokens=re.findall(r'[A-Za-z_][A-Za-z_0-9]*|[!&|^()*+01]',expr);i=0
    assert ''.join(tokens)==re.sub(r'\s+','',expr),expr
    def atom():
        nonlocal i
        t=tokens[i];i+=1
        if t=='!':return 1-atom()
        if t=='(':
            v=combine(0);assert tokens[i]==')';i+=1;return v
        return int(t) if t in ['0','1'] else values[t]
    priorities=[['|','+'],['^'],['&','*']]
    def combine(level):
        nonlocal i
        if level==3:return atom()
        v=combine(level+1)
        while i<len(tokens) and tokens[i] in priorities[level]:
            op=tokens[i];i+=1;b=combine(level+1)
            v=(v|b) if op in ['|','+'] else (v^b) if op=='^' else (v&b)
        return v
    result=combine(0);assert i==len(tokens);return result

def library(path):
    cells={};evidence=[]
    for name,body in blocks(path.read_text(),'cell'):
        if re.search(r'\b(?:ff|latch)\s*\(',body):continue  # Sequential cells are outside combinational mapping.
        pins=list(blocks(body,'pin'));inputs=[n for n,b in pins if re.search(r'direction\s*:\s*input\s*;',b)]
        outputs=[(n,b) for n,b in pins if re.search(r'direction\s*:\s*output\s*;',b)]
        if len(outputs)!=1:continue
        out,b=outputs[0];m=re.search(r'function\s*:\s*"([^"]+)"',b)
        if not m:continue
        assert len(inputs)<=6
        expr=m[1]
        if set(re.findall(r'[A-Za-z_][A-Za-z_0-9]*',expr))-set(inputs):continue  # Internal state variables, not combinational cells.
        table=''.join(str(boolean(expr,dict(zip(inputs,bits)))) for bits in itertools.product([0,1],repeat=len(inputs)))
        cells[name]=(inputs,table,out);evidence.append(dict(cell=name,pin_order=inputs,output=out,function=expr,truth_table=table))
    return cells,evidence

def pm_values(pm,patterns,target=None,bit=0):
    vals=[patterns[:,i] for i in range(patterns.shape[1])]
    for i,node in enumerate(pm['nodes'][patterns.shape[1]:],patterns.shape[1]):
        if i==target:vals.append(np.full(len(patterns),bit,dtype=np.uint8));continue
        key=np.zeros(len(patterns),dtype=np.int64)
        for p in node['pins']:key=key*2+vals[p]
        vals.append(np.array(list(node['tt']),dtype=np.uint8)[key])
    return np.stack(vals,1)

def aig_values(aig,patterns):
    vals=[patterns[:,i] for i in range(patterns.shape[1])]
    for n in aig['nodes'][patterns.shape[1]:]:
        vals.append(vals[n['pins'][0]] & vals[n['pins'][1]] if n['gate']=='AND' else 1-vals[n['pins'][0]])
    return np.stack(vals,1)

def main():
    start=time.time();torch.set_num_threads(2);torch.set_num_interop_threads(1)
    result=ROOT/'results';result.mkdir(exist_ok=True);logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    abc_bin=pathlib.Path(os.environ['DEEPCELL_ABC']);commands=[]
    def abc(command,tag):
        p=subprocess.run([str(abc_bin),'-s','-c',command],capture_output=True,text=True,timeout=60)
        output=p.stdout+p.stderr;(logs/(tag+'.log')).write_text(output)
        commands.append(dict(command=command.replace(str(ROOT),'$PILOT'),returncode=p.returncode,log='logs/'+tag+'.log'))
        assert p.returncode==0,output
        return output
    cells,evidence=library(ROOT/'assets/nangate45.lib');(result/'cell_semantics.json').write_text(json.dumps(evidence,indent=2)+'\n')
    original=ROOT/'assets/int2float.blif';mapped=result/'mapped.blif';bench=result/'golden.bench'
    abc(f'read_lib -G 250 {ROOT}/assets/nangate45.lib; read_blif {original}; strash; map; write_blif {mapped}; strash; write_bench -l {bench}; print_stats','mapping')
    assert mapped.exists() and bench.exists()
    assert 'Networks are equivalent' in abc(f'read_lib -G 250 {ROOT}/assets/nangate45.lib; cec {original} {mapped}','mapping_cec')
    # Rename only output-pin binding for the inherited explicit mapped-BLIF reader.
    lines=[];used=set()
    for line in mapped.read_text().splitlines():
        words=line.split()
        if words and words[0]=='.gate':
            name=words[1];used.add(name);order,table,out=cells[name]
            flow.LIB[name]=(order,table);line=re.sub(r'\b'+re.escape(out)+r'=', 'O=',line)
        lines.append(line)
    normalized=result/'mapped_normalized.blif';normalized.write_text('\n'.join(lines)+'\n')
    src=flow.read_blif(original);mp=flow.read_blif(normalized);pm=flow.graph_pm(mp);aig=flow.graph_bench(bench,mp['inputs'])
    assert len(pm['inputs'])==11 and mp['outputs']==src['outputs']==aig['output_names']
    patterns=np.array(list(itertools.product([0,1],repeat=11)),dtype=np.uint8)
    truth=np.array([flow.source_outputs(src,x) for x in patterns]);pv=pm_values(pm,patterns);av=aig_values(aig,patterns)
    assert np.array_equal(pv[:,pm['outputs']],truth) and np.array_equal(av[:,aig['outputs']],truth)
    bad=copy.deepcopy(aig)
    for n in bad['nodes'][11:]:n['pins']=[(p+1)%11 if p<11 else p for p in n['pins']]
    bad['outputs']=[(p+1)%11 if p<11 else p for p in bad['outputs']]
    mismatch=int(np.any(aig_values(bad,patterns)[:,bad['outputs']]!=truth,axis=1).sum());assert mismatch>0
    eligible=[];obligations={}
    for t,node in enumerate(pm['nodes']):
        if not 2<=len(node['pins'])<=6:continue
        zero=pm_values(pm,patterns,t,0);one=pm_values(pm,patterns,t,1)
        can0=np.all(zero[:,pm['outputs']]==truth,axis=1);can1=np.all(one[:,pm['outputs']]==truth,axis=1)
        assert (can0|can1).all()
        if (~can0).any() and (~can1).any():eligible.append(t)
        obligations[t]=(zero,can0,can1)
    targets=[eligible[int(i*(len(eligible)-1)/7)] for i in range(8)];assert len(set(targets))==8
    selection=dict(targets=targets,eligible_count=len(eligible),used_cells=sorted(used),pm_nodes=len(pm['nodes']),aig_nodes=len(aig['nodes']),inputs=11,outputs=len(pm['outputs']),patterns=2048,pi_permutation_disagreement_patterns=mismatch,selected_before_model_scoring=True)
    (result/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    cases=[]
    for t in targets:
        cut=copy.deepcopy(pm);cut['nodes'][t]={'cell':'PI','name':pm['nodes'][t]['name'],'pins':[]}
        cases.append(dict(id=f'epfl_int2float_nangate45_site_{t}',target=t,cut=cut,aig=aig))
    records=[];negative_done=False
    def accept(c,ranking,mode,logits=None,extra=None):
        nonlocal negative_done
        t=c['target'];zero,can0,can1=obligations[t];needed=~(can0&can1);patch=None
        for k in range(1,4):
            ids=ranking[:k];table={};conflict=False
            for row,bit in zip(zero[needed],can1[needed].astype(int)):
                key=tuple(int(row[p]) for p in ids)
                if key in table and table[key]!=bit:conflict=True;break
                table[key]=int(bit)
            if not conflict:
                tt=[table.get(bits,0) for bits in itertools.product([0,1],repeat=len(ids))];patch=netlist_for_table(ids,tt);break
        row=dict(case=c['id'],target=t,mode=mode,ranking=ranking,logits=logits,success=patch is not None,**(extra or {}))
        if patch is not None:
            path=result/f'{mode}_{t}.blif';flow.export_patch(pm,t,patch,path,mp['inputs'],mp['outputs'])
            # Independent exported .names cover evaluation, not the vectorized solver.
            parsed=flow.read_blif(path)
            assert all(flow.source_outputs(parsed,x)==tuple(expected) for x,expected in zip(patterns,truth))
            assert 'Networks are equivalent' in abc(f'cec {original} {path}',f'cec_{mode}_{t}')
            row.update(support=k,patch=patch,patch_blif='results/'+path.name,exhaustive_passed=True,abc_cec='equivalent')
            if not negative_done:
                broken=copy.deepcopy(patch);broken['nodes'].append(dict(gate='NOT',pins=[broken['output']]));broken['output']=len(broken['nodes'])-1
                neg=result/'negative.blif';flow.export_patch(pm,t,broken,neg,mp['inputs'],mp['outputs'])
                out=abc(f'cec {original} {neg}','negative_cec');assert 'NOT EQUIVALENT' in out;negative_done=True
        records.append(row)
    for seed in [208,209]:
        for arm in ['paired_pretrained','pm_only']:
            meta=json.loads((ROOT.parent/f'closure/results/full_token/{arm}_{seed}.json').read_text());ckpt=ROOT.parent/'closure'/meta['checkpoint_path']
            assert hashlib.sha256(ckpt.read_bytes()).hexdigest()==meta['checkpoint_sha256']
            model=Pipeline(arm,seed);model.load_state_dict(torch.load(ckpt,weights_only=True,map_location='cpu')['state_dict'],strict=True);model.eval()
            for c in cases:
                with torch.inference_mode():
                    tokens=model.pm_encode(c,cut=True);ids=legal_candidates(c['cut'],c['target'])
                    conditions=['matched','permuted_pi'] if arm=='paired_pretrained' else ['pm_only']
                    base_context=None;base_logits=None
                    for cond in conditions:
                        np.random.seed(sid(c['id']));h,f=model.aig(SimpleNamespace(**graph_fields(bad if cond=='permuted_pi' else aig,'aig_')))
                        context=torch.cat([h,f],1);model.context[c['id']]=context
                        out=model.contextualize([tokens],[c],[[c['target']]])[0]
                        logits=model.rank(torch.cat([out[ids],out[c['target']].expand(len(ids),-1)],1)).reshape(-1)
                        ranking=[ids[i] for i in torch.argsort(logits,descending=True,stable=True).tolist()]
                        extra=dict(seed=seed,checkpoint_sha256=meta['checkpoint_sha256'])
                        if cond=='matched':
                            base_context=context;base_logits=logits
                            model.context[c['id']]=context.flip(0);rev=model.contextualize([tokens],[c],[[c['target']]])[0]
                            rev_logits=model.rank(torch.cat([rev[ids],rev[c['target']].expand(len(ids),-1)],1)).reshape(-1)
                            extra['token_reversal_max_abs_logit_difference']=float((rev_logits-logits).abs().max());assert extra['token_reversal_max_abs_logit_difference']<1e-5
                            model.context[c['id']]=base_context
                        if cond=='permuted_pi':extra['matched_max_abs_logit_difference']=float((base_logits-logits).abs().max())
                        accept(c,ranking,f'{cond}_{seed}',logits.tolist(),extra)
            del model
    for c in cases:
        ids=legal_candidates(c['cut'],c['target']);accept(c,sorted(ids,reverse=True),'reverse_topological')
        shuffled=ids.copy();np.random.default_rng(208+c['target']).shuffle(shuffled);accept(c,shuffled,'random')
        pins=pm['nodes'][c['target']]['pins'];accept(c,pins+sorted(set(ids)-set(pins)),'oracle_direct_fanin')
    assert len(records)==72 and negative_done
    summary={m:dict(successes=sum(r['success'] for r in records if r['mode']==m),trials=sum(r['mode']==m for r in records)) for m in sorted(set(r['mode'] for r in records))}
    abc_sha=subprocess.check_output(['git','-C',str(abc_bin.parent),'rev-parse','HEAD'],text=True).strip()
    report=dict(status='complete',selection=selection,summary=summary,records=records,commands=commands,negative_control_passed=negative_done,seconds=time.time()-start,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,torch=torch.__version__,numpy=np.__version__,abc_commit=abc_sha,abc_binary_sha256=hashlib.sha256(abc_bin.read_bytes()).hexdigest(),training_updates=0,paid_api_requests=0,cost_usd=0)
    (result/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['records','commands']},indent=2),flush=True)

if __name__=='__main__':main()
