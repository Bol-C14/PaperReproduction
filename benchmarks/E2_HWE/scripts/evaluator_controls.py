"""Offline source-level controls, not hardware tasks or agent scores.

Execute unchanged AST nodes from the pinned release. Only dataclasses-json's
serialization decorator/metadata are no-ops; they are unused by these controls.
No alternate implementation of the parser or report rules is supplied.
"""
import argparse
import ast
import dataclasses
import enum
import hashlib
import json
import pathlib
import subprocess
import tempfile
import typing

p = argparse.ArgumentParser()
p.add_argument('--upstream', type=pathlib.Path, required=True)
p.add_argument('--output', type=pathlib.Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
ns = {**vars(typing), 'dataclass':dataclasses.dataclass,
      'field':dataclasses.field, 'asdict':dataclasses.asdict,
      'dataclass_json':lambda cls:cls, 'config':lambda **kw:{}, 'Enum':enum.Enum}
pins = {}
def load(rel, names, constants=False):
    path = a.upstream/rel
    raw = path.read_bytes()
    pins[rel] = hashlib.sha256(raw).hexdigest()
    tree = ast.parse(raw)
    nodes = [ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]
    nodes += [n for n in tree.body if getattr(n,'name',None) in names or
              (constants and isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id.startswith('_RESULTS_') for t in n.targets))]
    module = ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
    exec(compile(module,str(path),'exec'),ns)
load('hwe_bench/harness/base.py', {'Repository','PullRequestBase','TestStatus','Test','TestResult'})
load('hwe_bench/harness/repos/common.py', {'parse_test_markers','render_finalize_script'},True)
load('hwe_bench/harness/reporting.py', {'Report'})
parse = ns['parse_test_markers']
checks = []
cases = [
 ('f2p', 'TEST: t ... FAIL', 'TEST: t ... PASS', True),
 ('noop_failing', 'TEST: t ... FAIL', 'TEST: t ... FAIL', False),
 ('already_passing', 'TEST: t ... PASS', 'TEST: t ... PASS', False),
 ('bare_pass', 'TEST: t ... FAIL', 'PASS', False),
 ('partial_with_regression','TEST: a ... FAIL\nTEST: b ... PASS','TEST: a ... PASS\nTEST: b ... FAIL',False),
 ('missing_previous_test','TEST: a ... FAIL\nTEST: b ... PASS','TEST: a ... PASS',False),
 ('base_without_results','compiler failed before any result','TEST: t ... PASS',True),
 ('base_skip','TEST: t ... SKIP','TEST: t ... PASS',True),
 ('pass_followed_by_timeout','TEST: t ... FAIL','TEST: t ... PASS\n[TIMEOUT] Container exceeded 1200s and was terminated.',True),
 ('pass_followed_by_crash','TEST: t ... FAIL','TEST: t ... PASS\nSegmentation fault',True),
 ('bracket_suppresses_outer_failure','TEST: a ... FAIL','TEST: crash ... FAIL\nHWE_BENCH_RESULTS_START\nTEST: a ... PASS\nHWE_BENCH_RESULTS_END',True),
]
for label,base,fix,expected in cases:
    report=ns['Report'](org='fixture',repo='fixture',number=0,
        run_result=parse(''),test_patch_result=parse(base),fix_patch_result=parse(fix))
    checks.append({'case':label,'base_log':base,'fix_log':fix,'upstream_valid':report.valid,
                   'expected_observed_semantics':expected,'matched':report.valid==expected,
                   'f2p':sorted(report.f2p_tests),'n2p':sorted(report.n2p_tests),'s2p':sorted(report.s2p_tests)})

def git(cwd,*args):
    return subprocess.run(['git',*args],cwd=cwd,text=True,capture_output=True,check=True).stdout.strip()
with tempfile.TemporaryDirectory(prefix='hwe-history-control-') as tmp:
    repo=pathlib.Path(tmp)/'repo';repo.mkdir()
    git(repo,'init','-q');git(repo,'config','user.name','fixture');git(repo,'config','user.email','fixture@localhost')
    f=repo/'source.txt';f.write_text('synthetic ancestor content\n');git(repo,'add','.');git(repo,'commit','-qm','ancestor fixture')
    ancestor=git(repo,'rev-parse','HEAD')
    f.write_text('synthetic baseline content\n');git(repo,'commit','-qam','baseline fixture')
    base=git(repo,'rev-parse','HEAD')
    f.write_text('synthetic future solution sentinel\n');git(repo,'commit','-qam','future fixture')
    future=git(repo,'rev-parse','HEAD');git(repo,'checkout','-q','--detach',base)
    script=ns['render_finalize_script'](str(repo),str(pathlib.Path(tmp)/'base_commit.txt'))
    run=subprocess.run(['bash','-e','-c',script],text=True,capture_output=True)
    (a.output/'history_finalize.log').write_text(run.stdout+run.stderr)
    reachable=git(repo,'rev-list','HEAD').splitlines()
    future_probe=subprocess.run(['git','cat-file','-e',future],cwd=repo,text=True,capture_output=True)
    hist={'fixture_only':True,'finalizer_returncode':run.returncode,'reachable_count':len(reachable),
          'ancestor_retained':ancestor in reachable,'future_retained':future_probe.returncode==0,
          'remotes':git(repo,'remote'),'interpretation':'The finalizer prunes future unreferenced objects but does not sever current baseline ancestry. Actual image history is uninspected.'}
result={'kind':'source_controls_only','serialization_shim':'identity dataclasses_json decorator; empty serialization metadata; no scoring changes',
        'source_sha256':pins,'scoring_controls':checks,'history_control':hist}
(a.output/'evaluator_controls.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert all(x['matched'] for x in checks)
assert hist['finalizer_returncode']==0 and hist['ancestor_retained'] and not hist['future_retained']
