"""Explicit fake-model/offline tests; never import or execute the live entry point."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'closed_loop'))
import model_contract
import study
from pilot_support import (AttemptBudget, ascii_chat_token_bound, guidance, messages,
                           nearest_prior, observation, proposal_context)


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((HERE.parent / 'closed_loop/manifest.json').read_text())
        self.history = json.loads((HERE.parent / 'closed_loop/history.json').read_text())
        self.designs = [d for d in self.manifest['designs'] if d['role'] == 'prior' or d['id'] == 'fir3']
        self.vector = [1.0] + [0.0] * 383

    def test_prompt_guard_accepts_saved_key_sorting_but_not_changed_data(self):
        from no_guidance_control import validate_original_prompt, PROMPT_PREFIX
        actual = {'z': 1, 'a': 2}
        saved = json.loads(json.dumps(actual, sort_keys=True))
        self.assertEqual(validate_original_prompt(PROMPT_PREFIX+json.dumps(actual), saved), actual)
        with self.assertRaises(ValueError):
            validate_original_prompt(PROMPT_PREFIX+json.dumps(actual), {'z': 3, 'a': 2})

    def test_no_guidance_template_preserves_nested_original_serialization(self):
        from no_guidance_control import control_context
        template = {'legal_configs':[{'mode':'fast','id':'c0','noalumacc':False}],
                    'design_summary':{'z':'last','a':'first'}, 'iteration':1,
                    'target_history':[{'status':'ok','config':'c0','objective':1,'invocation':1}],
                    'retrieved_guidance':[{'normalized_objective':1,'config':'c0'}], 'retrieved_prior':'prior'}
        sorted_configs = json.loads(json.dumps(template['legal_configs'], sort_keys=True))
        sorted_summary = json.loads(json.dumps(template['design_summary'], sort_keys=True))
        history = [{'config':'c0','objective':1,'status':'ok','invocation':1}]
        context = control_context(sorted_configs, history, sorted_summary, 1, template=template)
        restored = copy.deepcopy(context)
        for key in ('retrieved_prior','retrieved_guidance'): restored[key] = template[key]
        self.assertEqual(json.dumps(restored), json.dumps(template))

    def test_no_guidance_intervention_changes_only_two_context_fields(self):
        from no_guidance_control import control_context
        old = json.loads((HERE/'real_pilot_reviewed_subset/contexts/1.json').read_text())['request']
        fresh = control_context(old['legal_configs'], old['target_history'], old['design_summary'], old['iteration'])
        self.assertEqual(set(fresh), set(old))
        self.assertEqual({k for k in old if old[k] != fresh[k]}, {'retrieved_prior','retrieved_guidance'})
        self.assertIsNone(fresh['retrieved_prior'])
        self.assertEqual(fresh['retrieved_guidance'], [])

    def test_summary_rejects_nontext_empty_and_long_values(self):
        summary = {f: 'explicit test fixture only' for f in model_contract.MODULE_FIELDS}
        self.assertEqual(model_contract.summary_fields(summary, model_contract.MODULE_FIELDS), summary)
        for value in (None, 1, {}, '', 'x' * 257):
            bad = dict(summary, inputs=value)
            with self.assertRaises(ValueError):
                model_contract.summary_fields(bad, model_contract.MODULE_FIELDS)

    def test_explicit_fake_cache_roundtrip_and_source_mismatch(self):
        cache = dict(source_sha256='test-source-not-an-RTL-hash',
                     modules=[dict(name='dut', summary={f: 'test fixture only' for f in model_contract.MODULE_FIELDS})],
                     design_summary={f: 'test fixture only' for f in model_contract.DESIGN_FIELDS},
                     embedding=list(self.vector), summary_model='FAKE-not-a-model-result',
                     summary_model_revision='test', embedding_model='FAKE-not-an-embedding-result',
                     embedding_model_revision='test', prompt_sha256='test', embedding_normalization='L2',
                     embedding_truncation='test-only', generation_provenance={'live': False, 'test_only': True})
        self.assertEqual(model_contract.summary_cache(cache, cache['source_sha256']), self.vector)
        with self.assertRaisesRegex(ValueError, 'different source'):
            model_contract.summary_cache(cache, 'other-source')
        cache['embedding'][0] = 2.0
        with self.assertRaisesRegex(ValueError, 'unit norm'):
            model_contract.summary_cache(cache, cache['source_sha256'])

    def test_retrieval_rejects_scale_bias_nonfinite_and_family_leakage(self):
        caches = {d['id']: {'embedding': list(self.vector)} for d in self.designs}
        selected, ranked = nearest_prior(caches, self.designs)
        self.assertEqual(selected, 'alu')  # deterministic alphabetical tie break
        self.assertNotIn('fir3', [p for _, p in ranked])
        for value in (2.0, float('nan'), True):
            bad = copy.deepcopy(caches)
            bad['alu']['embedding'][0] = value
            with self.assertRaises(ValueError):
                nearest_prior(bad, self.designs)
        bad = copy.deepcopy(self.designs)
        bad[0]['family'] = 'fir3'
        with self.assertRaises(ValueError):
            nearest_prior(caches, bad)

    def test_prior_guidance_is_sorted_normalized_and_backend_labeled(self):
        hist = copy.deepcopy(self.history)
        hist['alu'].reverse()
        items = guidance(hist, 'alu', 'cross_backend_archival_guidance')
        expected = sorted(hist['alu'], key=lambda r: (r['objective'], r['config']))[:3]
        self.assertEqual([r['config'] for r in items], [r['config'] for r in expected])
        self.assertTrue(all('objective' not in r for r in items))
        hist['alu'][0]['status'] = 'failed'
        with self.assertRaises(ValueError):
            guidance(hist, 'alu', 'matched_native_archive')

    def test_global_attempt_cap_and_per_stage_invalid_attempts(self):
        budget = AttemptBudget()
        for stage in range(17):
            for _ in range(2):
                budget.consume(str(stage))
        self.assertEqual(budget.total, 34)
        with self.assertRaises(ValueError):
            budget.consume('extra')
        budget = AttemptBudget()
        budget.consume('malformed_json')
        budget.consume('malformed_json')
        with self.assertRaises(ValueError):
            budget.consume('malformed_json')

    def test_fake_proposal_feedback_rejects_duplicate_and_extra_keys(self):
        # Deliberately scripted fake; this is not a model result or measured QoR.
        archive = [{'config': 'c0', 'objective': 999, 'status': 'ok', 'invocation': 1}]
        context = proposal_context(self.manifest['configs'], 'alu', [], archive,
                                   {'test_only': 'not a generated summary'}, 1)
        reply = {'configuration': {'mode': 'quality', 'noalumacc': False}}
        self.assertEqual(model_contract.proposal(reply, context), 'c1')
        for bad in ({'configuration': {'mode': 'fast', 'noalumacc': False}},
                    dict(reply, explanation='extra'),
                    {'configuration': {'mode': 'quality', 'noalumacc': 0}}):
            with self.assertRaises(ValueError):
                model_contract.proposal(bad, context)
        archive.append({'config': 'c1', 'objective': 888, 'status': 'ok', 'invocation': 2})
        self.assertEqual(len(context['target_history']), 1)
        with self.assertRaises(ValueError):
            proposal_context(self.manifest['configs'], 'alu', [], archive, {}, 1)

    def test_observation_requires_both_checks_and_correct_product(self):
        row = copy.deepcopy(self.history['alu'][0])
        self.assertEqual(observation(row)['objective'], row['objective'])
        for key, value in [('formal', 'CEC failed'), ('independent', 'failed'),
                           ('objective', float('nan')), ('objective', 1), ('vectors_checked', 0)]:
            bad = dict(row, **{key: value})
            with self.assertRaises(ValueError):
                observation(bad)

    def test_ascii_token_bound_rejects_unsupported_text(self):
        self.assertEqual(ascii_chat_token_bound(messages('public RTL')),
                         256 + len('systemuser') + len(messages('public RTL')[0]['content']) + len('public RTL'))
        with self.assertRaises(UnicodeEncodeError):
            ascii_chat_token_bound(messages('\u4e2d'))

    def test_synthesis_explicitly_pins_mapping_abc_and_cec_failure_stops(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'manifest.json').write_text(json.dumps(self.manifest))
            def fake_command(argv, logfile, timeout):
                logfile.write_text('Networks are NOT EQUIVALENT')
                if logfile.name == 'yosys.log':
                    (logfile.parent / 'mapped.json').write_text('{}')
                return 0, 0.0
            with patch.object(study, 'ROOT', root), patch.object(study, 'ABC', Path('/test/explicit-abc')), patch.object(study, 'command', fake_command):
                st = study.Study()
                row = st.measure(st.designs['alu'], self.manifest['configs'][0], 'fake_tool_test')
                self.assertEqual(row['status'], 'failed')
                self.assertIsNone(row['objective'])
                flow = (root / row['folder'] / 'flow.ys').read_text()
                self.assertIn('abc -exe /test/explicit-abc -fast -lut 4', flow)
                self.assertEqual(len(st.rows), 1)

    def test_tool_timeout_terminates_owned_grandchild(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'grandchild-survived.txt'
            child = 'import time;from pathlib import Path;time.sleep(0.5);Path(' + repr(str(marker)) + ').write_text("survived")'
            parent = 'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",' + repr(child) + ']);time.sleep(60)'
            with patch.object(study, 'ROOT', root):
                code, _ = study.command([sys.executable, '-c', parent], root / 'timeout.log', 0.2)
            self.assertEqual(code, 124)
            time.sleep(0.6)
            self.assertFalse(marker.exists(), 'Timed-out tool left an active descendant')


if __name__ == '__main__':
    unittest.main()
