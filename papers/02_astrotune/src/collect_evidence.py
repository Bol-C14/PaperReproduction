"""Compact raw logs, unique mapped netlists and one real placed artifact; no caches."""
from pathlib import Path
import json,hashlib,tarfile,gzip,shutil
ROOT=Path(__file__).resolve().parents[1];art=ROOT/'artifacts';art.mkdir(exist_ok=True);(art/'netlists').mkdir(exist_ok=True)
records=[json.loads(l) for p in (ROOT/'results').glob('*.jsonl') for l in p.read_text().splitlines()];manifest={d['id']:d for d in json.loads((ROOT/'benchmarks/manifest.json').read_text())['designs']};stats={}
for r in records:
 if r['stage']!='synth' or r['status']!='ok':continue
 net=ROOT/r['out']/'net.v';assert hashlib.sha256(net.read_bytes()).hexdigest()==r['net_sha256'];dest=art/'netlists'/(r['net_sha256']+'.v')
 if not dest.exists():shutil.copy2(net,dest)
 j=json.loads((ROOT/r['out']/'net.json').read_text());mod=j['modules'][manifest[r['design']]['top']]
 stats[r['design'],r['s']]={'design':r['design'],'s':r['s'],'net_sha256':r['net_sha256'],'mapped_cells':len(mod['cells']),'ports':len(mod['ports']),'netnames':len(mod['netnames'])}
(ROOT/'results/netlist_stats.json').write_text(json.dumps(list(stats.values()),indent=2))
# Hash-check EVERY child input against shipped content-addressed netlist bytes.
for r in records:
 if r['status']=='ok' and r['stage']=='place':assert hashlib.sha256((art/'netlists'/(r['parent_net_sha256']+'.v')).read_bytes()).hexdigest()==r['net_sha256']
pilot=ROOT/'work/multi_pipe_8bit_gp_single_0/0001_place';(art/'placed_example').mkdir(exist_ok=True)
for n in ('placed.def','placed.odb','eval.tcl','openroad.log'):
 if (pilot/n).exists():shutil.copy2(pilot/n,art/'placed_example'/n)
paths=[p for p in (ROOT/'work').rglob('*') if p.is_file() and (p.suffix in ('.log','.ys','.tcl') or p.name=='tb.v')]
archive=ROOT/'logs/raw_eda_and_validation.tar.gz'
with archive.open('wb') as f,gzip.GzipFile(fileobj=f,mode='wb',mtime=0) as z,tarfile.open(fileobj=z,mode='w') as t:
 for p in sorted(paths):
  info=t.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  with p.open('rb') as r:t.addfile(info,r)
print(json.dumps({'raw_log_files':len(paths),'archive_bytes':archive.stat().st_size,'unique_shipped_netlists':len(list((art/'netlists').glob('*.v'))),'all_child_netlist_hashes_verified':True},indent=2))
