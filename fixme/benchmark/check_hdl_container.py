raise SystemExit("Historical entry point preserved in git history; use check_harness_hardening.py in a fresh result layout. Legacy reports describe historical executions, not a new rerun.")
"""Execute exactly the seven fixed, predeclared HDL cases inside pinned Docker."""
import json,pathlib,hashlib
import container_isolation as ci
root=pathlib.Path(__file__).resolve().parents[1]/'hdl_container_validation'
image=json.loads((root/'image.json').read_text())['image_id'];assert image.startswith('sha256:')
# Locally built immutable image only; preserve the v7 default and restrictions.
ci.IMAGE=image
plan=json.loads((root/'PLAN.json').read_text());inside=(root/'inside.py').read_bytes()
correct='module mux(input a,b,s,output y);assign y=s?b:a;endmodule\n'
tb='''module calibration_tb;reg a,b,s;wire y;mux d(a,b,s,y);integer i;integer fails=0;initial begin for(i=0;i<4;i=i+1)begin a=i[0];b=~i[0];s=i[1];#1;if(y!==(s?b:a))fails=fails+1;end if(fails)$display("CHECK_FAIL failures=%0d",fails);else $display("CHECK_PASS checks=4");$finish;end endmodule\n'''
cases=[(correct,tb),(correct.replace('s?b:a','s?a:b'),tb),(correct,tb.replace('s?b:a','s?a:b')),(correct,'module calibration_tb;initial $finish;endmodule\n'),(correct.replace('assign y=','assign y=INVALID SYNTAX '),tb),(correct,tb.replace('initial begin','initial INVALID SYNTAX begin')),(correct,'module calibration_tb;initial forever #1;endmodule\n')]
rows=[]
for (name,expected),(dut,bench) in zip(zip(plan['cases'],plan['expected']),cases):
 d=root/name;d.mkdir();files={'inside.py':inside,'dut.sv':dut.encode(),'tb.sv':bench.encode()}
 for n,b in files.items():(d/n).write_bytes(b)
 r=ci.run_reviewed(files,['python3','/work/inside.py'],timeout=5)
 (d/'container.json').write_text(json.dumps(r,indent=2)+'\n')
 assert r['status']=='completed' and r['returncode']==0 and r['container_removed'],r
 result=json.loads(r['stdout']);(d/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['decision']==expected,(name,result)
 assert all(result['boundary'].values())
 rows.append({'case':name,'expected':expected,'actual':result['decision'],'seconds':r['seconds'],'snapshots':len(result['compile']['actual_process_snapshots'])+(len(result['simulate']['actual_process_snapshots']) if result['simulate'] else 0),'input_sha256':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}})
# Require actual compiler and actual simulator snapshots in baseline.
a=json.loads((root/'correct_mux/result.json').read_text());assert any(x['exe'].endswith('/iverilog') for x in a['compile']['actual_process_snapshots']);assert any(x['exe'].endswith('/vvp') for x in json.loads((root/'simulation_timeout/result.json').read_text())['simulate']['actual_process_snapshots'])
summary={'trials':rows,'all_expected_outcomes':True,'model_calls':0,'paid_resources':0,'host_configuration_changes':False,'image':image,'actual_compiler_and_simulator_snapshots_verified':True,'seconds_sum':round(sum(x['seconds'] for x in rows),4)}
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
