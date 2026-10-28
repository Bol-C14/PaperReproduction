"""Read-only staged/reachable-object scan; print locations/counts, never matches.

This is a bounded pattern and high-entropy review aid, not a proof that arbitrary
secrets cannot exist. Binary NPZ payloads are checked without pickle loading.
"""
from pathlib import Path
import argparse,hashlib,io,json,math,re,subprocess,zipfile

REPO=Path(__file__).resolve().parents[2]
PATTERNS={
 'private_key':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
 'github_token':re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
 'openai_key':re.compile(rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}'),
 'aws_access_key':re.compile(rb'(?:AKIA|ASIA)[A-Z0-9]{16}'),
 'google_key':re.compile(rb'AIza[A-Za-z0-9_-]{30,}'),
 'slack_token':re.compile(rb'xox[baprs]-[A-Za-z0-9-]{20,}'),
 'jwt':re.compile(rb'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),
 'auth_header_value':re.compile(rb'(?im)^\s*(?:authorization|proxy-authorization)\s*:\s*(?:Bearer|Basic)\s+[A-Za-z0-9+/=_-]{12,}'),
 'cookie_header_value':re.compile(rb'(?im)^\s*(?:cookie|set-cookie)\s*:\s*[^\s]{8,}'),
 'credentialed_url':re.compile(rb'https?://[^\s/@:]+:[^\s/@]{6,}@'),
 'literal_secret_assignment':re.compile(rb'''(?i)(?:api[_-]?key|secret[_-]?key|client[_-]?secret|password|access[_-]?token)\s*[=:]\s*["'][A-Za-z0-9+/=_-]{16,}["']'''),
 'internal_service_domain':re.compile(rb'(?i)\b[a-z0-9][a-z0-9.-]*\.(?:internal|corp|svc\.cluster\.local)\b'),
}


def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--ref');parser.add_argument('--output');args=parser.parse_args()
    objects=[];files=[]
    if args.ref:
        for row in git('rev-list','--objects',args.ref).decode().splitlines():
            oid,_,name=row.partition(' ')
            kind=git('cat-file','-t',oid).decode().strip()
            objects.append((oid,kind,name))
    else:
        for row in git('ls-files','--stage','-z').split(b'\0'):
            if not row:continue
            meta,name=row.split(b'\t',1);mode,oid,stage=meta.decode().split()
            if stage!='0':raise RuntimeError('Unmerged index')
            objects.append((oid,'blob',name.decode()))
    findings=[];entropy_candidates=[];binary=[];seen=set()
    for oid,kind,name in objects:
        if oid in seen:continue
        seen.add(oid)
        payload=git('cat-file',kind,oid)
        for category,pattern in PATTERNS.items():
            for match in pattern.finditer(payload):
                findings.append({'object':oid,'path':name,'category':category,'line':payload[:match.start()].count(b'\n')+1})
        if kind=='blob' and name:
            files.append({'path':name,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()})
            if any(part in {'.env','.aws','.ssh','.git-credentials','cookies.txt'} for part in Path(name).parts):
                findings.append({'object':oid,'path':name,'category':'credential_file_path'})
            if name.endswith('.npz'):
                import numpy as np
                with np.load(io.BytesIO(payload),allow_pickle=False) as archive:
                    arrays=[]
                    for key in archive.files:
                        value=archive[key]
                        if value.dtype!=np.float32 or value.shape!=(8,256):raise ValueError('Unexpected embedding artifact structure')
                        arrays.append({'name':key,'dtype':str(value.dtype),'shape':list(value.shape)})
                binary.append({'path':name,'inspection':'numpy allow_pickle=False; numeric embeddings only','arrays':arrays})
            else:
                for match in re.finditer(rb'''["']([A-Za-z0-9_+/=-]{28,})["']''',payload):
                    token=match.group(1)
                    if re.fullmatch(rb'[0-9a-fA-F]+',token):continue
                    probabilities=[token.count(c)/len(token) for c in set(token)]
                    entropy=-sum(v*math.log2(v) for v in probabilities)
                    if entropy>4.2:
                        entropy_candidates.append({'path':name,'line':payload[:match.start()].count(b'\n')+1,'token_sha256':hashlib.sha256(token).hexdigest(),'entropy':round(entropy,3)})
    result={'scope':'all reachable commit/tree/blob objects' if args.ref else 'all staged file blobs','ref':args.ref,'object_count':len(seen),'file_count':len(files),'total_file_bytes':sum(x['bytes'] for x in files),'credential_patterns_and_internal_domain_findings':findings,'high_entropy_candidates_for_review':entropy_candidates,'numeric_binary_inspections':binary,'files':files,'limitations':'Pattern/entropy scanning plus file-purpose review cannot prove absence of every possible secret. Package-version/CPU-resource metadata is included; no environment-variable dump is included.'}
    if args.output:Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['scope','object_count','file_count','total_file_bytes','credential_patterns_and_internal_domain_findings','high_entropy_candidates_for_review']}))
    raise SystemExit(1 if findings or entropy_candidates else 0)

if __name__=='__main__':main()
