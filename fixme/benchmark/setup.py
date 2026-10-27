"""Fetch pinned public inputs. Does not execute upstream scripts or change system packages."""
import argparse,hashlib,json,pathlib,subprocess,urllib.request
PIN='e875437fbb11590b71775b32d3579726d702cfc6'
p=argparse.ArgumentParser();p.add_argument('--root',default='.cache');a=p.parse_args();r=pathlib.Path(a.root).resolve();r.mkdir(parents=True,exist_ok=True)
u=r/'upstream'
if not u.exists(): subprocess.run(['git','-c','core.hooksPath=/dev/null','clone','--no-checkout','https://github.com/ChatDesignVerification/FIXME.git',str(u)],check=True)
subprocess.run(['git','-C',str(u),'-c','core.hooksPath=/dev/null','checkout','--detach',PIN],check=True)
packages=[('iverilog','12.0-2+b1'),('verilator','5.032-1+b2'),('yosys','0.52-2')]; records=[]
for name,version in packages:
 url=f'https://deb.debian.org/debian/pool/main/{name[0]}/{name}/{name}_{version}_amd64.deb';f=r/f'{name}.deb'
 if not f.exists():urllib.request.urlretrieve(url,f)
 expected={'iverilog':'febe027d2d3f5a7e570844d55758339ab5490acc09f404f214a8719d89d07056','verilator':'238ab4ca84cddd371f113cd549f16f2d65c43e7b4962a763bea1d259158dd3b2','yosys':'c950e58a1f554546a91602e5124eb05019a92040e57b0aaa43cf33b032ee9c40'}
 if hashlib.sha256(f.read_bytes()).hexdigest()!=expected[name]:raise SystemExit('Package hash mismatch: '+name)
 subprocess.run(['dpkg-deb','-x',str(f),str(r/'tools')],check=True)
 records.append(dict(name=name,version=version,url=url,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(r/'setup.json').write_text(json.dumps(dict(upstream=PIN,packages=records),indent=2))
print(r)
