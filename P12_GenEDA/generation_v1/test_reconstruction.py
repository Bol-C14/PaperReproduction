"""Tests of the new decoder port; do not confuse these with original GenEDA tests."""
import json
from pathlib import Path
import unittest

import numpy as np
import torch

import run_generation as g
import evaluate as e


class PortTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        self.decoder = g.Decoder().eval()

    def test_cached_autoregression_matches_full_prefix(self):
        ids = torch.tensor([[g.BOS, 21, 31, g.GRAPH, 41, 42]])
        graph = torch.randn(1, g.D)
        with torch.no_grad():
            full = self.decoder(ids, graph)[0]
            _, cache = self.decoder(ids[:, :4], graph)
            for i in range(4, 6):
                step, cache = self.decoder(ids[:, i:i+1], graph, cache)
                torch.testing.assert_close(step[:, 0], full[:, i], atol=2e-5, rtol=2e-5)

    def test_future_answer_cannot_leak_to_earlier_logits(self):
        first = torch.tensor([[g.BOS, 20, 30, 40]])
        second = first.clone(); second[:, -1] = 50
        with torch.no_grad():
            a, b = self.decoder(first)[0], self.decoder(second)[0]
        torch.testing.assert_close(a[:, :-1], b[:, :-1])

    def test_answer_only_loss_mask_and_byte_roundtrip(self):
        row = {'prompt': 'prompt', 'answer': 'real answer', 'graph': [0.] * 768}
        ids, labels, _ = g.batch([row], [0])
        pos = (ids[0] == g.GRAPH).nonzero()[0].item()
        self.assertTrue((labels[0, :pos] == -100).all())
        self.assertEqual(labels[0, pos].item(), ord('r') + 4)
        self.assertEqual(bytes(x-4 for x in g.byte_ids(row['answer'], 512)).decode(), row['answer'])

    def test_stage_freezing_and_adapter_gradients(self):
        self.decoder.setup('lora')
        logits = self.decoder(torch.tensor([[g.BOS, 20, 30]]))[0]
        logits.square().mean().backward()
        self.assertIsNone(self.decoder.tokens.weight.grad)
        for module in self.decoder.modules():
            if isinstance(module, g.LoRALinear):
                self.assertIsNotNone(module.b.grad)
                self.assertIsNone(module.base.weight.grad)

    def test_independent_evaluator_controls(self):
        self.assertEqual(e.rouge_l('adder adds data', 'adder adds data'), 1)
        self.assertEqual(e.rouge_l('foo', 'bar'), 0)
        self.assertEqual(e.terms('clock reset input output interface'), set())
        self.assertEqual(e.terms('adder and multiplier'), {'add', 'multiply'})


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PortTests))
    g.write_json(Path(__file__).parent / 'results/port_tests.json',
                 {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                  'scope': 'New reconstruction implementation, not original GenEDA'})
    raise SystemExit(not result.wasSuccessful())
