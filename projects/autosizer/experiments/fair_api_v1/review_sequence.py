"""Generate all five real builder stages + corrections with labeled mock data.
No API, simulator, secrets or download. This is a size audit, not model evidence.
"""
import hashlib
import json
from pathlib import Path
import tempfile
from fair_runtime import AttemptLedger,STAGES,build_messages,check_input,correction_messages,TokenCounterRequired,InputLimitExceeded,CONFIG
from test_runtime import initialized,fresh,CU


def review():
    cases=[]
    with tempfile.TemporaryDirectory() as tmp:
        ledger=AttemptLedger(Path(tmp)/'ledger.json');common=initialized(ledger);rows=[]
        for stage in STAGES:
            if stage=='outer_regeneration':rows=fresh(ledger)
            messages=build_messages(stage,ledger=ledger,common_rows=common,arm_rows=rows,
                                    understanding=None if stage=='circuit_understanding' else CU,
                                    domain=None if stage=='circuit_understanding' else json.loads((Path(__file__).parent/'PLAN.json').read_text())['initial_domain'])
            # Complete raw correction response retained. This length is a fixture,
            # not a conversion of the model's output-token cap to a byte guarantee.
            for variant,request in [('nominal',messages),('one_correction',correction_messages(messages,'SYNTHETIC INVALID RESPONSE '+('x'*1024),'Missing required JSON field'))]:
                encoded=json.dumps(request,ensure_ascii=False).encode()
                checked=check_input(request)
                context=json.loads(messages[1]['content'])['context']
                cases.append({'stage':stage,'variant':variant,'fixture_only':True,
                    'messages_sha256':hashlib.sha256(encoded).hexdigest(),
                    'observation_rows':len(context['history']),
                    'fresh_attempts_used':context['fresh_attempts_used'],
                    'remaining_fresh_attempts':context['remaining_attempts'],
                    'serialized_messages_bytes':len(encoded),'byte_cap':CONFIG['caps']['serialized_messages_bytes'],
                    'conservative_input_upper_bound':checked['input_tokens_upper_bound'],'input_token_cap':CONFIG['caps']['input_chat_tokens_per_request'],
                    'admission':'READY_USING_CONTEXT_ENVELOPE','reason':checked['counter_id'],'truncated':False})
        huge=correction_messages(messages,'x'*CONFIG['caps']['serialized_messages_bytes'],'Oversized full correction')
        try:check_input(huge)
        except InputLimitExceeded:overflow='BLOCKED_WITHOUT_TRUNCATION'
        else:raise AssertionError('Oversized request admitted')
    return {'kind':'Offline sequence audit with synthetic observations and understanding; no model/simulator calls',
            'new_api_calls':0,'new_simulator_calls':0,'secret_reads':0,'requests_reviewed':len(cases),
            'token_status':'Full fixed-model input context ceiling reserved for each request; no exact tokenizer or context truncation required. Actual provider usage reconciles cost.',
            'maximum_reserved_input_tokens_total':CONFIG['caps']['input_chat_tokens_total'],'total_generated_cap':7168,
            'full_correction_overflow':overflow,'cases':cases}

if __name__=='__main__':print(json.dumps(review(),indent=2))
