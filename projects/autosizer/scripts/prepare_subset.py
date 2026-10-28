"""Build a transparent two-device tt selector; never alter official model bodies."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'downloads'
header = (source / 'models/all.spice').read_text().split('* include all individual diode models')[0]
# Preserve upstream scale and rotweak declarations. Make its one include absolute.
header = header.replace('"parameters/lod.spice"', '"' + str(source / 'models/parameters/lod.spice') + '"')
includes = ['models/parameters/critical.spice', 'models/corners/tt/nonfet.spice']
includes += [f'cells/{t}_01v8/sky130_fd_pr__{t}_01v8__{s}.spice'
             for t in ['nfet', 'pfet'] for s in ['mismatch.corner', 'tt.corner']]
body = '* Local selector of official unmodified SKY130 tt model files\n.lib tt\n' + header
body += ''.join(f'.include "{source / name}"\n' for name in includes) + '.endl tt\n'
out = ROOT / 'tools/sky130_subset.lib.spice'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(body)
manifest = {'kind': 'local_selection_wrapper_not_new_model',
            'upstream_commit': 'f62031a1be9aefe902d6d54cddd6f59b57627436',
            'corner': 'tt', 'scale': '1e-6_from_upstream_all.spice',
            'selector_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
            'header_source': 'models/all.spice prefix before diode includes',
            'includes': includes,
            'model_bodies_modified': False}
(ROOT / 'provenance/pdk_subset.json').write_text(json.dumps(manifest, indent=2))
print(out)
