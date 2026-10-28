"""Frozen eight-control evaluator-contract pilot. No model, network or training."""
import ast
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

SRC = Path('/src')
OUT = Path('/work')
START = time.monotonic()
ATTEMPTS = []
CASES = json.loads((SRC / 'fixtures.json').read_text())

def call(argv, path, timeout=150, env=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    entry = dict(argv=argv, timeout_seconds=timeout, attempt=len(ATTEMPTS) + 1)
    try:
        p = subprocess.run(argv, cwd=path.parent, env=env, capture_output=True,
                           text=True, timeout=timeout)
        path.with_suffix('.stdout.log').write_text(p.stdout)
        path.with_suffix('.stderr.log').write_text(p.stderr)
        entry.update(returncode=p.returncode, status='completed')
        return p
    except subprocess.TimeoutExpired as exc:
        entry.update(returncode=None, status='timeout')
        for suffix, text in [('stdout', exc.stdout), ('stderr', exc.stderr)]:
            path.with_suffix(f'.{suffix}.log').write_text(
                text.decode(errors='replace') if isinstance(text, bytes) else text or '')
        return None
    finally:
        entry['wall_seconds'] = time.monotonic() - start
        ATTEMPTS.append(entry)
        (OUT / 'attempts.json').write_text(json.dumps(ATTEMPTS, indent=2))

def official(case, directory):
    directory.mkdir(parents=True)
    fixture = SRC / 'fixtures' / case['id']
    row = dict(full_response=(fixture / 'candidate.v').read_text(),
               ground_truth=(fixture / 'gold.v').read_text())
    (directory / 'responses.jsonl').write_text(json.dumps(row) + '\n')
    (directory / 'benchmark.jsonl').write_text(json.dumps(row) + '\n')
    # Upstream sources this file; only add the installed official Yosys binary to PATH.
    (directory / 'yosys.env').write_text('export PATH=/opt/yosys/bin:$PATH\n')
    env = dict(os.environ, P07_ORIGINAL_LOGDIR=str(directory))
    p = call([sys.executable, '/src/original_driver.py',
              '--results_path', str(directory / 'responses.jsonl'),
              '--samples_per_question', '1', '--yosys_location', str(directory / 'yosys.env'),
              '--benchmark_path', str(directory / 'benchmark.jsonl')],
             directory / 'driver', timeout=400, env=env)
    result_file = directory / 'responses_evaluation.jsonl'
    if p is None or p.returncode or not result_file.exists():
        return dict(status='unknown', reason='upstream_driver_failure')
    rows = [json.loads(s) for s in result_file.read_text().splitlines()]
    if len(rows) != 1:
        return dict(status='unknown', reason='unexpected_row_count', count=len(rows))
    return dict(status='pass' if rows[0]['success'] else 'fail', **rows[0])

def rename_from_upstream(code):
    # Port reuses only this exact upstream function; no upstream top-level execution.
    module = ast.parse((SRC / 'upstream/evaluation_script.py').read_text())
    target = [n for n in module.body if isinstance(n, ast.FunctionDef)
              and n.name == 'rename_modules_and_instantiations']
    import re
    namespace = {'re': re}
    exec(compile(ast.Module(body=target, type_ignores=[]), '<upstream-rename>', 'exec'), namespace)
    return namespace['rename_modules_and_instantiations'](code)

def port(case, directory, bound=50):
    directory.mkdir(parents=True)
    fixture = SRC / 'fixtures' / case['id']
    code, names = rename_from_upstream((fixture / 'gold.v').read_text())
    (directory / 'gold.v').write_text(code)
    (directory / 'candidate.v').write_text((fixture / 'candidate.v').read_text())
    codes = []
    statuses = []
    for original, renamed in names.items():
        script = ('read_verilog gold.v\nread_verilog candidate.v\n'
                  'prep; proc; opt; memory;\nclk2fflogic;\n'
                  f'miter -equiv -flatten {renamed} {original} miter\n'
                  f'sat -seq {bound} -verify -prove trigger 0 -show-all '
                  '-show-inputs -show-outputs -set-init-zero miter\n')
        script_file = directory / f'{original}.ys'
        script_file.write_text(script)
        p = call(['yosys', '-s', str(script_file)], directory / original)
        codes.append(-1 if p is None else p.returncode)
        statuses.append('timeout' if p is None else 'completed')
    return dict(status='pass' if all(c == 0 for c in codes) else 'fail',
                returncodes=codes, checks=len(codes), subprocess_statuses=statuses,
                guarded_status='invalid' if not codes else
                ('unknown' if 'timeout' in statuses else ('pass' if all(c == 0 for c in codes) else 'fail')),
                bound=bound)

def oracle(case, directory):
    directory.mkdir(parents=True)
    fixture = SRC / 'fixtures' / case['id']
    if case['kind'] == 'invalid':
        results = []
        for role in ['gold', 'candidate']:
            p = call(['iverilog', '-g2012', '-s', 'top', '-o', str(directory / (role+'.vvp')),
                      str(fixture / (role+'.v'))], directory / role, timeout=20)
            results.append(None if p is None else p.returncode)
        return dict(status='invalid_candidate' if results[0] == 0 and results[1] not in (0, None)
                    else 'unknown', syntax_returncodes=results)
    # Reviewed, narrowly applicable renaming for authored fixtures; independent of upstream regex.
    gold = (fixture / 'gold.v').read_text().replace('module top(', 'module gold_top(')
    cand = (fixture / 'candidate.v').read_text().replace('module top(', 'module cand_top(')
    source = gold + '\n' + cand
    if case['kind'] == 'comb':
        tb = '''module tb;
reg a,b; wire gy,cy; integer i;
gold_top g(a,b,gy); cand_top c(a,b,cy);
initial begin
 for(i=0;i<4;i=i+1) begin {a,b}=i; #1; $display("OBS %0d %0d %0d",i,gy,cy); end
 $finish; end endmodule'''
        expected = []
        for i in range(4):
            a,b=(i>>1)&1,i&1
            model=case['model']
            g = int(not(a and b)) if model=='nand' else ((a^b) if model=='xor' else (a&b))
            c = int((not a) or (not b)) if model=='nand' else ((a and not b) or (not a and b)) if model=='xor' else (a|b)
            expected.append([i,int(g),int(c)])
        proof = 'exhaustive four valuations of both Boolean inputs'
    else:
        width=case['width']; delayed=case['model']=='delayed'
        outputs = 'wire gy,cy;' if delayed else f'wire [{width-1}:0] gy,cy;'
        init = 'g.count=0; c.count=0;' if delayed else 'g.q=0; c.q=0;'
        tb = f'''module tb;
reg clk; {outputs} integer i;
gold_top g(clk,gy); cand_top c(clk,cy);
initial begin clk=0; {init} #1;
 $display("OBS %0d %0d %0d",0,gy,cy);
 for(i=1;i<=260;i=i+1) begin #1; clk=1; #1;
 $display("OBS %0d %0d %0d",i,gy,cy); #1; clk=0; end
 $finish; end endmodule'''
        expected=[]
        mask=(1<<width)-1
        for edge in range(261):
            if delayed: g,c=int((edge&mask)==60),0
            else: g,c=edge&mask,((edge*2)&mask if case['model']=='increment_two' else (edge*(-15))&mask)
            expected.append([edge,g,c])
        # Joint-state reachability until repetition: no data inputs, deterministic counters.
        seen=set(); joint=(0,0); steps=0; first_bad=None
        while joint not in seen:
            seen.add(joint)
            g,c=(int(joint[0]==60),0) if delayed else joint
            if g!=c and first_bad is None: first_bad=steps
            delta=2 if case['model']=='increment_two' else (-15 if case['model']=='increment_subtract' else 1)
            joint=((joint[0]+1)&mask,(joint[1]+delta)&mask); steps+=1
        proof=f'exhaustive deterministic joint-state orbit from zero: {len(seen)} states; clock stuttering leaves state unchanged'
    design=directory/'oracle.v'; design.write_text(source+'\n'+tb+'\n')
    binary=directory/'oracle.vvp'
    compile_result=call(['iverilog','-g2012','-s','tb','-o',str(binary),str(design)],directory/'compile',20)
    if compile_result is None or compile_result.returncode:
        return dict(status='unknown',reason='oracle_compile_failed')
    p=call(['vvp',str(binary)],directory/'simulate',20)
    if p is None or p.returncode: return dict(status='unknown',reason='oracle_simulation_failed')
    observations=[list(map(int,line.split()[1:])) for line in p.stdout.splitlines() if line.startswith('OBS ')]
    if observations!=expected:
        return dict(status='unknown',reason='independent_model_disagrees_with_RTL_simulation',observations=observations,expected=expected)
    mismatches=[row for row in observations if row[1]!=row[2]]
    return dict(status='non_equivalent' if mismatches else 'equivalent_under_reviewed_contract',
                first_witness=mismatches[0] if mismatches else None,
                observations=len(observations), proof=proof, simulation_model_agreement=True)

def main():
    OUT.mkdir(exist_ok=True)
    (OUT/'started.json').write_text(json.dumps(dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(), protocol_sha256=hashlib.sha256((SRC/'PROTOCOL.md').read_bytes()).hexdigest()),indent=2))
    rows=[]
    for case in CASES:
        print('START',case['id'],flush=True)
        path=OUT/case['id']
        row=dict(id=case['id'],frozen_prediction=case['predicted_official'],independent_truth=case['independent_truth'])
        row['original']=official(case,path/'original')
        row['port']=port(case,path/'port')
        row['oracle']=oracle(case,path/'oracle')
        row['original_port_agreement']=row['original']['status']==row['port']['status']
        if case['id']=='delayed_pulse': row['novel_bound160']=port(case,path/'novel_bound160',160)
        rows.append(row)
        (OUT/'results.json').write_text(json.dumps(rows,indent=2))
        print(json.dumps(row),flush=True)
    usage=resource.getrusage(resource.RUSAGE_CHILDREN)
    summary=dict(cases=len(rows),original_port_agreements=sum(r['original_port_agreement'] for r in rows),
                 original_predictions_matched=sum(r['original']['status']==r['frozen_prediction'] for r in rows),
                 unknown_original=sum(r['original']['status']=='unknown' for r in rows),
                 unknown_oracles=sum(r['oracle']['status']=='unknown' for r in rows),
                 outer_subprocess_attempts=len(ATTEMPTS),outer_timeouts=sum(x['status']=='timeout' for x in ATTEMPTS),
                 experiment_wall_seconds=time.monotonic()-START,children_user_seconds=usage.ru_utime,
                 children_system_seconds=usage.ru_stime,children_maxrss_kib=usage.ru_maxrss,
                 completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (OUT/'metrics.json').write_text(json.dumps(summary,indent=2)); print(json.dumps(summary),flush=True)

if __name__=='__main__': main()
