"""Recreate verified workspace Icarus from official Debian metadata/package.
No system install; never reads NR_KEY. Network uses explicit proxy-only whitelist.
Model and verifier workers must NOT use this downloader environment.
"""
import argparse,hashlib,json,lzma,os,platform,re,shutil,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
SAFE={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':'/tmp','LANG':'C.UTF-8'}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,**kw):return subprocess.run(args,env=SAFE,check=True,**kw)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--prefix',type=Path,default=Path('/workspace/free-tools/iverilog'));parser.add_argument('--acquire',action='store_true');parser.add_argument('--build-image',action='store_true');args=parser.parse_args();base=args.prefix;base.mkdir(parents=True,exist_ok=True)
 assert platform.machine()=='x86_64' and 'trixie' in Path('/etc/os-release').read_text(),'recipe requires inspected Debian13 amd64; review other hosts explicitly'
 expected=json.loads((P.parent/'metrics/verified_toolchain.json').read_text());idx=json.loads((P/'toolchain_provenance/index_expected.json').read_text())
 package_url='https://deb.debian.org/debian/pool/main/i/iverilog/iverilog_12.0-2+b1_amd64.deb'
 if args.acquire:
  transport_env=dict(SAFE)
  for name in ('HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','NO_PROXY','SSL_CERT_FILE','CURL_CA_BUNDLE'):
   if name in os.environ:transport_env[name]=os.environ[name]
  for name,url in [('InRelease','https://deb.debian.org/debian/dists/trixie/InRelease'),('Packages.xz','https://deb.debian.org/debian/dists/trixie/main/binary-amd64/Packages.xz'),('iverilog.deb',package_url)]:
   # Known official URLs only. No header/key/proxy value logging.
   result=subprocess.run(['curl','-fL','--max-time','90',url,'-o',str(base/name)],env=transport_env,capture_output=True)
   assert result.returncode==0,'official package acquisition failed; stop without alternate sources'
 assert digest(base/'InRelease')==expected['inrelease_sha256'],'release changed; review new signed provenance before continuing'
 home=base/'gnupg';home.mkdir(exist_ok=True,mode=0o700)
 verified=run(['gpg','--batch','--no-default-keyring','--no-auto-key-retrieve','--homedir',str(home),'--keyring','/usr/share/keyrings/debian-archive-keyring.gpg','--verify',str(base/'InRelease')],capture_output=True)
 assert digest(base/'Packages.xz')==idx['sha256'] and (base/'Packages.xz').stat().st_size==idx['bytes']
 records=lzma.decompress((base/'Packages.xz').read_bytes()).decode().split('\n\n');record=next(x for x in records if x.startswith('Package: iverilog\n'));assert ('SHA256: '+expected['package_sha256']) in record
 assert digest(base/'iverilog.deb')==expected['package_sha256']
 run(['dpkg-deb','-x',str(base/'iverilog.deb'),str(base/'root')])
 bindir=base.parent/'bin';bindir.mkdir(exist_ok=True)
 for name in ['iverilog','vvp']:
  extra=['-B',str(base/'root/usr/lib/x86_64-linux-gnu/ivl')] if name=='iverilog' else []
  import shlex
  wrapper=bindir/name;wrapper.write_text('#!/bin/sh\nexec '+shlex.join([str(base/'root/usr/bin'/name),*extra])+' "$@"\n');wrapper.chmod(0o755)
 if args.build_image:
  context=base/'docker-context';root=context/'rootfs';context.mkdir(exist_ok=True);shutil.copytree(base/'root',root,dirs_exist_ok=True);(root/'bin').mkdir(exist_ok=True);shutil.copy2('/bin/sh',root/'bin/sh',follow_symlinks=True)
  libraries=set()
  for binary in [x for x in root.rglob('*') if x.is_file() and x.open('rb').read(4)==b'\x7fELF']:
   r=subprocess.run(['ldd',str(binary)],env=SAFE,capture_output=True,text=True)
   for name in re.findall(r'(?:=>\s+|^\s*)(/[^\s]+)',r.stdout,re.M):
    if Path(name).is_file():libraries.add(name)
  for name in libraries:
   target=root/name.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():shutil.copy2(name,target,follow_symlinks=True)
  for name in ['tmp','work']:(root/name).mkdir(exist_ok=True)
  for directory in [root,*root.rglob('*')]:
   if directory.is_dir():directory.chmod(0o755)
  (root/'tmp').chmod(0o1777);shutil.copyfile(P/'toolchain_provenance/Dockerfile',context/'Dockerfile')
  run(['docker','build','--no-cache','--network=none','--tag','trace2skill-local/iverilog:12.0-debian-verified',str(context)],capture_output=True)
  image=run(['docker','image','inspect','--format','{{.Id}}','trace2skill-local/iverilog:12.0-debian-verified'],capture_output=True,text=True).stdout.strip()
  print(json.dumps({'toolchain':'prepared','image_id':image,'note':'fresh image may have another ID; use inspected ID explicitly, do not silently change a scientific run'}))
 else:print(json.dumps({'toolchain':'prepared','bin':str(bindir),'model_requests':0}))
if __name__=='__main__':main()
