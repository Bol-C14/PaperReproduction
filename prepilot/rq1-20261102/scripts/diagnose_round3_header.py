"""Read-only diagnostic of the frozen gate failure, not an eligibility override."""
from pathlib import Path
import difflib,hashlib,json
P=Path(__file__).resolve().parents[1];R=P/'logs/physical-only-round3';D=R/'A1_noop'
a=(D/'before_funcsim.v').read_text();b=(D/'after_funcsim.v').read_text()
# Compare exact entire remaining file after a confirmed comment-only preamble.
def split(s):
 lines=s.splitlines(keepends=True);i=next(i for i,x in enumerate(lines) if x.strip() and not x.lstrip().startswith('//'))
 assert all(x.lstrip().startswith('//') or not x.strip() for x in lines[:i])
 return ''.join(lines[:i]),''.join(lines[i:])
ah,ab=split(a);bh,bb=split(b)
assert ab==bb,'actual body changes need another audit'
changed=[x for x in difflib.ndiff(ah.splitlines(),bh.splitlines()) if x.startswith(('- ','+ '))]
assert all(x[2:].startswith(('// Date        :','//               /workspace/work/rq1-prepilot-20261102/physical-only-round3/A1_noop/')) for x in changed)
result={'status':'frozen_gate_failed_do_not_override','source_of_failure':'generated_Command_comment_wrapped_into_path_continuation_not_removed_by_frozen_canonicalizer','actual_semantic_body_difference_found':False,'whole_body_after_comment_only_preamble_identical':ab==bb,'body_sha256':[hashlib.sha256(x.encode()).hexdigest() for x in (ab,bb)],'changed_comment_lines':changed,'eligibility_reclassified':False,'B_run':False,'new_EDA_processes_for_diagnosis':0}
(P/'ROUND3_HEADER_DIAGNOSTIC.json').write_text(json.dumps(result,indent=2)+'\n')
(P/'ROUND3_EXPORT_DIFF.txt').write_text(''.join(difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),fromfile='before_funcsim.v',tofile='after_funcsim.v')))
print(json.dumps(result,indent=2))
