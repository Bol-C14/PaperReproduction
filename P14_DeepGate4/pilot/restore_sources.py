"""Optional bounded restoration of seven original files from pinned public URLs.

This is a recovery helper, not a research run. Existing files are never replaced.
Sources stay in the ignored code/ directory; no licenses or gates are accepted.
"""
from pathlib import Path
import hashlib,json,urllib.request
ROOT=Path(__file__).resolve().parent

def main():
    manifest=json.loads((ROOT/'source_provenance.json').read_text())
    entries={e['path']:e for e in manifest['text_source_files']}
    target_root=(ROOT.parent/'code').resolve()
    downloaded=0
    for relative in manifest['required_for_CPU_pilot']:
        entry=entries[relative]
        target=(target_root/relative).resolve()
        if not target.is_relative_to(target_root):raise ValueError('Invalid source path')
        if target.exists():
            payload=target.read_bytes()
        else:
            if entry['bytes']>100_000:raise ValueError('Per-file size gate')
            request=urllib.request.Request(entry['url'])
            with urllib.request.urlopen(request,timeout=30) as response:
                payload=response.read(entry['bytes']+1)
            downloaded+=len(payload)
            if downloaded>300_000:raise ValueError('Total source restore size gate')
        if len(payload)!=entry['bytes'] or hashlib.sha256(payload).hexdigest()!=entry['sha256']:
            raise ValueError(f'Source mismatch: {relative}')
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as out:out.write(payload)
        print('Verified',relative)
    print('Downloaded bytes',downloaded)

if __name__=='__main__':main()
