#!/usr/bin/env python3
"""Prepared live pilot. Do not execute until the parent releases the denied action.

Importing this file has no side effects. Offline tests exercise pilot_support,
not this entry point. No local LLM weights or service are used.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

from api_adapter import ChatAPI, ModelAPIError
from pilot_support import (AttemptBudget, ascii_chat_token_bound, guidance,
                           messages, nearest_prior, observation, proposal_context)


def main():
    root = Path(os.environ['PAPER_REPRO_ROOT']).resolve()
    src = Path(__file__).resolve().parents[1] / 'closed_loop'
    auth = json.loads((root / 'results/crop/API_AUTHORIZED.json').read_text())
    # This is the existing outbound authorization boundary, now tied to the
    # actual service/model and approved data/token-counting scope.
    if (auth.get('approved') is not True
            or auth.get('base_url') != os.environ.get('PAPER_LLM_BASE_URL', '').rstrip('/')
            or auth.get('model') != os.environ.get('PAPER_LLM_MODEL')
            or auth.get('payload_scope') != 'crop_public_seven_circuits_summaries_qor'
            or auth.get('input_counting') != 'ascii_byte_upper_bound+256'
            or auth.get('byte_bpe_and_framing_confirmed') is not True):
        raise SystemExit('Endpoint/model/data/token-counting authorization does not match')
    out = root / 'results/crop/live-pilot'
    out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(src))
    import model_contract
    import study
    api = ChatAPI(allow_network=True, token_counter=ascii_chat_token_bound)
    budget = AttemptBudget()
    model = os.environ['PAPER_LLM_MODEL']
    revision = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
    source_commit = subprocess.check_output(['git', '-C', str(src), 'rev-parse', 'HEAD'], text=True).strip()

    def save(path, obj):
        study.dump(out / path, obj)

    def sha(text):
        return hashlib.sha256(text.encode()).hexdigest()

    save('budget.json', dict(frozen_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
         source_commit=source_commit, seed=23, max_api_attempts=34,
         summary_circuits=7, summary_stages=2, attempts_per_stage=2,
         max_proposals=3, max_new_target_eda_measurements=4,
         max_new_prior_measurements=0, max_input_tokens=4096, max_new_tokens=640,
         input_counting='approved ASCII byte-BPE upper bound plus 256 framing tokens',
         decoding='temperature=0; provider determinism not guaranteed',
         api_model=model, minilm_revision=revision,
         objective='LUT4 count * maximum unit LUT depth',
         limitations=['single-module educational circuits', 'model/tool substitutions', 'no paper-quality claim']))
    save('versions.json', dict(python=platform.python_version(), cpu_affinity=sorted(os.sched_getaffinity(0)),
                              model_backend='authorized OpenAI-compatible chat API'))

    def generate(stage, attempt, prompt, required=None):
        record = dict(budget.consume(stage), prompt=prompt, prompt_sha256=sha(prompt))
        path = Path('generations') / (stage + '_' + str(attempt) + '.json')
        save(path, dict(record, status='attempt_reserved_before_transport'))
        try:
            record.update(api.complete(messages(prompt), byte_cap=12000 if required else 18000))
        except ModelAPIError as exc:
            # No retry for HTTP/transport/budget/authorization errors. The
            # request may have reached the provider; retain consumed attempt.
            record.update(exc.evidence)
            save(path, dict(record, status='transport_or_budget_failure', error=str(exc)))
            raise SystemExit('Model request failed; evidence retained; no automatic retry') from None
        try:
            obj = json.loads(record['raw_output'])
            if required is not None:
                model_contract.summary_fields(obj, required)
            record['status'] = 'parsed'
        except (ValueError, TypeError):
            record['status'] = 'invalid_json_or_summary'
            obj = None
        save(path, record)
        return obj, record

    manifest = json.loads((src / 'manifest.json').read_text())
    designs = [d for d in manifest['designs'] if d['role'] == 'prior' or d['id'] == 'fir3']
    caches = {}
    for design in designs:
        source = (src / design['rtl']).read_text()
        if sha(source) != design['sha256']:
            raise SystemExit('RTL source differs from the frozen public manifest')
        records = []
        module = None
        for attempt in range(2):
            prompt = ('Summarize this actual unsigned combinational Verilog module as JSON with EXACT keys '
                      + json.dumps(sorted(model_contract.MODULE_FIELDS))
                      + '. Each value a nonempty concise string, at most 256 characters. State widths, '
                      'arithmetic/truncation, and combinational timing limitations. RTL:\n' + source)
            module, rec = generate(design['id'] + '_module', attempt, prompt, model_contract.MODULE_FIELDS)
            records.append(rec)
            if module is not None:
                break
        if module is None:
            raise SystemExit('Module summary budget exhausted')
        circuit = None
        for attempt in range(2):
            prompt = ('Build a whole-design summary ONLY from the following module summary. There is one '
                      'top module dut, no child instances. Return JSON with EXACT keys '
                      + json.dumps(sorted(model_contract.DESIGN_FIELDS))
                      + '. Each value a nonempty concise string, at most 256 characters. Do not invent '
                      'clocks, physical timing or hierarchy.\nMODULE SUMMARY:\n' + json.dumps(module))
            circuit, rec = generate(design['id'] + '_design', attempt, prompt, model_contract.DESIGN_FIELDS)
            records.append(rec)
            if circuit is not None:
                break
        if circuit is None:
            raise SystemExit('Design summary budget exhausted')
        caches[design['id']] = dict(source_sha256=design['sha256'], modules=[dict(name='dut', summary=module)],
            design_summary=circuit, summary_model=model, summary_model_revision=records[-1]['model'],
            embedding_model='sentence-transformers/all-MiniLM-L6-v2', embedding_model_revision=revision,
            prompt_sha256=study.digest([r['prompt_sha256'] for r in records]),
            embedding_normalization='L2 unit norm', embedding_truncation='max_seq_length=256; input counts recorded',
            generation_provenance=dict(live=True, stages=['RTL module summary', 'design summary from module summary'],
                                       attempts=len(records), seed=23, temperature=0))
        save(Path('summaries') / (design['id'] + '.json'), caches[design['id']])

    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer(str(root / 'assets/shared/all-minilm-l6-v2'),
                                  local_files_only=True, trust_remote_code=False, device='cpu')
    if encoder.max_seq_length != 256:
        raise SystemExit('Unexpected MiniLM truncation limit')
    for name, cache in caches.items():
        text = json.dumps(cache['design_summary'], sort_keys=True)
        cache['embedding'] = encoder.encode(text, normalize_embeddings=True).tolist()
        cache['embedding_input_tokens'] = len(encoder.tokenizer(text)['input_ids'])
        cache['embedding_max_seq_length'] = encoder.max_seq_length
        model_contract.summary_cache(cache, next(d['sha256'] for d in designs if d['id'] == name))
        save(Path('summaries') / (name + '.json'), cache)

    selected, similarities = nearest_prior(caches, designs)
    # Rebuilt prior bank is checked against the actual tool bytes and RTL/config
    # manifest by the offline EDA preparation stage. Do not mix Debian rows in.
    bank = json.loads((root / 'results/crop/native-priors/bank.json').read_text())
    history = bank['history']
    tools = {'yosys': root / 'tools/crop/yosys/yosys', 'abc': root / 'tools/abc-rl/abc/abc'}
    actual_tools = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in tools.items()}
    if (bank['tool_sha256'] != actual_tools or bank['manifest_sha256'] != hashlib.sha256((src / 'manifest.json').read_bytes()).hexdigest()
            or bank['backend_relation'] != 'matched_native_archive'):
        raise SystemExit('Prepared prior bank does not match current tools/manifest')
    prior_guidance = guidance(history, selected, 'matched_native_archive')
    save('retrieval.json', dict(similarities=similarities, selected=selected, guidance=prior_guidance,
                                prior_bank_source_commit=bank['source_commit'], backend_relation='matched_native_archive'))
    exp = out / 'experiment'
    exp.mkdir()
    for directory in ['circuits', 'abc_scripts']:
        shutil.copytree(src / directory, exp / directory)
    target_manifest = dict(manifest, max_measurement_calls=4)
    study.dump(exp / 'manifest.json', target_manifest)
    study.ROOT = exp
    study.YOSYS, study.ABC = tools['yosys'], tools['abc']
    st = study.Study()
    target = st.designs['fir3']
    byconfig = {c['id']: c for c in manifest['configs']}
    archive = [observation(st.measure(target, byconfig['c0'], 'live_model', seed=23, iteration=0))]
    save('target_archive.json', archive)
    for iteration in range(1, 4):
        context = proposal_context(manifest['configs'], selected, prior_guidance, archive,
                                   caches['fir3']['design_summary'], iteration)
        chosen = None
        for attempt in range(2):
            prompt = ('Choose one legal UNTRIED synthesis configuration to minimize the objective. Use '
                      'prior ratios as guidance and actual fresh target observations; explore if uncertain. '
                      'Return exactly {"configuration":{"mode": string,"noalumacc": boolean}}. Do not return id. '
                      'Context:\n' + json.dumps(context))
            response, record = generate('proposal_' + str(iteration), attempt, prompt)
            try:
                chosen = model_contract.proposal(response, context)
            except (ValueError, TypeError, KeyError) as exc:
                save(Path('rejections') / (str(iteration) + '_' + str(attempt) + '.json'),
                     dict(error=str(exc), response=response))
                continue
            save(Path('contexts') / (str(iteration) + '.json'), dict(request=context, response=response, chosen=chosen))
            break
        if chosen is None:
            raise SystemExit('Proposal budget exhausted; no heuristic fallback')
        archive.append(observation(st.measure(target, byconfig[chosen], 'live_model', seed=23,
                                               iteration=iteration, retrieved=selected)))
        save('target_archive.json', archive)
    save('outcome.json', dict(status='completed', new_target_measurements=len(st.rows), api_attempts=budget.total,
         all_validated=True, initial=archive[0]['objective'], best=min(r['objective'] for r in archive),
         configs=[r['config'] for r in archive], selected=selected,
         limits=['single tiny heldout FIR3 and one seed', 'nontrivial hierarchy untested',
                 'API LLM and Yosys/ABC LUT4 substitutions', 'not original implementation, dataset or PPA']))


if __name__ == '__main__':
    main()
