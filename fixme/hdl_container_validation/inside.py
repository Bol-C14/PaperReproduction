"""Reviewed compiler/simulator supervisor; records actual process boundaries."""
import json,os,pathlib,subprocess,time,socket,threading
P=pathlib.Path('/work')
def snapshot(pid):
 p=pathlib.Path('/proc')/str(pid)
 try:
  status=(p/'status').read_text();fields={x.split(':',1)[0]:x.split(':',1)[1].strip() for x in status.splitlines() if ':' in x}
  exe=os.readlink(p/'exe')
  return {'exe':exe,'Uid':fields['Uid'],'CapEff':fields['CapEff'],'NoNewPrivs':fields['NoNewPrivs'],'mount_namespace':os.readlink(p/'ns/mnt'),'network_namespace':os.readlink(p/'ns/net'),'mountinfo':(p/'mountinfo').read_text()}
 except (FileNotFoundError,ProcessLookupError):return None
boundary={'host_canary_absent':not pathlib.Path('/workspace/fixme-owned-isolation-canary.txt').exists(),'docker_socket_absent':not pathlib.Path('/var/run/docker.sock').exists(),'repository_absent':not pathlib.Path('/workspace/PaperReproduction/.git').exists(),'credential_names_absent':not any(x in os.environ for x in ['NR_KEY','OPENAI_API_KEY'])}
try:pathlib.Path('/root-write-probe').write_text('probe');boundary['root_readonly']=False
except OSError:boundary['root_readonly']=True
try:
 s=socket.socket();s.settimeout(.2);s.connect(('192.0.2.1',80));boundary['network_denied']=False
except OSError:boundary['network_denied']=True
finally:s.close()
(P/'scratch-probe').write_text('ok');boundary['scratch_writable']=(P/'scratch-probe').read_text()=='ok'
assert all(boundary.values()),boundary
self_info=snapshot(os.getpid());assert self_info['Uid'].split()==['65534']*4 and int(self_info['CapEff'],16)==0 and self_info['NoNewPrivs']=='1'
rows=[]
def command(argv,timeout):
 t=time.monotonic();p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);observed=[];seen=set()
 # Capture real executable identities rather than just the command wrapper.
 while p.poll() is None and time.monotonic()-t<min(.1,timeout):
  a=snapshot(p.pid)
  if a and a['exe'] not in seen:
   observed.append(a);seen.add(a['exe'])
  time.sleep(.0002)
 try:o,e=p.communicate(timeout=max(.001,timeout-(time.monotonic()-t)));state='completed'
 except subprocess.TimeoutExpired:p.kill();o,e=p.communicate();state='timeout'
 for a in observed:
  assert a['Uid'].split()==['65534']*4 and int(a['CapEff'],16)==0 and a['NoNewPrivs']=='1'
  assert a['mount_namespace']==self_info['mount_namespace'] and a['network_namespace']==self_info['network_namespace']
 return {'argv':argv,'state':state,'returncode':p.returncode,'stdout':o.decode(),'stderr':e.decode(),'seconds':round(time.monotonic()-t,6),'actual_process_snapshots':observed}
# A FIFO hold makes the short-lived real compiler inspectable without changing source.
os.mkfifo('/work/dut-gated.sv')
def feed_source():
 time.sleep(.2)
 with open('/work/dut-gated.sv','w') as f:f.write((P/'dut.sv').read_text())
threading.Thread(target=feed_source,daemon=True).start()
compile_result=command(['iverilog','-g2012','-s','calibration_tb','-o','/work/sim.vvp','/work/dut-gated.sv','/work/tb.sv'],2)
if compile_result['returncode']!=0:decision='task_syntax_failure';sim=None
else:
 sim=command(['vvp','/work/sim.vvp'],.5)
 if sim['state']=='timeout':decision='timeout_unknown'
 elif sim['returncode']!=0:decision='error'
 elif 'CHECK_FAIL' in sim['stdout']:decision='fail'
 elif 'CHECK_PASS checks=4' in sim['stdout']:decision='pass'
 else:decision='unknown'
print(json.dumps({'boundary':boundary,'supervisor':self_info,'compile':compile_result,'simulate':sim,'decision':decision,'versions':subprocess.run(['iverilog','-V'],capture_output=True,text=True).stdout,'package_versions':pathlib.Path('/package-versions.txt').read_text()}))
