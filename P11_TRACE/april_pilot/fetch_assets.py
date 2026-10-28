import urllib.request,json,hashlib,time
from pathlib import Path
R=Path(__file__).resolve().parent
base='https://raw.githubusercontent.com/zyzheng17/TRACE_DAC26/b207dd94670f34ed3d51f0f8bcb5cd5be9ebaa70/'
items={'hf_metadata.json':'https://huggingface.co/api/datasets/zyzheng23/TRACE_dataset?blobs=true','upstream_README.md':base+'README.md','loader.py':base+'tasks/predictive/pm/dataset/loader.py','eval.py':base+'tasks/predictive/pm/eval.py','official_pm_probability.pth':base+'checkpoints/trace_predictive_pm_probability.pth'}
report=[]
for name,url in items.items():
 try:
  with urllib.request.urlopen(url,timeout=45) as f:data=f.read()
  (R/name).write_bytes(data)
  report.append(dict(name=name,url=url,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status='downloaded'))
 except Exception as e:report.append(dict(name=name,url=url,status='failed',error=str(e)))
 print(json.dumps(report[-1]),flush=True)
(R/'asset_receipt.json').write_text(json.dumps(report,indent=2)+'\n')
