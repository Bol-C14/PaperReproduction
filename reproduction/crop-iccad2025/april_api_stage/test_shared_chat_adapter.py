"""Mock-only tests against the actual shared code, in disposable private roots.

No real load_config/create_config/private key file/real ledger is accessed.
All pricing values below are synthetic fixtures, NOT current provider prices.
"""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
import urllib.error
from unittest.mock import Mock

from api_adapter import ChatAPI, ModelAPIError
from pilot_support import messages, ascii_chat_token_bound
from shared_chat_adapter import SharedChatAPI, load_shared_api, reservation_usd


class SharedIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.environ.get('CROP_SHARED_MODULE_FOR_TESTS')
        if not path:
            raise unittest.SkipTest('Set CROP_SHARED_MODULE_FOR_TESTS to the shared source, never its private config')
        spec = importlib.util.spec_from_file_location('crop_shared_mock_test_source', path)
        cls.shared = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.shared)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'mock-private-root'
        self.shared.initialize_layout(self.root)
        self.model = 'google/gemini-2.5-flash'
        self.data = dict(base_url='https://openrouter.ai/api/v1', provider='openrouter',
                         api_key='MOCK-NOT-A-CREDENTIAL', chat_model=self.model,
                         batch_id='crop-test-batch', batch_budget_usd='20',
                         max_concurrent_requests=4, max_requests=44, project_max_requests={'crop':34,'autosizer':10}, live_calls_enabled=True,
                         authorized_projects=['crop'], max_output_tokens=640)
        self.config = self.shared.Config(self.data, self.root)
        self.pricing = dict(model=self.model, confirmed_upper_bound=True,
                            input_usd_per_million='1', output_usd_per_million='2',
                            request_fee_usd='0', source='SYNTHETIC TEST FIXTURE ONLY')
        self.calls = []

    def ledger(self):
        return [json.loads(line) for line in (self.root/'usage.jsonl').read_text().splitlines()]

    def response(self, cost='0.0001', finish='stop'):
        usage = dict(prompt_tokens=10, completion_tokens=2, completion_tokens_details={'reasoning_tokens':0})
        if cost is not None:
            usage['cost'] = cost
        return dict(model=self.model, choices=[dict(finish_reason=finish, message={'content':'{}'})], usage=usage)

    def adapter(self, transport=None, allow_network=True):
        def default_transport(endpoint, payload):
            self.calls.append((endpoint, payload))
            return self.response()
        client = self.shared.Client(self.config, _transport=transport or default_transport)
        return SharedChatAPI(client, run_id='crop-offline-fixture', pricing=self.pricing,
                             token_counter=ascii_chat_token_bound, allow_network=allow_network,
                             safe_error_type=self.shared.SafeError)

    def test_disabled_loader_and_legacy_http_do_not_read_private_config(self):
        fake = types.SimpleNamespace(load_config=Mock())
        with self.assertRaises(ModelAPIError):
            load_shared_api('unused', run_id='fixture', pricing=self.pricing,
                            token_counter=ascii_chat_token_bound, _shared_module=fake)
        fake.load_config.assert_not_called()
        with self.assertRaisesRegex(ModelAPIError, 'Direct HTTP is disabled'):
            ChatAPI(True).complete([])
        self.assertFalse((self.root/'openrouter.json').exists())

    def test_shared_live_gate_cannot_be_bypassed(self):
        self.data['live_calls_enabled'] = False
        api = self.adapter()
        with self.assertRaisesRegex(ModelAPIError, 'Live calls are disabled'):
            api.complete(messages('fixture only'))
        self.assertEqual(self.calls, [])
        self.assertEqual(self.ledger(), [])
        self.assertFalse(self.data['live_calls_enabled'])

    def test_shared_project_scope_cannot_be_bypassed(self):
        self.data['authorized_projects'] = ['another-test-project']
        with self.assertRaisesRegex(ModelAPIError, 'not authorized'):
            self.adapter().complete(messages('fixture only'))
        self.assertEqual(self.calls, [])
        self.assertEqual(self.ledger(), [])

    def test_actual_shared_slots_wire_and_metadata_only_ledger(self):
        def transport(endpoint, payload):
            self.calls.append((endpoint, payload))
            busy = 0
            for slot in (self.root/'slots').iterdir():
                fd = os.open(slot, os.O_RDWR)
                try:
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        busy += 1
                    else:
                        fcntl.flock(fd, fcntl.LOCK_UN)
                finally:
                    os.close(fd)
            self.assertEqual(busy, 1)
            self.assertEqual(endpoint, '/chat/completions')
            self.assertEqual(payload['model'], self.model)
            self.assertIs(payload['provider']['allow_fallbacks'], False)
            self.assertEqual(payload['provider']['max_price']['prompt'], 0.3)
            self.assertFalse(payload['stream'])
            self.assertEqual(payload['max_tokens'], 640)
            self.assertNotIn('models', payload)
            return self.response()
        record = self.adapter(transport).complete(messages('DO-NOT-PUT-PROMPT-IN-SHARED-LEDGER'))
        rows = self.ledger()
        self.assertEqual([r['event'] for r in rows], ['reserve','finish'])
        self.assertEqual(rows[0]['accounted_usd'], '0.32')
        self.assertEqual(rows[1]['accounted_usd'], '0.0001')
        self.assertEqual(rows[1]['cost_source'], 'provider_usage')
        self.assertEqual(record['request_model'], self.model)
        self.assertEqual(record['temperature'], 0)
        self.assertEqual(record['reasoning_tokens'], 0)
        self.assertEqual(rows[-1]['tokens']['reasoning_tokens'], 0)
        self.assertEqual(self.calls[0][1]['reasoning'], {'enabled':False})
        self.assertEqual(self.calls[0][1]['temperature'], 0)
        text = json.dumps(rows)
        self.assertNotIn('DO-NOT-PUT-PROMPT', text)
        self.assertNotIn('MOCK-NOT-A-CREDENTIAL', text+json.dumps(record))
        self.assertFalse((self.root/'openrouter.json').exists())

    def test_failed_attempt_is_reserved_once_without_hidden_retry(self):
        def transport(endpoint, payload):
            self.calls.append(1)
            raise urllib.error.HTTPError('https://example.invalid',429,'MOCK-NOT-A-CREDENTIAL',{},None)
        api = self.adapter(transport)
        with self.assertRaises(ModelAPIError) as error:
            api.complete(messages('fixture'))
        self.assertEqual(self.calls, [1])
        self.assertEqual(api.attempts, 1)
        self.assertNotIn('MOCK-NOT-A-CREDENTIAL', str(error.exception))
        rows = self.ledger()
        self.assertEqual(rows[-1]['status'], 'http_error')
        self.assertEqual(rows[-1]['accounted_usd'], rows[0]['accounted_usd'])

    def test_shared_usd_budget_denies_before_second_transport(self):
        self.data['batch_budget_usd'] = '0.32'
        def transport(endpoint, payload):
            self.calls.append(1)
            return self.response(cost=None)
        api = self.adapter(transport)
        api.complete(messages('fixture'))
        with self.assertRaisesRegex(ModelAPIError, 'budget would be exceeded'):
            api.complete(messages('fixture'))
        self.assertEqual(self.calls, [1])
        self.assertEqual(api.attempts, 2)
        self.assertEqual(len(self.ledger()), 2)

    def test_project_total_33_counts_every_shared_attempt(self):
        api = self.adapter()
        for _ in range(33):
            api.complete(messages('fixture'))
        with self.assertRaisesRegex(ModelAPIError, 'attempt cap'):
            api.complete(messages('fixture'))
        self.assertEqual(len(self.calls), 33)
        self.assertEqual(len(self.ledger()), 66)

    def test_shared_global_request_cap_prevents_second_transport(self):
        self.data['max_requests'] = 1
        api = self.adapter()
        api.complete(messages('fixture'))
        with self.assertRaisesRegex(ModelAPIError, 'first-phase request cap'):
            api.complete(messages('fixture'))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(len(self.ledger()), 2)

    def test_shared_reservation_overrun_blocks_following_request(self):
        def transport(endpoint, payload):
            self.calls.append(1)
            return self.response(cost='0.4')
        api = self.adapter(transport)
        with self.assertRaisesRegex(ModelAPIError, 'exceeded caller reservation'):
            api.complete(messages('fixture'))
        with self.assertRaisesRegex(ModelAPIError, 'remains blocked'):
            api.complete(messages('fixture'))
        self.assertEqual(self.calls, [1])
        self.assertEqual(self.ledger()[-1]['status'], 'reservation_exceeded')

    def test_missing_unconfirmed_wrong_or_nonfinite_prices_fail_closed(self):
        self.assertEqual(reservation_usd(self.pricing, self.model), '0.005376000')
        for pricing in (None, dict(self.pricing, model='wrong/model'),
                        dict(self.pricing, confirmed_upper_bound=False),
                        dict(self.pricing, input_usd_per_million='NaN')):
            with self.assertRaises(ModelAPIError):
                reservation_usd(pricing, self.model)
        self.assertEqual(self.calls, [])

    def test_input_estimate_is_not_a_tokenizer_gate(self):
        api = self.adapter()
        api.token_counter = lambda messages: 999999
        record = api.complete(messages('small complete public context'))
        self.assertEqual(record['input_tokens_estimate'], 999999)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1]['messages'], messages('small complete public context'))

    def test_public_chat_only_bridge_needs_no_private_request_method(self):
        calls = []
        config = self.config
        response = self.response()
        class PublicOnly:
            def __init__(self): self.config = config
            def chat(self, chat_messages, *, project, run_id, max_tokens, max_cost_usd, authorize_live, request_options):
                calls.append(request_options)
                return response
        api = SharedChatAPI(PublicOnly(), run_id='fixture', pricing=None, token_counter=None, allow_network=True)
        api.complete(messages('fixture'))
        self.assertEqual(calls[0]['temperature'], 0)
        self.assertEqual(calls[0]['reasoning'], {'enabled':False})

    def test_config_change_stops_instead_of_model_fallback(self):
        api = self.adapter()
        self.data['chat_model'] = 'changed/test-model'
        with self.assertRaisesRegex(ModelAPIError, 'changed'):
            api.complete(messages('fixture'))
        self.assertEqual(self.calls, [])

    def test_invalid_completion_remains_accounted_and_is_not_retried(self):
        def transport(endpoint, payload):
            self.calls.append(1)
            return self.response(finish='length')
        api = self.adapter(transport)
        with self.assertRaises(ModelAPIError) as error:
            api.complete(messages('fixture'))
        self.assertEqual(self.calls, [1])
        self.assertEqual(error.exception.evidence['raw_output'], '{}')
        self.assertEqual(self.ledger()[-1]['accounted_usd'], '0.0001')


if __name__ == '__main__':
    unittest.main()
