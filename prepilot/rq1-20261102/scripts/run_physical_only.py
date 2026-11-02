"""One paired physical-action pilot, with conditional bounded confirmations."""
import hashlib,json,os,pathlib,re,subprocess,time
ROOT=pathlib.Path('/workspace/work/rq1-prepilot-20261102/physical-only-round3')
SRC=pathlib.Path('/workspace/work/fpl26_optimization_contest_ablation_shu/fpl26_contest_benchmarks/vexriscv_re-place_2025.1.dcp')
HASH='8baf6451f9b20b8a82f035d14187c7350529a6ea0330e02d93c7100b19753149'
expected_hash=hashlib.sha256(SRC.read_bytes()).hexdigest();assert expected_hash==HASH
started=time.monotonic();deadline=started+1180;rows=[]
def canonical(p):
 return '\n'.join(x for x in p.read_text().splitlines() if not x.startswith(('// Date        :','// Command     :','# Command Used:')))
def clock(p):return {k:float(v) for k,v in (line.split('\t') for line in p.read_text().splitlines())}
def run(name,action):
 # Same hash read warms input file under the same policy before each process.
 assert hashlib.sha256(SRC.read_bytes()).hexdigest()==HASH
 remaining=deadline-time.monotonic()
 if remaining<35:raise RuntimeError('Global budget exhausted before next arm')
 cap=min(290,int(remaining-15))
 out=ROOT/name;out.mkdir()
 cmd=['timeout','--signal=TERM','--kill-after=10s',str(cap)+'s',os.environ['VIVADO_EXEC'],'-mode','batch','-notrace','-source',str(ROOT/'physical_only_arm.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(SRC),str(out),action]
 (out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
 t=time.monotonic()
 with (out/'stdout.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=out)
 row={'arm':name,'action':action,'exit_code':r.returncode,'wall_seconds':time.monotonic()-t,'nominal_timeout_seconds':cap,'threads':2,'tool_seed':'not_set_not_claimed_controlled','input_sha256':HASH,'status':'complete' if r.returncode==0 else ('censored_timeout' if r.returncode in (124,137) else 'tool_failed')}
 if r.returncode==0:
  before=clock(out/'before_contest.tsv');after=clock(out/'after_contest.tsv')
  s=(out/'after_timing.rpt').read_text();m=re.search(r'WNS\(ns\).*?\n.*?\n(.*?)\n',s,re.S);assert m
  v=m[1].split();route=(out/'route.rpt').read_text();errs=re.search(r'# of nets with routing errors\.+\s*:\s*(\d+)',route);fully=re.search(r'# of fully routed nets\.+\s*:\s*(\d+)',route);total=re.search(r'# of routable nets\.+\s*:\s*(\d+)',route);assert errs and fully and total
  drc=(out/'drc.rpt').read_text();assert 'REPORT SUMMARY' in drc
  bad_drc=re.findall(r'^\|[^|]+\|\s*(?:Error|Critical Warning)\s*\|',drc,re.M)
  log=(out/'stdout.log').read_text()
  row.update({'before_clock':before,'after_clock':after,'tns_ns':float(v[1]),'setup_failing_endpoints':int(v[2]),'whs_ns':float(v[4]),'ths_ns':float(v[5]),'wpws_ns':float(v[8]),'tpws_ns':float(v[9]),'route_error_nets':int(errs[1]),'fully_routed_nets':int(fully[1]),'routable_nets':int(total[1]),'bad_drc_rows':len(bad_drc),'funcsim_identical':canonical(out/'before_funcsim.v')==canonical(out/'after_funcsim.v'),'constraints_identical':canonical(out/'before_constraints.xdc')==canonical(out/'after_constraints.xdc'),'physopt_ms':int(re.search(r'RQ1_PHYSOPT_MS=(\d+)',log)[1]),'route_ms':int(re.search(r'RQ1_ROUTE_MS=(\d+)',log)[1]),'psir_phase_executed':bool(re.search(r'^Phase \d+ Physical Synthesis in Router',log,re.M))})
  row['contract_pass']=all([row['funcsim_identical'],row['constraints_identical'],before['period_ns']==after['period_ns']==1.570,before['wns_ns']==-1.654,row['route_error_nets']==0,row['fully_routed_nets']==row['routable_nets'],row['ths_ns']==0,row['tpws_ns']==0,row['whs_ns']>=0,row['wpws_ns']>=0,not bad_drc,not row['psir_phase_executed']])
 else:row['contract_pass']=False
 rows.append(row);(ROOT/'ledger.json').write_text(json.dumps(rows,indent=2)+'\n')
 if not row['contract_pass']:raise RuntimeError('Stop: incomplete or unconfirmed contract for '+name)
 return row
try:
 a=run('A1_noop','noop');b=run('B1_routing_opt','routing_opt')
 assert a['before_clock']==b['before_clock']
 # Same original HDL/XDC across arms, not merely self-comparison.
 for suffix in ['funcsim.v','constraints.xdc']:
  assert canonical(ROOT/'A1_noop'/('before_'+suffix))==canonical(ROOT/'B1_routing_opt'/('before_'+suffix))
 delta=b['after_clock']['wns_ns']-a['after_clock']['wns_ns']
 result={'initial_pair_delta_ns':delta,'initial_pair_contracts_pass':True,'initial_cost_ratio_B_over_A':b['wall_seconds']/a['wall_seconds'],'expanded':False,'engineering_screen_ns':0.050,'screen_is_statistical_significance':False}
 if delta>=0.050 and b['wall_seconds']<=2*a['wall_seconds']:
  result['expanded']=True
  for name,action in [('B2_routing_opt','routing_opt'),('A2_noop','noop'),('A3_noop','noop'),('B3_routing_opt','routing_opt')]:run(name,action)
  result['reason']='technical_confirmations_completed; require final paired/range summary'
 else:result['reason']='initial_pair_not_worth_expansion_under_frozen_engineering_screen'
 result['tool_wall_seconds']=sum(r['wall_seconds'] for r in rows)
 result['controller_wall_seconds']=time.monotonic()-started
 (ROOT/'decision.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
except Exception as e:
 (ROOT/'STOP_REASON.txt').write_text(type(e).__name__+': '+str(e)+'\n')
 print(type(e).__name__+': '+str(e));raise
