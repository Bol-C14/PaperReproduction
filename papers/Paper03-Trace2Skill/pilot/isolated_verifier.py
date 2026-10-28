"""Real restricted Icarus verifier for the public adder infrastructure fixture.
Never used as CVDP. Only fixed approved compiler commands; candidate is data.
"""
import hashlib,json,re,subprocess,tempfile,time
from pathlib import Path
from verifier_fixture.docker_smoke import IMAGE,ENV

def candidate_source(text):
    if not isinstance(text,str):raise ValueError('text RTL required')
    s=text.strip()
    if s.startswith('```'):
        lines=s.splitlines()
        if lines[-1].strip()!='```':raise ValueError('unterminated fence')
        s='\n'.join(lines[1:-1])
    if len(s.encode())>16384 or s.count('endmodule')!=1 or not re.search(r'\bmodule\s+adder\b',s):raise ValueError('single small adder module required')
    # Fixture is combinational: prohibit simulation control, includes and plugins.
    if '$' in s or '`' in s or re.search(r'\b(initial|final|bind|import|export|program|specify)\b',s):raise ValueError('unavailable simulation control/directives')
    if re.search(r'Authorization|Bearer\s|NR_KEY|sk-[A-Za-z0-9_-]{20,}',s,re.I):raise ValueError('sensitive output rejected')
    return s+'\n'

class RealAdderVerifier:
    mode='real_isolated_iverilog_public_fixture'
    def __init__(self,image=IMAGE):
        if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):raise ValueError('immutable image ID required')
        self.image=image;self.rows=[]
    def __call__(self,text,*,rollout):
        source=candidate_source(text);begin=time.monotonic()
        with tempfile.TemporaryDirectory(prefix='t2s-agent-rtl-') as tmp:
            d=Path(tmp);d.chmod(0o755);(d/'candidate.sv').write_text(source);(d/'tb.sv').write_bytes((Path(__file__).parent/'verifier_fixture/tb.sv').read_bytes())
            for f in d.iterdir():f.chmod(0o644)
            command='iverilog -g2012 -s tb -o /tmp/sim.vvp /work/candidate.sv /work/tb.sv; rc=$?; if [ "$rc" -ne 0 ]; then exit 20; fi; cd /tmp; vvp /tmp/sim.vvp'
            args=['docker','create','--network=none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges:true','--pids-limit=64','--memory=256m','--cpus=1','--user=65534:65534','--tmpfs','/tmp:rw,noexec,nosuid,size=64m','--mount',f'type=bind,src={d},dst=/work,readonly',self.image,'-c',command]
            cid=subprocess.check_output(args,env=ENV,text=True,stderr=subprocess.DEVNULL).strip()
            try:
                info=json.loads(subprocess.check_output(['docker','inspect',cid],env=ENV,text=True))[0];host=info['HostConfig']
                assert host['NetworkMode']=='none' and host['ReadonlyRootfs'] and not host['Privileged'] and info['Config']['User']=='65534:65534'
                assert len(info['Mounts'])==1 and info['Mounts'][0]['RW'] is False
                assert 'NR_KEY' not in [x.split('=',1)[0] for x in info['Config']['Env']]
                try:
                    r=subprocess.run(['docker','start','-a',cid],env=ENV,capture_output=True,timeout=30)
                    state=json.loads(subprocess.check_output(['docker','inspect',cid],env=ENV,text=True))[0]['State'];code=state['ExitCode'];raw=r.stdout+r.stderr
                    status='pass' if code==0 and b'PASS: 256 exhaustive input pairs' in raw else ('compile_fail' if code==20 else 'functional_fail')
                except subprocess.TimeoutExpired:code=None;raw=b'';status='timeout'
                row={'rollout':rollout,'mode':self.mode,'status':status,'pass':status=='pass','exit_code':code,'elapsed_seconds':round(time.monotonic()-begin,6),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'output_sha256':hashlib.sha256(raw).hexdigest(),'image_id':self.image,'network':'none','read_only_root':True,'NR_KEY_in_worker':False}
                self.rows.append(row);return row
            finally:subprocess.run(['docker','rm','-f',cid],env=ENV,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
