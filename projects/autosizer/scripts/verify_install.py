"""Verify official Debian signatures/hash chain and locally extract ngspice."""
from pathlib import Path
import hashlib
import json
import lzma
import subprocess

ROOT = Path(__file__).resolve().parents[1]
if (ROOT/'results/PHASE_CLOSED.json').exists():
    raise SystemExit('Phase closed; preparation is documented for a future authorized replay')
env = {'PATH':'/usr/bin:/bin','LC_ALL':'C'}
keyhome = ROOT/'tools/verification-home'
keyhome.mkdir(parents=True,exist_ok=True)
keyhome.chmod(0o700)
command = ['gpg','--no-options','--homedir',str(keyhome),'--no-default-keyring',
           '--keyring','/usr/share/keyrings/debian-archive-keyring.gpg','--verify',
           str(ROOT/'downloads/debian_InRelease')]
verified = subprocess.run(command,env=env,capture_output=True,text=True,check=True)
(ROOT/'logs/debian_signature.log').write_text(verified.stdout+verified.stderr)
index = ROOT/'downloads/debian_Packages.xz'
assert hashlib.sha256(index.read_bytes()).hexdigest() in (ROOT/'downloads/debian_InRelease').read_text()
package = json.loads((ROOT/'provenance/debian_packages.json').read_text())[0]
stanza = next(block for block in lzma.decompress(index.read_bytes()).decode().split('\n\n')
              if block.startswith('Package: ngspice\n'))
for key in ['Version', 'Filename', 'Size', 'SHA256']:
    assert f'{key}: {package[key]}\n' in stanza+'\n'
deb = ROOT/'downloads'/Path(package['Filename']).name
assert hashlib.sha256(deb.read_bytes()).hexdigest() == package['SHA256']
assert deb.stat().st_size==int(package['Size'])
subprocess.run(['dpkg-deb','-x',str(deb),str(ROOT/'tools/ngspice')],env=env,check=True)
print('Verified package locally extracted; no maintainer scripts or system installation')
