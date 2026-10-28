"""Restore included licensed model sources into the ignored runtime asset directory.

No downloads, simulator invocations, package installation or closed-phase changes.
"""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'provenance/vendored_sky130_manifest.json').read_text())
for entry in manifest:
    source=ROOT/entry['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['sha256']
    relative=source.relative_to(ROOT/'vendor/sky130_tt')
    target=ROOT/'downloads'/relative
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest()!=entry['sha256']:
            raise RuntimeError(f'Refusing to overwrite different existing asset: {relative}')
    else:
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
print(f'{len(manifest)} official model source files restored/verified; no simulation or network access.')
