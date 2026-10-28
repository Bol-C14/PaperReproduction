"""Pinned per-run Docker restrictions; no host mounts, inherited secrets or daemon changes.
Only reviewed recipes are enabled. This BusyBox backend validates the boundary,
not HDL execution; an HDL toolchain image needs separate review and calibration.
"""
import io,json,os,pathlib,subprocess,tarfile,tempfile,time,uuid,hashlib,resource,signal
IMAGE='busybox@sha256:bdf57e528e45e4433820e045b29b4597825a1c9e38353532d90a01445013f82e'
ENV={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/nonexistent'}
def payload_provenance(origin,contains_credentials=False,disclosure_approved=False):
    allowed={'reviewed_local_fixture','official_pinned_source','model_generated','user_provided','unknown'}
    if origin not in allowed:raise ValueError('unknown provenance label')
    return {'origin':origin,'contains_credentials':bool(contains_credentials),'disclosure_approved':bool(disclosure_approved),'external_transmission_permitted':False,'execution_requires_review':origin not in {'reviewed_local_fixture','official_pinned_source'},'classification':'blocked_sensitive' if contains_credentials else 'local_only_pending_review' if origin in {'model_generated','user_provided','unknown'} else 'reviewed_local'}
MANIFEST=pathlib.Path(__file__).resolve().parents[1]/'harness_hardening/reviewed_manifest.json'
MANIFEST_SHA256='87e1d398542af07ae50dbf2959d3df942254c290f485f038461af47bd0c1d0b0'
def authorize_fixture(files,argv,timeout,origin,fixture_id):
    if origin is None or fixture_id is None:raise ValueError('explicit origin and reviewed fixture_id required')
    policy=payload_provenance(origin)
    if origin!='reviewed_local_fixture' or policy['execution_requires_review']:raise ValueError('origin not authorized for fixed calibration')
    raw=MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:raise ValueError('reviewed manifest integrity mismatch')
    entry=json.loads(raw)['fixtures'].get(fixture_id)
    if entry is None:raise ValueError('fixture_id not allowlisted')
    actual={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
    if actual!=entry['files'] or list(argv)!=entry['argv'] or timeout!=entry['timeout']:raise ValueError('payload/command/budget differs from reviewed manifest')
    return policy,entry

def _client_output_limits():
    # Applies only to the short-lived Docker CLI child, never the host controller.
    resource.setrlimit(resource.RLIMIT_FSIZE,(131072,131072))

def run_reviewed(files,argv,timeout=3,origin=None,fixture_id=None):
    policy,entry=authorize_fixture(files,argv,timeout,origin,fixture_id)
    image=entry['image']
    if not 0<timeout<=10:raise ValueError('bounded timeout required')
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w') as t:
        for name,data in files.items():
            p=pathlib.PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or not p.parts:raise ValueError('unsafe payload path')
            if not isinstance(data,bytes):raise TypeError('bytes required')
            if len(data)>65536:raise ValueError('fixture too large')
            info=tarfile.TarInfo(str(p));info.size=len(data);info.mode=0o444;t.addfile(info,io.BytesIO(data))
    if len(buf.getvalue())>1048576:raise ValueError('payload budget')
    name='fixme-isolation-'+uuid.uuid4().hex
    cmd=['docker','run','--name',name,'--rm','--pull=never','--network=none','--read-only','--user=65534:65534','--cap-drop=ALL','--security-opt=no-new-privileges=true','--pids-limit=32','--memory=128m','--memory-swap=128m','--cpus=0.5','--ulimit=nofile=64:64','--ulimit=fsize=1048576:1048576','--ulimit=core=0:0','--log-driver=none','--tmpfs=/work:rw,noexec,nosuid,nodev,size=8m,mode=1777','--workdir=/work','-i',image,'sh','-c','tar -xf - -C /work && exec "$@"','reviewed-recipe',*argv]
    start=time.monotonic();status='completed'
    # Bound retained host feedback without inheriting application credentials.
    with tempfile.TemporaryFile() as stdout,tempfile.TemporaryFile() as stderr:
        p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,env=ENV,close_fds=True,preexec_fn=_client_output_limits)
        try:p.communicate(buf.getvalue(),timeout=timeout)
        except subprocess.TimeoutExpired:
            status='timeout';subprocess.run(['docker','rm','-f',name],env=ENV,capture_output=True,timeout=5);p.kill();p.communicate()
        finally:
            cleanup=subprocess.run(['docker','rm','-f',name],env=ENV,capture_output=True,timeout=5)
        stdout.seek(0);stderr.seek(0);out=stdout.read(65537);err=stderr.read(65537)
    if len(out)>65536 or len(err)>65536 or p.returncode==-signal.SIGXFSZ:status='output_limit'
    remaining=subprocess.run(['docker','ps','-aq','--filter','name=^/'+name+'$'],env=ENV,capture_output=True,text=True,timeout=5)
    return {'status':status,'returncode':p.returncode,'seconds':round(time.monotonic()-start,4),'stdout':out[:65536].decode(errors='replace'),'stderr':err[:65536].decode(errors='replace'),'container_removed':remaining.returncode==0 and not remaining.stdout.strip(),'image':image,'argv':cmd,'provenance':policy,'fixture_id':fixture_id,'oracle_policy':entry['oracle_policy'],'manifest_sha256':MANIFEST_SHA256,'input_sha256':entry['files'],'executed_recipe_argv':entry['argv']}
