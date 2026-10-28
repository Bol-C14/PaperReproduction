"""Focused read-only audit of archived final configurations plus FMA proof replay."""
import collections
import hashlib
import json
import math
import pathlib
import shutil
import sys
import time

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import z3
from circuits import emit,inputs,symbolic,workload
from run_loop import restore,run

OUT=pathlib.Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load_rows(stage):return [json.loads(x) for x in (ROOT/'runs'/stage/'RESULTS.jsonl').read_text().splitlines()]
def folder(row):return pathlib.Path(row['evaluation']['synthesis']['log']).parent


def audit_dag(row,stage):
    artifact=json.loads((ROOT/'runs'/stage/f'{row["name"]}_{row["width"]}_{row["mode"]}.egraph.json').read_text())
    data=artifact['egraph'];nodes=data['nodes'];classes=data['class_data']
    report=row['dag_reports'][row['weight']]
    selected=report['selected_node_ids'];byclass={nodes[k]['eclass']:k for k in selected}
    assert len(byclass)==len(selected)
    root=next(c for c,v in classes.items() if v.get('let')=='$root')
    class_width={}
    def width_node(n):
        if n['op'] in ('Ult','Sge0','Not'):return 1
        index=1 if n['op']=='V' else 0
        return int(nodes[n['children'][index]]['op'])
    for n in nodes.values():
        if classes[n['eclass']]['type']!='B':continue
        w=width_node(n)
        if n['eclass'] in class_width:assert class_width[n['eclass']]==w
        class_width[n['eclass']]=w
    visiting=set();seen=set();incoming=collections.Counter()
    def build(c):
        if classes[c]['type']!='B':return json.loads(nodes[next(k for k,n in nodes.items() if n['eclass']==c)]['op'])
        assert c not in visiting,'selected cycle'
        assert c in byclass,'missing selected child'
        visiting.add(c);seen.add(c);n=nodes[byclass[c]];args=[]
        for child in n['children']:
            child_class=nodes[child]['eclass']
            if classes[child_class]['type']=='B':incoming[child_class]+=1
            args.append(build(child_class))
        visiting.remove(c)
        return tuple([n['op']]+args)
    term=build(root)
    assert term==restore(row['selected']['term'])
    # Formula reimplementation from the frozen v4 manifest, not engine.cost.
    area=0;mul=[]
    for key in selected:
        n=nodes[key];w=width_node(n);op=n['op'];children=[nodes[c]['eclass'] for c in n['children'] if classes[nodes[c]['eclass']]['type']=='B']
        a=0
        if op in ('Add','Mux'):a=w
        elif op=='Mul':a=class_width[children[0]]*class_width[children[1]];mul.append({'id':key,'area_once':a,'root_unfolded_uses':incoming[n['eclass']]})
        elif op=='Shr':a=w*class_width[children[1]]
        elif op=='Abs':a=2*w
        elif op in ('Ult','Sge0'):a=class_width[children[0]]
        if a:assert n['eclass'] in seen,'positive-cost orphan'
        area+=a
    assert area==report['area']==row['selected']['proxy_area']
    assert report['lower']==report['upper']==str(area)
    text=(folder(row)/'design.v').read_text().split('module candidate',1)[1]
    return {'selected_nodes':len(selected),'root_reachable_classes':len(seen),'recomputed_area':area,
            'selected_multipliers':mul,'emitted_multiply_operators':text.count(' * ')}


