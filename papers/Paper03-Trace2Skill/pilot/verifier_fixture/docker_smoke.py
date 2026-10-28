"""Actual isolated Icarus positive/negative fixture controls. No model/network API."""
import argparse,hashlib,json,re,subprocess,tempfile,time
from pathlib import Path
P=Path(__file__).resolve().parent
IMAGE='sha256:5ca5a8b42e0bd12da72852a33d5d50ef45de6e0e8949edcae6cd288d7608b509'
ENV={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/tmp','LANG':'C.UTF-8'}
COMMAND='test -z "${NR_KEY+x}" || exit 80; test ! -e /var/run/docker.sock || exit 81; if (echo no >/root-proof) 2>/dev/null; then exit 82; fi; if (echo no >>/work/adder.sv) 2>/dev/null; then exit 83; fi; iverilog -g2012 -s tb -o /tmp/sim.vvp /work/adder.sv /work/tb.sv && cd /tmp && vvp /tmp/sim.vvp'

def main(image=IMAGE):
 assert re.fullmatch(r"sha256:[a-f0-9]{64}",image),"an inspected immutable image ID is required"
 outcomes=[]
 for control in ['positive','negative']:
  with tempfile.TemporaryDirectory(prefix='t2s-isolated-') as tmp:
   d=Path(tmp);d.chmod(0o755);source=(P/'upstream/adder.sv').read_text()
   if control=='negative':source=source.replace('assign X = A + B;','assign X = A | B;')
   (d/'adder.sv').write_text(source);(d/'tb.sv').write_bytes((P/'tb.sv').read_bytes())
   for f in d.iterdir():f.chmod(0o644)
   args=['docker','create','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges:true','--pids-limit=64','--memory=256m','--cpus=1','--user=65534:65534','--tmpfs','/tmp:rw,noexec,nosuid,size=64m','--mount',f'type=bind,src={d},dst=/work,readonly',image,'-c',COMMAND]
   cid=subprocess.check_output(args,env=ENV,text=True).strip()
   try:
    info=json.loads(subprocess.check_output(['docker','inspect',cid],env=ENV,text=True))[0];host=info['HostConfig'];cfg=info['Config'];keys=[x.split('=',1)[0] for x in cfg['Env']]
    assert host['NetworkMode']=='none' and host['ReadonlyRootfs'] and not host['Privileged'] and cfg['User']=='65534:65534' and 'NR_KEY' not in keys
    start=time.monotonic();run=subprocess.run(['docker','start','-a',cid],env=ENV,capture_output=True,text=True,timeout=30);elapsed=time.monotonic()-start
    code=json.loads(subprocess.check_output(['docker','inspect',cid],env=ENV,text=True))[0]['State']['ExitCode'];output=run.stdout+run.stderr
    assert code==(0 if control=='positive' else 1),(code,output)
    assert ('PASS: 256 exhaustive input pairs' in output) if control=='positive' else ('adder mismatch' in output)
    outcomes.append({'control':control,'exit_code':code,'elapsed_seconds':elapsed,'output':output.strip(),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'isolation':{'network_mode':host['NetworkMode'],'read_only_root':host['ReadonlyRootfs'],'privileged':host['Privileged'],'cap_drop':host['CapDrop'],'security_opt':host['SecurityOpt'],'user':cfg['User'],'memory_bytes':host['Memory'],'pids_limit':host['PidsLimit'],'nano_cpus':host['NanoCpus'],'NR_KEY_in_container_env':False,'docker_socket_absent_checked':True,'root_write_rejected_checked':True,'source_write_rejected_checked':True}})
   finally:subprocess.run(['docker','rm','-f',cid],env=ENV,capture_output=True)
 return {'status':'REAL_DOCKER_RTL_SMOKE_PASSED','image_id':image,'real_verifier_executions':2,'new_model_requests':0,'controls':outcomes}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--image-id',default=IMAGE);args=parser.parse_args();print(json.dumps(main(args.image_id),indent=2))
