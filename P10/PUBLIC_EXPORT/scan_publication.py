"""Local pre-publication gate. Never prints matched secret values."""
import collections,hashlib,json,pathlib,re,subprocess,sys

REPO=pathlib.Path(__file__).resolve().parents[2]
PATTERNS={
 'private_key':rb'-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----',
 'aws_key':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'github_token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
 'openai_token':rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}\b',
 'google_key':rb'\bAIza[0-9A-Za-z_-]{35}\b',
 'slack_token':rb'\bxox[baprs]-[0-9A-Za-z-]{20,}\b',
 'jwt':rb'\beyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b',
 'url_userinfo':rb'https?://[^\s/:@]+:[^\s/@]+@',
 'bearer_header':rb'(?i)authorization[\s\x22\x27:=]+bearer\s+[A-Za-z0-9_./+-]{16,}',
 'credential_literal':rb'(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|secret[_-]?key)\s*[:=]\s*[\x22\x27]([^\x22\x27\n]{12,})[\x22\x27]',
 'internal_endpoint':rb'(?:[A-Za-z0-9.-]+\.)?(?:ace-research\.openai\.org|openai\.org|internal\.[A-Za-z0-9.-]+|localhost:[0-9]+|127\.0\.0\.1:[0-9]+)',
 'signed_url':rb'https?://[^\s\x22\x27]+[?&](?:X-Amz-Signature|sig|token|access_token)=[^\s\x22\x27]{16,}',
 'environment_dump':rb'(?m)^(?:AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN|OPENAI_API_KEY|CODEX_CONNECTORS_TOKEN|HTTP_COOKIE|AUTHORIZATION)=.+$',
 'cookie_header':rb'(?im)^(?:set-cookie|cookie):\s*[^\n]{16,}$',
 'private_library_identifier':rb'\blibfile_[a-f0-9]{32}\b',
}
DENIED_PATH=re.compile(r'(^|/)(\.env(?:\.[^/]*)?|auth\.json|credentials|cookies(?:\.txt|\.json)?|id_rsa|id_ed25519|\.venv|vendor|\.cache|__pycache__)(/|$)|\.(bundle|zip|whl|pt|pth|ckpt|safetensors)$|\.tar\.(gz|xz|zst)$')


def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])


def main(output):
    patterns={k:re.compile(v) for k,v in PATTERNS.items()};findings=[];counts=collections.Counter()
    def inspect(data,source):
        for label,pattern in patterns.items():
            for m in pattern.finditer(data):findings.append({'source':source,'category':label,'match_sha256':hashlib.sha256(m.group()).hexdigest(),'match_bytes':len(m.group())})
    head=git('rev-parse','HEAD').decode().strip();commits=git('rev-list',head).decode().splitlines()
    oids=git('rev-list','--objects','--no-object-names',head).decode().splitlines()
    proc=subprocess.Popen(['git','-C',str(REPO),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid in oids:
        proc.stdin.write((oid+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().decode().split();data=proc.stdout.read(int(header[2]));assert proc.stdout.read(1)==b'\n'
        counts[header[1]]+=1
        if header[1] in ('blob','commit','tag'):inspect(data,'object:'+oid)
    proc.stdin.close();assert proc.wait()==0
    historical_paths=0
    for commit in commits:
        for entry in git('ls-tree','-rz','--name-only',commit).decode().split('\0')[:-1]:
            historical_paths+=1
            if DENIED_PATH.search(entry):findings.append({'source':'historical-path-sha256:'+hashlib.sha256(entry.encode()).hexdigest(),'category':'excluded_asset_in_history'})
    working=git('ls-files','-z').decode().split('\0')[:-1]
    for name in working:
        path=REPO/name
        if path.is_symlink():inspect(str(path.readlink()).encode(),'working:'+name)
        else:inspect(path.read_bytes(),'working:'+name)
        if DENIED_PATH.search(name):findings.append({'source':'path-sha256:'+hashlib.sha256(name.encode()).hexdigest(),'category':'excluded_asset_in_index'})
    result={'head':head,'branch':git('branch','--show-current').decode().strip(),'commits':len(commits),'object_counts':dict(counts),
            'working_files':len(working),'historical_path_occurrences':historical_paths,'detectors':list(PATTERNS),
            'findings':findings,'passed':not findings,'scope':'All reachable branch objects plus every historical tree path and indexed working file; unrelated refs and raw Git auth/config excluded',
            'limitations':'Static signatures/assignment/header/path scan, not an absolute guarantee; matching values never printed'}
    pathlib.Path(output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='findings'}))
    return 1 if findings else 0


if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python scan_publication.py LOCAL_REPORT_JSON')
    raise SystemExit(main(sys.argv[1]))
