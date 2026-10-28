import copy, hashlib, json, pathlib, sys
from scorer import score,gates,evidence_gate

root=pathlib.Path(__file__).resolve().parents[1]
source=pathlib.Path(sys.argv[1])
raw=source.read_text()
data=json.loads(raw) if raw.lstrip().startswith('{') else json.loads(raw.split('=',1)[1].rstrip(';\n'))
rows=[]
for e in data['entries']:
    s=score(e['stageScore'],e['metrics'],e['frequency'])
    rows.append(dict(id=e['id'],published=e['score'],recomputed=s['score'],delta=s['score']-e['score'],
                     stage=e['stageScore'],result=s['result'],paper_legacy=e['id'].startswith('legacy-0721-'),
                     roi_status='not_recomputed_missing_normalization'))
ideal=dict(area=23746.27,power=2.49435,setupWns=0,setupTns=0,holdWns=0,holdTns=0)
controls=[]
for name,l,p,e,expected in [
 ('complete',[True]*2,[True]*4,True,100),
 ('missing_eco',[True]*2,[True]*4,False,40/3),
 ('missing_io',[True]*2,[False,True,True,True],True,35/3),
 ('missing_synthesis',[False,False],[True]*4,True,0),
 ('partial_synthesis',[True,False],[True]*4,True,10/3)]:
    actual=score(gates(l,p,e),ideal,350)['score']
    assert abs(actual-expected)<1e-9
    controls.append(dict(id=name,expected=expected,actual=actual,passed=True))
for metric,value in [('area',0),('power',-1),('setupWns',float('nan')),('holdWns',None)]:
    m={**ideal,metric:value}; s=score(100,m,350)
    assert s['components'][metric]==0
    controls.append(dict(id='invalid_'+metric,actual=s['score'],passed=True))
for f in [0,100,351]:
    try: score(100,ideal,f)
    except ValueError: controls.append(dict(id='unknown_frequency_'+str(f),passed=True))
    else: raise AssertionError(f)
artifact=dict(design_sha256='design',constraints_sha256='constraint',validator='independent-parser',valid=True)
valid={'artifacts':{k:dict(artifact) for k in ['netlist','layout','gds','timing','qor']}}
for name,b,expect in [('consistent_evidence',valid,True),('pass_string',{'stdout':'PASS','exit_code':0},False)]:
    assert evidence_gate(b,'design','constraint') is expect
    controls.append(dict(id=name,accepted=expect,passed=True))
for name,key,value in [('stale_design','design_sha256','old'),('stale_constraint','constraints_sha256','old'),('invalid_gds','valid',False)]:
    b=copy.deepcopy(valid); b['artifacts']['gds'][key]=value
    assert not evidence_gate(b,'design','constraint')
    controls.append(dict(id=name,accepted=False,passed=True))
out=dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_generated_at=data['generatedAt'],
         status='offline_replay',record_count=len(rows),rows=rows,synthetic_controls=controls,
         max_absolute_score_delta=max(abs(r['delta']) for r in rows),
         matching_at_1e_3=sum(abs(r['delta'])<1e-3 for r in rows))
(root/'results'/'score_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['rows','synthetic_controls']},indent=2))
print('synthetic_controls',len(controls))
