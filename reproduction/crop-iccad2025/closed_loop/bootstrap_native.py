#!/usr/bin/env python3
"""Restore pinned free tools locally; no system installation or credentials."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT=Path(__file__).resolve().parent
records=json.loads((ROOT/'native/downloads.json').read_text())
for record in records:
    path=ROOT/'native'/record['path']
    if not path.exists():
        # Stop on denial. No authentication, alternate endpoints or automatic retries.
        with urllib.request.urlopen(record['url'],timeout=30) as response:
            data=response.read(25_000_001)
        if len(data)>25_000_000: raise SystemExit('Package size cap exceeded')
        if hashlib.sha256(data).hexdigest()!=record['sha256']:
            raise SystemExit('Package hash mismatch')
        path.write_bytes(data)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
        raise SystemExit('Existing package hash mismatch')
    subprocess.run(['dpkg-deb','-x',str(path),str(ROOT/'native/root')],check=True)
subprocess.run([str(ROOT/'native/root/usr/bin/yosys'),'-V'],check=True)
