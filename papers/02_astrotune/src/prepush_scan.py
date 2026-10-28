"""Read-only scan of index plus all reachable Git blob history, recursive archives.
No match payload printed/stored; only counts and object/path identifiers on issues.
"""
import subprocess,re,io,tarfile,zipfile,json,hashlib
from pathlib import Path
REPO=Path('/workspace/PaperReproduction')
def git(*a):return subprocess.check_output(['git','-C',str(REPO),*a])
patterns={
 'internal_infrastructure_domain':rb'(?i)\b(?:(?:[a-z0-9-]+\.)*openai\.org|(?:[a-z0-9-]+\.)+(?:internal|corp|localdomain))(?::[0-9]+)?\b',
 'private_ipv4':rb'\b(?:10\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b',
 'pasted_key_family':rb'\bnrk_[A-Za-z0-9_-]{20,}',
 'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'github_token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})',
 'aws_access':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'openai_key':rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}',
 'credential_assignment':rb'(?im)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[=:]\s*["\x27]([A-Za-z0-9_+/-]{24,})["\x27]',
 'proxy_environment':rb'(?im)^\s*(?:export\s+)?(?:HTTPS?_PROXY|ALL_PROXY|CODEX_APPS_AUTHORIZATION|CODEX_CONNECTORS_TOKEN)\s*=',
 'credential_url':rb'https?://[^\s/"\x27:]+:[^\s/@"\x27]+@',
}
patterns={k:re.compile(v) for k,v in patterns.items()};hits=[];archive_members=0;checked=set();sizes=[]
sensitive_path=re.compile(r'(^|/)(?:\.env(?:\..*)?|\.netrc|\.npmrc|\.aws|\.ssh|auth\.json|credentials(?:\.json)?|proxy[_-]?env)(/|$)',re.I)
def scan(data,label,depth=0):
 global archive_members
 digest=hashlib.sha256(data).digest()
 if digest in checked:return
 checked.add(digest)
 for name,pat in patterns.items():
  if pat.search(data):hits.append({'kind':name,'location':label})
 if depth>=3:return
 try:
  if data.startswith(b'\x1f\x8b'):
   with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
    for m in t:
     if m.isfile():
      archive_members+=1
      if sensitive_path.search(m.name):hits.append({'kind':'sensitive_archive_path','location':label+'!'+m.name})
      f=t.extractfile(m);scan(f.read(),label+'!'+m.name,depth+1)
  elif data.startswith(b'PK\x03\x04'):
   with zipfile.ZipFile(io.BytesIO(data)) as z:
    for n in z.namelist():archive_members+=1;scan(z.read(n),label+'!'+n,depth+1)
 except (tarfile.TarError,zipfile.BadZipFile,EOFError):hits.append({'kind':'archive_parse_failed','location':label})
objects=git('rev-list','--objects','--all').splitlines();blobs=0
for line in objects:
 parts=line.split(b' ',1);oid=parts[0].decode();name=parts[1].decode(errors='replace') if len(parts)>1 else ''
 if git('cat-file','-t',oid).strip()!=b'blob':continue
 blobs+=1;size=int(git('cat-file','-s',oid));sizes.append((size,name,oid))
 if sensitive_path.search(name):hits.append({'kind':'sensitive_git_path','location':name,'oid':oid})
 scan(git('cat-file','blob',oid),'git:'+oid+':'+name)
index_files=git('ls-files','-z').split(b'\0');index_count=0
for n in index_files:
 if not n:continue
 index_count+=1;name=n.decode();scan(git('show',':'+name),'index:'+name)
 if sensitive_path.search(name):hits.append({'kind':'sensitive_index_path','location':name})
# Restrict tracked scope to task artifacts and three root policy/readme files.
unrelated=[n.decode() for n in index_files if n and not n.decode().startswith('papers/02_astrotune/') and n.decode() not in ('README.md','.gitignore','.gitattributes')]
result={'reachable_commit_count':int(git('rev-list','--count','--all')),'reachable_blob_count':blobs,'index_file_count':index_count,'distinct_content_scanned':len(checked),'nested_archive_members_examined':archive_members,'sensitive_findings_count':len(hits),'sensitive_findings_identifiers_only':hits,'unrelated_tracked_paths':unrelated,'largest_blobs':[{'bytes':a,'path':b,'oid':c} for a,b,c in sorted(sizes,reverse=True)[:12]],'over_50MiB_blob_count':sum(a>50*1024**2 for a,b,c in sizes),'over_100MiB_blob_count':sum(a>100*1024**2 for a,b,c in sizes),'limitations':'Pattern/manual-scope scan, not proof against arbitrary unknown secrets. No raw matched value or supplied chat credential is emitted. All reachable refs scanned, plus staged index; nested tar.gz/zip contents inspected read-only.'}
out=Path('/workspace/scratch/astrotune/prepush_infra_scan.json');out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('sensitive_findings_identifiers_only','largest_blobs','unrelated_tracked_paths')},indent=2));print('unrelated_path_count',len(unrelated));print('largest_blob_bytes',max(a for a,b,c in sizes))
