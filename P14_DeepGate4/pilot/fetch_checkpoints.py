"""Bounded public-file fetch; byte/hash inspection only, no unpickling."""
from pathlib import Path
import urllib.request, hashlib, json, time
ROOT = Path(__file__).resolve().parent
CACHE = ROOT.parent / '.checkpoint-cache'
CACHE.mkdir(exist_ok=True)
SHA = '85e20742a2d4702426f94e86666cdcdb408fba8a'
EXPECTED = {'model_last.pth': 'c0663c81375f4df7a7740db3e4ad6180cecc5ed5', 'model_last_workload.pth': '85bf4a4655e2b844ad93a0812ffeec4b0bba8757'}
rows=[]
for name, expected in EXPECTED.items():
    url=f'https://raw.githubusercontent.com/zyzheng17/DeepGate4-ICLR-25/{SHA}/trained/{name}'
    path=CACHE/name
    started=time.monotonic()
    downloaded=0
    if not path.exists():
        with urllib.request.urlopen(url,timeout=30) as response, path.open('wb') as out:
            while chunk:=response.read(1024*1024):
                downloaded+=len(chunk)
                if downloaded>20_000_000:
                    raise RuntimeError('20 MB per checkpoint size gate')
                out.write(chunk)
    payload=path.read_bytes()
    blob=hashlib.sha1(f'blob {len(payload)}\0'.encode()+payload).hexdigest()
    assert blob==expected, (name,blob,expected)
    rows.append(dict(file=name,url=url,bytes=len(payload),downloaded_bytes=downloaded,sha256=hashlib.sha256(payload).hexdigest(),git_blob=blob,elapsed_seconds=time.monotonic()-started))
(ROOT/'checkpoint_fetch.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(rows,indent=2))
