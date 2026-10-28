"""Oracle authority comes from the reviewed full-payload manifest, never stdout.
Protocol checks alone do not authenticate arbitrary RTL/TB output.
"""
import re,signal

def evaluate_fixed(result):
    # The host controller and immutable allowlist are trusted. This is binding
    # validation, not cryptographic attestation of an untrusted host caller.
    import json,hashlib
    from container_isolation import MANIFEST,MANIFEST_SHA256
    raw=MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:return {'status':'unknown','reason':'manifest integrity failure'}
    entry=json.loads(raw)['fixtures'].get(result.get('fixture_id'))
    if entry is None or result.get('manifest_sha256')!=MANIFEST_SHA256:return {'status':'unknown','reason':'missing reviewed execution binding'}
    cmd=result.get('argv',[])
    if result.get('image')!=entry['image'] or 'reviewed-recipe' not in cmd or cmd[cmd.index('reviewed-recipe')+1:]!=entry['argv']:return {'status':'unknown','reason':'execution recipe mismatch'}
    if result.get('oracle_policy')!=entry['oracle_policy']:return {'status':'unknown','reason':'oracle policy mismatch'}
    return _evaluate_bound_result(result)

def _evaluate_bound_result(result):
    if result.get('status')!='completed' or result.get('returncode')!=0:return {'status':'unknown','reason':'infrastructure/timeout, no correctness inference'}
    if result.get('oracle_policy')!='trusted_fixed_mux_trace':return {'status':'unknown','reason':'diagnostic fixture has no correctness authority'}
    # Caller must first obtain result through manifest-authorized run_reviewed.
    import json
    try:inner=json.loads(result['stdout'])
    except (ValueError,KeyError):return {'status':'unknown','reason':'malformed supervisor envelope'}
    c=inner.get('compile',{})
    if c.get('state')!='completed':return {'status':'unknown','reason':'compile '+str(c.get('state'))}
    if c.get('returncode')!=0:
        if c.get('returncode',0)<0:return {'status':'unknown','reason':'compiler resource/signal termination'}
        if re.search(r'syntax error|invalid module item',c.get('stderr',''),re.I):return {'status':'task_syntax_failure','reason':'explicit compiler syntax diagnostic'}
        return {'status':'unknown','reason':'compiler nonzero without confirmed syntax diagnostic'}
    sim=inner.get('simulate') or {}
    if sim.get('state')!='completed':return {'status':'unknown','reason':'simulation '+str(sim.get('state'))}
    if sim.get('returncode')!=0:return {'status':'unknown','reason':'simulator nonzero'}
    lines=sim.get('stdout','').splitlines();observations=[];terminals=[]
    for line in lines:
        if line.startswith('FIXME_OBSERVATION '):
            m=re.fullmatch(r'FIXME_OBSERVATION ([0-3]) ([01]) ([01]) ([01]) ([01xz]) ([01])',line)
            if not m:return {'status':'unknown','reason':'malformed observation'}
            observations.append(m.groups())
        elif line.startswith('FIXME_RESULT '):
            m=re.fullmatch(r'FIXME_RESULT checks=4 failures=([0-4])',line)
            if not m:return {'status':'unknown','reason':'malformed terminal'}
            terminals.append(int(m[1]))
        elif line.startswith('CHECK_PASS') or line.startswith('CHECK_FAIL'):
            return {'status':'unknown','reason':'legacy marker is not oracle evidence'}
    if len(terminals)!=1 or len(observations)!=4:return {'status':'unknown','reason':'missing/duplicate records'}
    failures=0
    for i,row in enumerate(observations):
        index,a,b,s,y,claimed=row
        if (index,a,b,s)!=(str(i),str(i%2),str(1-i%2),str(i//2)):return {'status':'unknown','reason':'wrong/duplicate vector identity'}
        expected=b if s=='1' else a
        if y not in ('0','1'):return {'status':'unknown','reason':'unknown output value'}
        if claimed!=expected:return {'status':'fail','reason':'reviewed checker expectation disagrees with independent mux relation'}
        failures+=y!=expected
    if terminals[0]!=failures:return {'status':'unknown','reason':'terminal disagrees with recomputed observations'}
    return {'status':'fail' if failures else 'pass','checks':4,'failures':failures,'authority':'exact reviewed fixture plus independent host mux relation; not arbitrary stdout authenticity'}
