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
                try:check_input(request)
                except (TokenCounterRequired,InputLimitExceeded) as error:
                    blocked=type(error).__name__
                else:raise AssertionError('Missing tokenizer must block')
                context=json.loads(messages[1]['content'])['context']
                cases.append({'stage':stage,'variant':variant,'fixture_only':True,
                    'messages_sha256':hashlib.sha256(encoded).hexdigest(),
                    'observation_rows':len(context['history']),
                    'fresh_attempts_used':context['fresh_attempts_used'],
                    'remaining_fresh_attempts':context['remaining_attempts'],
                    'serialized_messages_bytes':len(encoded),'byte_cap':24576,
                    'certified_token_upper_bound':None,'input_token_cap':8192,
                    'admission':'BLOCKED','reason':blocked,'truncated':False})
        huge=correction_messages(messages,'x'*24576,'Oversized full correction')
        try:check_input(huge)
        except InputLimitExceeded:overflow='BLOCKED_WITHOUT_TRUNCATION'
        else:raise AssertionError('Oversized request admitted')
    return {'kind':'Offline sequence audit with synthetic observations and understanding; no model/simulator calls',
            'new_api_calls':0,'new_simulator_calls':0,'secret_reads':0,'requests_reviewed':len(cases),
            'token_status':'Every sequence request blocks without a certified model-specific chat token upper-bound counter. No exact Gemini fit claimed.',
            'maximum_reserved_input_tokens_total':81920,'total_generated_cap':7168,
            'full_correction_overflow':overflow,'cases':cases}

if __name__=='__main__':print(json.dumps(review(),indent=2))
