"""Regression test: errors.jsonl captures injected layer failures."""
import json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, 'optimizer')
import streaming_oracle as so
from debug_logging import ErrorLogger

legacy_work = Path('optimizer/outputs_haiku_run_legacy_gen1-3/work')
rollout_files = sorted(legacy_work.glob('gen1_ind*/rollouts_gen1_ind*.jsonl'))
rollout_files = [f for f in rollout_files if 'materialized' not in f.name and 'reward' not in f.name]
rollouts_by_ind = []
for rf in rollout_files:
    ind_rollouts = []
    with open(rf) as f:
        for line in f:
            line = line.strip()
            if line:
                try: ind_rollouts.append(json.loads(line))
                except: pass
    rollouts_by_ind.append(ind_rollouts)

print(f'Loaded {sum(len(r) for r in rollouts_by_ind)} rollouts across {len(rollouts_by_ind)} individuals')

# Mock client that fails every 20th call
call_count = [0]
class MockResp:
    def __init__(self, content):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]
        self.usage = SimpleNamespace(prompt_tokens=100, completion_tokens=200, total_tokens=300, completion_tokens_details=SimpleNamespace(reasoning_tokens=50))

class MockCompletions:
    @staticmethod
    def create(model, messages, **kwargs):
        call_count[0] += 1
        if call_count[0] % 20 == 0:
            raise RuntimeError(f'simulated API error at call #{call_count[0]}')
        if call_count[0] % 15 == 0:
            return MockResp('')  # empty response
        sys_msg = messages[0].get('content','') if messages else ''
        if 'refinement protocol' in sys_msg: return MockResp('# mocked\n- [1] mock\n')
        if 'cross-task' in sys_msg.lower(): return MockResp('# synth\n- p1\n')
        return MockResp('# oracle\n## KEEP\n-x\n## ADD\n-y\n## REMOVE\n-z\n## CHANGE\n-w\n')

class MockChat:
    def __init__(self): self.completions = MockCompletions()

class MockClient:
    def __init__(self): self.chat = MockChat()

with tempfile.TemporaryDirectory() as tmp:
    run_dir = Path(tmp)
    gen_dir = run_dir / 'gen1'
    gen_dir.mkdir()
    err_logger = ErrorLogger(run_dir=run_dir, enabled=True)

    result = so.run_generation_oracle(
        gen_dir=gen_dir, generation=1,
        rollouts_by_individual=rollouts_by_ind,
        scoreboard='  t: avg=50%',
        best=0.5, mean=0.4, worst=0.3,
        llm_client=MockClient(), llm_model='mock',
        error_logger=err_logger,
    )
    print(f'Oracle returned: {result and result.name}')
    print(f'Total mock LLM calls: {call_count[0]}')

    errors_file = run_dir / 'errors.jsonl'
    if errors_file.exists():
        errs = [json.loads(l) for l in errors_file.read_text().splitlines() if l.strip()]
        print(f'\nCaptured {len(errs)} events in errors.jsonl:')
        by_sev = {}
        for e in errs:
            by_sev[e['severity']] = by_sev.get(e['severity'], 0) + 1
        print(f'  By severity: {by_sev}')
        print('\n  Sample entries:')
        for e in errs[:4]:
            sev = e.get('severity','?')
            phase = e.get('phase','?')
            if 'exception_type' in e:
                print(f'    [{sev}] {phase} — {e["exception_type"]}: {e["exception_msg"][:50]}')
                ctx = e.get('context',{})
                print(f'           context: {ctx}')
            else:
                print(f'    [{sev}] {phase} — {e.get("message","")[:60]}')
        assert len(errs) >= 3, f'Expected at least 3 error events, got {len(errs)}'
        print('\n[OK] errors.jsonl captures both exceptions (severity=warning) and empty-response events (severity=info)')
    else:
        print('[FAIL] errors.jsonl was not created')
        sys.exit(1)