def cone(module,roots,skip_select=False):
    drivers={b:(key,c) for key,c in module['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs}
    cells=set();leaves=set()
    def visit(bit):
        if bit not in drivers:leaves.add(bit);return
        key,c=drivers[bit]
        if key in cells:return
        cells.add(key)
        for p,bs in c['connections'].items():
            if c['port_directions'][p]=='input' and not(skip_select and c['type']=='$_MUX_' and p=='S'):
                for b in bs:visit(b)
    for bit in roots:visit(bit)
    return cells,leaves


def guard_info(row):
    m=json.loads((folder(row)/'mapped.json').read_text())['modules']['candidate']
    muxes={k for k,c in m['cells'].items() if c['type']=='$_MUX_'}
    selects={b for k in muxes for b in m['cells'][k]['connections']['S']}
    g,leaves=cone(m,selects);data,_=cone(m,m['ports']['out']['bits'],skip_select=True)
    return {'all_cells':len(m['cells']),'mux_cells':len(muxes),'control_cone_cells':len(g),
            'control_types':dict(collections.Counter(m['cells'][k]['type'] for k in g)),
            'control_leaf_bits':sorted(leaves),'a_high_bits':m['ports']['a']['bits'][3:],
            'control_data_overlap_cells':len(g&data),'control_cell_ids':sorted(g),'mux_cell_ids':sorted(muxes)}


def prove(label,formula,expected='unsat'):
    solver=z3.SolverFor('QF_BV');solver.set(timeout=10000,random_seed=0);solver.add(formula)
    start=time.perf_counter();status=solver.check()
    (OUT/(label+'.smt2')).write_text(solver.to_smt2())
    result={'status':str(status),'expected':expected,'wall_seconds':time.perf_counter()-start}
    if status==z3.sat:result['witness']={str(v):solver.model()[v].as_long() for v in solver.model().decls()}
    assert str(status)==expected,(label,result)
    return result


def main():
    start=time.perf_counter();base=load_rows('width_matrix1');aware=load_rows('integrated_matrix1');allrows=base+aware
    assert len(base)==72 and len(aware)==24
    expected_synth='read_verilog design.v\nhierarchy -top candidate\nsynth -top candidate -noabc\nopt_clean\nwrite_json mapped.json\nstat\n'
    expected_verify='read_verilog design.v miter.v\nprep -top miter -flatten\nsat -verify -prove mismatch 0 -show-inputs\n'
    creators=set();pairs=[];dagrows=[]
    for r in allrows:
        f=folder(r);assert (f/'synth.ys').read_text()==expected_synth
        assert (f/'verify.ys').read_text()==expected_verify
        original=emit(workload(r['name'],r['width']),'original')
        assert (f/'design.v').read_text().startswith(original)
        assert len(r['history'])==8 and all(h['nodes']<5000 for h in r['history'])
        assert r['optimizer_process']['wall_seconds']<60
        assert all(t['status']=='sat' and t['lower']==t['upper'] for t in r['dag_reports'])
        assert r['source_sha256']['engine.py']==digest(ROOT/'engine.py')
        assert r['source_sha256']['dag_extract.py']==digest(ROOT/'dag_extract.py')
        module=json.loads((f/'mapped.json').read_text());creators.add(module['creator'])
        assert len(module['modules']['candidate']['cells'])==r['evaluation']['mapped']['gates']
        assert r['evaluation']['z3']=='unsat' and r['evaluation']['rtl_check']['returncode']==0
        dagrows.append({'key':[r['name'],r['width'],r['mode'],r['weight']],**audit_dag(r,'integrated_matrix1' if r['mode']=='context_live' else 'width_matrix1')})
    assert len(creators)==1
    for r in aware:
        a=next(t for t in base if (t['name'],t['width'],t['mode'],t['weight'])==(r['name'],r['width'],'agnostic',r['weight']))
        assert r['selected']['delay_target']<=a['selected']['delay_target']
        pairs.append({'key':[r['name'],r['width'],r['weight']],'agnostic_delay_target':a['selected']['delay_target'],
                      'aware_delay_target':r['selected']['delay_target'],'same_common_rule_cost_source':True})
    fma=next(r for r in aware if (r['name'],r['width'],r['weight'])==('bounded_fma',16,1))
    fbase=next(r for r in base if (r['name'],r['width'],r['mode'],r['weight'])==('bounded_fma',16,'agnostic',1))
    a,b,c=z3.BitVecs('a b c',16);env={'a':a,'b':b,'c':c};guard=z3.ULT(a,8)
    original=symbolic(workload('bounded_fma',16),env);candidate=symbolic(restore(fma['selected']['term']),env)
    archived=z3.parse_smt2_file(str(folder(fma)/'equivalence.smt2'));assert len(archived)==1
    proof={}
    proof['archived_full_domain']=prove('archived_full_domain',archived[0])
    proof['care_partition']=prove('care_partition',z3.And(guard,original!=candidate))
    proof['outside_original']=prove('outside_original',z3.And(z3.Not(guard),original!=c))
    proof['outside_candidate']=prove('outside_candidate',z3.And(z3.Not(guard),candidate!=c))
    proof['narrow_operand_obligation']=prove('narrow_operand_obligation',z3.And(guard,a!=z3.ZeroExt(13,z3.Extract(2,0,a))))
    proof['guard_unsigned_obligation']=prove('guard_unsigned_obligation',z3.And(guard,z3.Extract(15,15,a)==1))
    full32=z3.ZeroExt(16,a)*z3.ZeroExt(16,b)+z3.ZeroExt(16,c)
    reference=z3.If(guard,z3.Extract(15,0,full32),c)
    proof['full32_reference']=prove('full32_reference',original!=reference)
    proof['outside_internal_can_differ']=prove('outside_internal_can_differ',z3.And(z3.Not(guard),a*b+c!=z3.ZeroExt(13,z3.Extract(2,0,a))*b+c),'sat')
    vectors=[]
    for av,bv,cv in [(7,65535,65535),(8,3,5),(65535,65535,65535),(0,65535,65535)]:
        subst=[(a,z3.BitVecVal(av,16)),(b,z3.BitVecVal(bv,16)),(c,z3.BitVecVal(cv,16))]
        oval=z3.simplify(z3.substitute(original,*subst)).as_long();nval=z3.simplify(z3.substitute(candidate,*subst)).as_long()
        assert oval==nval
        vectors.append({'a':av,'b':bv,'c':cv,'guard':av<8,'original_out':oval,'candidate_out':nval,
                        'original_inner_mod16':(av*bv+cv)%65536,'candidate_inner_mod16':((av&7)*bv+cv)%65536})
    target=OUT/'fma16_rtl';target.mkdir(exist_ok=False)
    for name in ['design.v','miter.v','verify.ys']:shutil.copyfile(folder(fma)/name,target/name)
    rtl=run([str(ROOT/'.venv/bin/yowasp-yosys'),'-s','verify.ys'],target,target/'verify.log',120)
    assert rtl.get('returncode')==0
    old_manifest=(ROOT/'ARTIFACT_MANIFEST.sha256').read_text().splitlines()
    for line in old_manifest:
        h,path=line.split('  ',1);assert digest(ROOT/path)==h,path
    result={'pairs_checked':len(pairs),'configuration_rows_checked':len(allrows),'synthesis_script_sha256':hashlib.sha256(expected_synth.encode()).hexdigest(),
            'yosys_creators':sorted(creators),'pairs':pairs,'dag':dagrows,'fma_proofs':proof,'fma_vectors':vectors,
            'fma_guard_cost':guard_info(fma),'fma_baseline_guard_cost':guard_info(fbase),'fma_rtl_replay':rtl,
            'old_artifact_hashes_verified':len(old_manifest),'wall_seconds':time.perf_counter()-start}
    (OUT/'AUDIT_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('dag','pairs','fma_guard_cost','fma_baseline_guard_cost')},indent=2))


if __name__=='__main__':main()
