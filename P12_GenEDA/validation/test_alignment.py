"""Original GenEDA connector/interface tests with a frozen synthetic word table.

No LLM, language-generation objective, pretrained weights or remote code is loaded.
AST extraction executes the original selected methods without importing the
surrounding Transformers/LLaVA application. Original source bytes stay unchanged.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import resource
import time
from types import SimpleNamespace
import unittest

import numpy as np
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
torch.set_num_threads(2)
torch.set_num_interop_threads(1)
torch.manual_seed(17)
IGNORE_INDEX, IMAGE_TOKEN_INDEX = -100, -200
METRICS = {}


def source(path):
    raw = (HERE / 'upstream' / path).read_bytes()
    expected = json.loads((HERE / 'results' / 'integrity.json').read_text())['source_files'][path]['sha256']
    assert hashlib.sha256(raw).hexdigest() == expected, f'Modified upstream source: {path}'
    return raw.decode()


namespace = {'torch': torch, 'IGNORE_INDEX': IGNORE_INDEX, 'IMAGE_TOKEN_INDEX': IMAGE_TOKEN_INDEX, 'dataclass': dataclass}
exec(compile(source('projector_builder.py'), 'upstream/projector_builder.py', 'exec'), namespace)
builder = namespace['build_vision_projector']
tree = ast.parse(source('llava_arch.py'))
original_class = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'LlavaMetaForCausalLM')
methods = [x for x in original_class.body if isinstance(x, ast.FunctionDef) and x.name in {'encode_graph', 'prepare_inputs_labels_for_multimodal'}]
exec(compile(ast.Module(body=methods, type_ignores=[]), 'upstream/llava_arch.py', 'exec'), namespace)
train_tree = ast.parse(source('train.py'))
collator = next(x for x in train_tree.body if isinstance(x, ast.ClassDef) and x.name == 'DataCollatorForSupervisedDataset')
defer_annotations = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
exec(compile(ast.fix_missing_locations(ast.Module(body=[defer_annotations, collator], type_ignores=[])), 'upstream/train.py', 'exec'), namespace)
Collator = namespace['DataCollatorForSupervisedDataset']
fixture = np.load(HERE / 'results' / 'fixture_features.npz', allow_pickle=False)
GRAPHS = torch.from_numpy(fixture['train'][:16].copy())


class Harness(nn.Module):
    encode_graph = namespace['encode_graph']
    prepare_inputs_labels_for_multimodal = namespace['prepare_inputs_labels_for_multimodal']

    def __init__(self, width=32, padding='right', max_length=128):
        super().__init__()
        self.backbone = nn.Module()
        self.backbone.mm_projector = builder(SimpleNamespace(mm_hidden_size=768, hidden_size=width, mm_projector_type='mlp2x_gelu'))
        self.backbone.embed_tokens = nn.Embedding(64, width)
        self.backbone.embed_tokens.weight.requires_grad_(False)
        self.config = SimpleNamespace(tokenizer_padding_side=padding, tokenizer_model_max_length=max_length)
        self.dtype = torch.float32
        self.device = torch.device('cpu')

    def get_model(self):
        return self.backbone

    def prepare(self, ids, graphs, labels=None, mask=None):
        return self.prepare_inputs_labels_for_multimodal(ids, None, mask, None, labels, graphs)


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        self.model = Harness()
        self.ids = torch.tensor([[4, IMAGE_TOKEN_INDEX, 5, 6]])
        self.labels = torch.tensor([[IGNORE_INDEX, IGNORE_INDEX, 5, 6]])

    def test_01_projector_width_and_shape(self):
        self.assertEqual(tuple(self.model.encode_graph(GRAPHS[:2]).shape), (2, 32))
        self.assertEqual(tuple(self.model.encode_graph(GRAPHS[0]).shape), (32,))
        wide = Harness(width=2048)
        self.assertEqual(tuple(wide.encode_graph(GRAPHS[:1]).shape), (1, 2048))
        METRICS['fixture_projector_parameters_width32'] = sum(x.numel() for x in self.model.backbone.mm_projector.parameters())
        METRICS['fixture_projector_parameters_width2048'] = sum(x.numel() for x in wide.backbone.mm_projector.parameters())

    def test_02_actual_features_inserted_and_text_preserved(self):
        result = self.model.prepare(self.ids, GRAPHS[0], self.labels)
        embeds, labels = result[4:]
        self.assertEqual(tuple(embeds.shape), (1, 4, 32))
        torch.testing.assert_close(embeds[0, 1], self.model.encode_graph(GRAPHS[0]))
        torch.testing.assert_close(embeds[0, [0, 2, 3]], self.model.backbone.embed_tokens(torch.tensor([4, 5, 6])))
        self.assertEqual(labels.tolist(), [[IGNORE_INDEX, IGNORE_INDEX, 5, 6]])

    def test_03_original_collator_and_batched_feature_pairing(self):
        instances = [{'input_ids': self.ids[0], 'labels': self.labels[0], 'graph': GRAPHS[i]} for i in range(2)]
        batch = Collator(SimpleNamespace(pad_token_id=0, model_max_length=128))(instances)
        self.assertEqual(tuple(batch['images'].shape), (2, 768))
        out = self.model.prepare(batch['input_ids'], batch['images'], batch['labels'], batch['attention_mask'])
        torch.testing.assert_close(out[4][:, 1], self.model.encode_graph(GRAPHS[:2]))
        self.assertEqual(out[5][:, 1].tolist(), [IGNORE_INDEX, IGNORE_INDEX])

    def test_04_gradients_reach_connector_not_frozen_word_fixture(self):
        out = self.model.prepare(self.ids, GRAPHS[0], self.labels)[4]
        out[:, 1].square().mean().backward()
        gradients = [x.grad for x in self.model.backbone.mm_projector.parameters()]
        self.assertTrue(all(x is not None and torch.isfinite(x).all() for x in gradients))
        norm = sum(x.square().sum().item() for x in gradients) ** 0.5
        self.assertGreater(norm, 0)
        self.assertIsNone(self.model.backbone.embed_tokens.weight.grad)
        METRICS['connector_gradient_norm_fixture'] = norm

    def test_05_missing_marker_silently_drops_graph(self):
        ids = torch.tensor([[4, 5, 6]])
        first = self.model.prepare(ids, GRAPHS[0])[4]
        second = self.model.prepare(ids, GRAPHS[1])[4]
        torch.testing.assert_close(first, second)
        torch.testing.assert_close(first[0], self.model.backbone.embed_tokens(ids[0]))
        METRICS['missing_marker_behavior'] = 'Graph projected, but zero graph tokens inserted; text-only output.'

    def test_06_bad_feature_dimension_rejected(self):
        with self.assertRaises(RuntimeError):
            self.model.encode_graph(torch.zeros(1, 767))

    def test_07_more_markers_than_features_rejected(self):
        with self.assertRaises(IndexError):
            self.model.prepare(torch.tensor([[4, IMAGE_TOKEN_INDEX, IMAGE_TOKEN_INDEX, 5]]), GRAPHS[:1])

    def test_08_right_and_left_padding_and_masks(self):
        ids = torch.tensor([[4, IMAGE_TOKEN_INDEX, 5, 6], [4, IMAGE_TOKEN_INDEX, 5, 0]])
        mask = ids.ne(0)
        labels = ids.clone()
        labels[labels == IMAGE_TOKEN_INDEX] = IGNORE_INDEX
        for side in ['left', 'right']:
            model = Harness(padding=side)
            out = model.prepare(ids, GRAPHS[:2], labels, mask)
            self.assertEqual(out[2].sum(dim=1).tolist(), [4, 3])
            pad_location = 0 if side == 'left' else 3
            self.assertEqual(out[2][1, pad_location].item(), False)
            self.assertEqual(out[5][1, pad_location].item(), IGNORE_INDEX)
            torch.testing.assert_close(out[4][1, pad_location], torch.zeros(32))

    def test_09_real_feature_shuffle_changes_graph_token_only(self):
        # Fixed pair; assert they are not a duplicate feature vector.
        self.assertFalse(torch.equal(GRAPHS[0], GRAPHS[1]))
        first = self.model.prepare(self.ids, GRAPHS[0])[4]
        second = self.model.prepare(self.ids, GRAPHS[1])[4]
        delta = (first - second).abs().amax(dim=-1)
        self.assertGreater(delta[0, 1].item(), 0)
        self.assertEqual(delta[0, [0, 2, 3]].sum().item(), 0)
        METRICS['graph_token_change_max_fixture'] = delta[0, 1].item()

    def test_10_synthetic_connector_optimization_fixed_40_steps(self):
        # Synthetic targets only: proves numerical trainability, not semantic alignment.
        generator = torch.Generator().manual_seed(17)
        target = torch.randn((len(GRAPHS), 32), generator=generator)
        optimizer = torch.optim.AdamW(self.model.backbone.mm_projector.parameters(), lr=0.01)
        trace = []
        for step in range(41):
            prediction = self.model.encode_graph(GRAPHS)
            loss = (prediction - target).square().mean()
            trace.append({'step': step, 'mse': loss.item()})
            if step < 40:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        with torch.no_grad():
            shuffled = (self.model.encode_graph(GRAPHS.roll(1, dims=0)) - target).square().mean().item()
        METRICS['synthetic_training'] = {'semantic_alignment': False, 'generation': False, 'seed': 17,
                                       'train_rows': len(GRAPHS), 'steps': 40, 'lr': 0.01,
                                       'initial_mse': trace[0]['mse'], 'final_mse': trace[-1]['mse'],
                                       'shuffled_training_fixture_mse': shuffled,
                                       'trace': trace,
                                       'interpretation': 'Synthetic train-set unit check only; no validation/test targets used and no scientific generalization claim.'}
        self.assertLess(trace[-1]['mse'], trace[0]['mse'])
        self.assertIsNone(self.model.backbone.embed_tokens.weight.grad)

    def test_11_truncation_can_remove_graph_marker(self):
        model = Harness(max_length=1)
        result = model.prepare(self.ids, GRAPHS[0], self.labels)
        self.assertEqual(tuple(result[4].shape), (1, 1, 32))
        torch.testing.assert_close(result[4][0, 0], model.backbone.embed_tokens(torch.tensor(4)))


class RecordingResult(unittest.TextTestResult):
    records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({'test': test.id(), 'status': 'pass'})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({'test': test.id(), 'status': 'fail', 'error': self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({'test': test.id(), 'status': 'error', 'error': self._exc_info_to_string(err, test)})


if __name__ == '__main__':
    start = time.monotonic()
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(unittest.defaultTestLoader.loadTestsFromTestCase(AlignmentTests))
    record = {'scope': 'Original source projector/insertion/collator, fixture embeddings; NOT end-to-end generation',
              'torch_version': torch.__version__, 'cuda_built': torch.backends.cuda.is_built(),
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'records': result.records, 'metrics': METRICS,
              'elapsed_seconds': time.monotonic() - start,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE / 'results' / 'alignment_tests.json').write_text(json.dumps(record, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
