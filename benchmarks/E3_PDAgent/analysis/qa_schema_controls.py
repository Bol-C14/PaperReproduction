"""Novel schema probe, NOT the unreleased official QA checker. No model calls.
References/candidate text remain private; output contains hashes and outcomes.
"""
import sys,json,hashlib,re
from pathlib import Path
root=Path(sys.argv[1]);out=Path(sys.argv[2]);rows=[]
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
a={x['id']:x for x in json.load(open(root/'sta/sta_benchmark.json'))}
for task in ('TC_03','TC_11'):
 q=a[task];ref=q.get('answer') or q['accepted_answers'][0]
 if task=='TC_03':
  values=re.findall(r'(\d+(?:\.\d+)?)ns',ref)
  assert len(values)==2
  paraphrase='Setup and hold slack decrease by '+format(float(values[0])*1000,'g')+' ps and '+format(float(values[1])*1000,'g')+' ps, respectively.'
  variants={'reference':ref,'valid_paraphrase':paraphrase,'wrong_keyword_prefix':'The following claim is false: '+ref+' Both slacks actually improve.'}
 else:
  option=next(x for x in q['options'] if x.startswith(ref+'.'))
  wrong=next(x[0] for x in q['options'] if not x.startswith(ref+'.'))
  variants={'reference':ref,'valid_option_text':option,'wrong_option':wrong,'wrong_keyword_prefix':ref+' is wrong; '+wrong+' is correct.'}
 for kind,value in variants.items():
  rows.append({'task_id':task,'control':kind,'candidate_sha256':digest(value),'reference_sha256':digest(ref),'stated_verification_type':q['verification_type'],'hypothetical_literal_equal':value.strip()==ref.strip(),'hypothetical_substring':ref in value,'official_checker_executed':False,'correctness_grade':None})
out.write_text(json.dumps({'status':'offline_replay','scope':'novel schema ambiguity probe, not paper-protocol reproduction','rows':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
