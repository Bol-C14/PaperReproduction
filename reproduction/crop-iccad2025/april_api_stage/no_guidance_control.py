#!/usr/bin/env python3
"""One cached-summary no-guidance control. Main runs only when explicitly invoked."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from api_adapter import ModelAPIError
from pilot_support import AttemptBudget, ascii_chat_token_bound, messages, observation, proposal_context
from shared_chat_adapter import load_shared_api

PROMPT_PREFIX = ('Choose one legal UNTRIED synthesis configuration to minimize the objective. Use '
                 'prior ratios as guidance and actual fresh target observations; explore if uncertain. '
                 'Return exactly {"configuration":{"mode": string,"noalumacc": boolean}}. Do not return id. '
                 'Context:\n')


def control_context(configs, archive, design_summary, iteration):
    # Keep the original context shape/arm label and prompt. Only these two
    # retrieval fields are ablated; subsequent target histories evolve normally.
    return proposal_context(configs, None, [], archive, design_summary, iteration)


def main():
    root = Path(os.environ['PAPER_REPRO_ROOT']).resolve()
    src = Path(__file__).resolve().parents[1] / 'closed_loop'
    sys.path.insert(0, str(src))
    import study
    import model_contract
    original = root / 'results/crop/live-pilot'
    original_budget = json.loads((original/'budget.json').read_text())
    auth = json.loads((root/'results/crop/API_AUTHORIZED.json').read_text())
    if auth.get('approved') is not True or auth.get('payload_scope') != 'crop_public_seven_circuits_summaries_qor':
        raise SystemExit('Existing public CROP scope not authorized')
    out = root / 'results/crop/no-guidance-control-20261028'
    out.mkdir(parents=True, exist_ok=False)
    source_sha = subprocess.check_output(['git','-C',str(src),'rev-parse','HEAD'],text=True).strip()
    api = load_shared_api(root/'tools/shared/openrouter_shared.py',
                          run_id='crop-no-guidance-'+source_sha[:8], pricing=None,
                          token_counter=ascii_chat_token_bound, allow_network=True, max_attempts=6)
    if api.model != original_budget['api_model'] or api.model != 'google/gemini-2.5-flash':
        raise SystemExit('Shared model differs from the original pilot')
    manifest = json.loads((src/'manifest.json').read_text())
    cache = json.loads((original/'summaries/fir3.json').read_text())
    target = next(d for d in manifest['designs'] if d['id']=='fir3')
    model_contract.summary_cache(cache, target['sha256'])
    bank = json.loads((root/'results/crop/native-priors/bank.json').read_text())
    tools = {'yosys':root/'tools/crop/yosys/yosys','abc':root/'tools/abc-rl/abc/abc'}
    if {k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in tools.items()} != bank['tool_sha256']:
        raise SystemExit('Native tool bytes changed')
    if bank['manifest_sha256'] != hashlib.sha256((src/'manifest.json').read_bytes()).hexdigest():
        raise SystemExit('Source/config manifest changed')
    if hashlib.sha256((src/target['rtl']).read_bytes()).hexdigest() != target['sha256']:
        raise SystemExit('FIR3 source changed')
    retrieval = json.loads((original/'retrieval.json').read_text())
    original_first = json.loads((original/'contexts/1.json').read_text())['request']
    original_prompt = json.loads((original/'generations/proposal_1_0.json').read_text())['prompt']
    if original_prompt != PROMPT_PREFIX+json.dumps(original_first):
        raise SystemExit('Proposal prompt is not identical to original source')
    study.dump(out/'protocol.json', dict(source_commit=source_sha, original_source_commit=original_budget['source_commit'],
        frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()), arm='no_guidance', seed=23,
        model=api.model, temperature=0, reasoning_enabled=False, max_output_tokens=640,
        max_actual_api_attempts=6, nominal_api_attempts=3, cumulative_project_remaining_before=16,
        per_request_reservation_usd='0.32', maximum_unknown_cost_reservations_usd='1.92',
        cumulative_shared_api_stage_limit_usd='10.00', no_credential_or_policy_changes=True,
        baseline_config='c0', fresh_baseline_calls=1, subsequent_measurement_budget=3,
        max_synthesis_attempts=4, correctness_vectors_each=256, correctness_seed=701,
        tool_sha256=bank['tool_sha256'], summary_reused=True, new_summary_embedding_calls=0,
        design_summary_cache_sha256=hashlib.sha256((original/'summaries/fir3.json').read_bytes()).hexdigest(),
        shared_module_sha256=getattr(api,'shared_module_sha256',None),
        comparison='Earlier guided trajectory versus later no-guidance run; one seed, not strictly paired',
        intervention=['retrieved_prior=null','retrieved_guidance=[]'],
        fairness_limits=['Shared cached preprocessing; compare search-only cost, not whole-pipeline cost',
                         'Fresh run in later time window; model ID is not immutable weights/provider identity',
                         'Public shared interface adds standard-tier price/parameter safety routing constraints']))
    exp = out/'experiment';exp.mkdir()
    for directory in ('circuits','abc_scripts'):shutil.copytree(src/directory,exp/directory)
    study.dump(exp/'manifest.json',dict(manifest,max_measurement_calls=4))
    study.ROOT,study.YOSYS,study.ABC=exp,tools['yosys'],tools['abc']
    st=study.Study();byconfig={c['id']:c for c in manifest['configs']}
    baseline=st.measure(target,byconfig['c0'],'no_guidance',seed=23,iteration=0)
    archive=[observation(baseline)]
    study.dump(out/'target_archive.json',archive)
    guided_first=proposal_context(manifest['configs'],retrieval['selected'],retrieval['guidance'],archive,cache['design_summary'],1)
    if guided_first != original_first:
        raise SystemExit('Fresh baseline/context differs from original; no model call allowed')
    budget=AttemptBudget(max_total=6)
    for iteration in range(1,4):
        context=control_context(manifest['configs'],archive,cache['design_summary'],iteration)
        chosen=None
        for attempt in range(2):
            record=dict(budget.consume('proposal_'+str(iteration)),prompt=PROMPT_PREFIX+json.dumps(context))
            path=out/'generations'/f'proposal_{iteration}_{attempt}.json'
            study.dump(path,dict(record,status='reserved_before_shared_call'))
            try:
                record.update(api.complete(messages(record['prompt'])))
            except ModelAPIError as exc:
                record.update(exc.evidence);record.update(status='shared_or_completion_failure',error=str(exc))
                study.dump(path,record)
                raise SystemExit('Shared call failed; no automatic retry') from None
            try:
                response=json.loads(record['raw_output'])
                chosen=model_contract.proposal(response,context)
                record['status']='accepted'
            except (ValueError,TypeError,KeyError) as exc:
                record.update(status='content_rejected',error=str(exc));context['last_rejection']=str(exc)
                study.dump(path,record)
                continue
            study.dump(path,record)
            study.dump(out/'contexts'/f'{iteration}.json',dict(request=context,response=response,chosen=chosen))
            print('PROPOSAL',iteration,attempt,chosen,record.get('usage'),flush=True)
            break
        if chosen is None:raise SystemExit('Two content attempts exhausted; no heuristic fallback')
        archive.append(observation(st.measure(target,byconfig[chosen],'no_guidance',seed=23,iteration=iteration)))
        study.dump(out/'target_archive.json',archive)
    study.dump(out/'outcome.json',dict(status='completed',arm='no_guidance',seed=23,
        api_attempts=budget.total,new_target_measurements=len(st.rows),all_validated=True,
        initial=archive[0]['objective'],best=min(r['objective'] for r in archive),
        configs=[r['config'] for r in archive],retrieved_prior=None,retrieved_guidance=[],
        limits=['single-seed later no-guidance run; earlier guided run is not strict paired evidence',
                'cached preprocessing reused; no end-to-end cost advantage claim']))


if __name__=='__main__':
    main()
