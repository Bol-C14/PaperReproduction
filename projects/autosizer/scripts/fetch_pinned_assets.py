"""Recreate only the recorded minimal free assets; abort on changed bytes or source."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
budget = json.loads((ROOT/'configs/budget.json').read_text())
if (ROOT/'results/PHASE_CLOSED.json').exists():
    raise SystemExit('Phase closed; future downloads require a newly authorized protocol')
if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(budget['deadline_utc']):
    raise SystemExit('Time budget exhausted')
records = json.loads((ROOT/'provenance/downloads.json').read_text())
required = {'debian_InRelease', 'debian_Packages.xz', 'ngspice_44.2+ds-1_amd64.deb',
            'LICENSE', 'models/all.spice', 'models/parameters/critical.spice',
            'models/parameters/lod.spice', 'models/corners/tt/nonfet.spice'}
required |= {f'cells/{t}_01v8/sky130_fd_pr__{t}_01v8__{s}.spice'
             for t in ['nfet','pfet'] for s in ['tt.corner','tt.pm3','mismatch.corner']}
transferred = sum(r.get('bytes',0) for r in records)
events_path = ROOT/'logs/download_replay_events.json'
events = json.loads(events_path.read_text()) if events_path.exists() else []
transferred += sum(e['bytes'] for e in events)
for r in records:
    if r['file'] not in required or 'error' in r:
        continue
    target = ROOT/'downloads'/r['file']
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == r['sha256']:
        continue
    host = urllib.parse.urlsplit(r['url']).hostname
    assert host in {'deb.debian.org','raw.githubusercontent.com'}
    if transferred+r['bytes'] > budget['max_download_bytes']:
        raise SystemExit('Download budget would be exceeded')
    with urllib.request.urlopen(r['url'], timeout=30) as response:
        data = response.read(r['bytes']+1)
    events.append({'file':r['file'],'url':r['url'],'bytes':len(data),
                   'utc':dt.datetime.now(dt.timezone.utc).isoformat()})
    events_path.write_text(json.dumps(events,indent=2))
    transferred += len(data)
    assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'], r['file']
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
print('All required pinned assets verified; no model or paid-service calls')
