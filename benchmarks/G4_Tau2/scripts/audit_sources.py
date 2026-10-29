"""Metadata only; run on controller host, never in an evaluated workspace."""
from pathlib import Path
import hashlib,json,subprocess,platform,datetime,os
ROOT=Path(os.environ['TAU2_REPRO_ROOT']).resolve()
paper=ROOT/'checkouts/tau2/paper'; upstream=ROOT/'checkouts/tau2/upstream'
def git(*args):return subprocess.check_output(['git','-C',str(upstream),*args],text=True).strip()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=list((paper/'data/tau2/domains/telecom').rglob('*'))
paths += list((paper/'src/tau2').rglob('*.py'))
paths += [paper/x for x in ['pdm.lock','pyproject.toml','LICENSE','README.md']]
hashes={str(p.relative_to(paper)):sha(p) for p in paths if p.is_file()}
datasets={}
for p in (paper/'data/tau2/domains/telecom').glob('tasks*.json'):
    tasks=json.loads(p.read_text())
    datasets[p.name]={'count':len(tasks),'sha256':sha(p),'reward_bases':{str(b):sum(tuple(t['evaluation_criteria']['reward_basis'])==b for t in tasks) for b in {tuple(t['evaluation_criteria']['reward_basis']) for t in tasks}}}
meta={'audit_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'paper_commit':git('rev-parse','v0.1.0^{commit}'),'paper_tag_object':git('rev-parse','v0.1.0'),'candidate_v013':git('rev-parse','v0.1.3^{commit}'),'current_audit_commit':git('rev-parse','HEAD'),'tags':git('tag').splitlines(),'platform':platform.platform(),'python':platform.python_version(),'git_version':subprocess.check_output(['git','--version'],text=True).strip(),'bubblewrap_version':subprocess.check_output(['bwrap','--version'],text=True).strip(),'uv_version':subprocess.check_output(['uv','--version'],text=True).strip(),'datasets':datasets,'source_hashes':hashes,'paper_html_sha256':sha(ROOT/'assets/tau2/paper-v1.html'),'source_clean':subprocess.check_output(['git','-C',str(paper),'status','--porcelain'],text=True),'source_pack':git('count-objects','-vH')}
(ROOT/'results/tau2/source-audit.json').write_text(json.dumps(meta,indent=2))
main=paper/'data/tau2/domains/telecom/tasks.json'
main_tasks=json.loads(main.read_text())
inventory={'source_commit':meta['paper_commit'],'source_path':str(main.relative_to(paper)),'source_sha256':sha(main),'rows':[{'task_id':t['id'],'required_components':t['evaluation_criteria']['reward_basis']} for t in main_tasks]}
(ROOT/'results/tau2/reward-basis-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
print(json.dumps({k:v for k,v in meta.items() if k!='source_hashes'},indent=2))
