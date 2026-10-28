"""Independent lexical evaluation: no trainer, PyTorch, model, or API imports.

No lexical metric here establishes circuit-functional correctness.
"""
import collections
import argparse
import json
from pathlib import Path
import re
import statistics

HERE = Path(__file__).resolve().parent
# Frozen before generation. Clock/reset/interface/input/output are excluded as
# generic prompt/template cues. Vocabulary coverage is reported, never assumed.
FUNCTION_TERMS = {
    'add': r'\b(add|adds|added|adder|addition|sum)\b',
    'subtract': r'\b(subtract|subtracts|subtractor|subtraction|difference)\b',
    'multiply': r'\b(multiply|multiplies|multiplier|multiplication|product)\b',
    'compare': r'\b(compare|compares|comparator|comparison|equality)\b',
    'increment': r'\b(increment|increments|incremented|incrementing)\b',
    'decrement': r'\b(decrement|decrements|decremented|decrementing)\b',
    'counter': r'\b(counter|counters|counting)\b',
    'state_machine': r'\b(fsm|state machine|finite.state)\b',
    'memory': r'\b(memory|memories|ram|rom|cache)\b',
    'instruction': r'\b(instruction|instructions|opcode|opcodes|decode|decoding)\b',
    'pipeline': r'\b(pipeline|pipelined|pipelining|stages)\b',
    'branch': r'\b(branch|branches|branching|jump)\b',
    'shift': r'\b(shift|shifts|shifter|shifting)\b',
    'multiply_divide': r'\b(division|divide|divider|quotient|remainder)\b',
    'interrupt': r'\b(interrupt|interrupts|exception|exceptions)\b',
    'arbitration': r'\b(arbitrate|arbiter|arbitration|priority)\b',
    'toggle': r'\b(toggle|toggles|toggling|inverts|inversion)\b',
    'parity': r'\b(parity|xor|exclusive.or)\b',
    'multiplex': r'\b(multiplex|multiplexer|mux|selects|selection)\b',
    'buffer': r'\b(buffer|buffering|fifo|queue)\b',
}


def tokens(text):
    return re.findall(r'[a-z0-9_]+', text.lower())


def rouge_l(generated, reference):
    a, b = tokens(generated), tokens(reference)
    if not a or not b:
        return 0.0
    previous = [0] * (len(b) + 1)
    for x in a:
        current = [0]
        for j, y in enumerate(b):
            current.append(previous[j] + 1 if x == y else max(previous[j + 1], current[-1]))
        previous = current
    return 2 * previous[-1] / (len(a) + len(b))


def terms(text):
    return {name for name, pattern in FUNCTION_TERMS.items() if re.search(pattern, text.lower())}


def score(example):
    generated, reference = example['generated'], example['reference_prefix']
    a, b = terms(generated), terms(reference)
    overlap = len(a & b)
    precision = overlap / len(a) if a else 0.0
    recall = overlap / len(b) if b else None
    f1 = 2 * overlap / (len(a) + len(b)) if b else None
    words = tokens(generated)
    bigrams = list(zip(words, words[1:]))
    raw = generated.encode('utf-8')
    byte_trigrams = [raw[i:i+3] for i in range(max(0, len(raw)-2))]
    return {'id': example['id'], 'seed': example['seed'], 'arm': example['arm'],
            'split': example['split'], 'intervention': example['intervention'],
            'exact_prefix_match': generated == reference,
            'rouge_l_f1': rouge_l(generated, reference),
            'functional_terms_precision': precision, 'functional_terms_recall': recall,
            'functional_terms_f1': f1, 'reference_terms': sorted(b), 'generated_terms': sorted(a),
            'generated_bytes': len(generated.encode()),
            'repeated_bigram_fraction': 1 - len(set(bigrams)) / len(bigrams) if bigrams else 0.0,
            'repeated_byte_trigram_fraction': 1 - len(set(byte_trigrams)) / len(byte_trigrams) if byte_trigrams else 0.0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir', default='results')
    args = parser.parse_args()
    results = HERE / args.results_dir
    examples = []
    for path in sorted(results.glob('run_*.json')):
        examples.extend(json.loads(path.read_text())['generations'])
    for path in sorted(results.glob('baselines_seed*.json')):
        examples.extend(json.loads(path.read_text()))
    assert examples, 'No generations found'
    rows = [score(row) for row in examples]
    groups = collections.defaultdict(list)
    for row in rows:
        groups[(row['seed'], row['arm'], row['split'], row['intervention'])].append(row)
    summaries = []
    for key, subset in sorted(groups.items()):
        summary = dict(zip(['seed', 'arm', 'split', 'intervention'], key))
        summary['n'] = len(subset)
        for metric in ['exact_prefix_match', 'rouge_l_f1', 'functional_terms_precision', 'functional_terms_recall', 'functional_terms_f1', 'generated_bytes', 'repeated_bigram_fraction', 'repeated_byte_trigram_fraction']:
            values = [row[metric] for row in subset if row[metric] is not None]
            summary[metric] = statistics.mean(values) if values else None
        summary['references_with_functional_terms'] = sum(bool(row['reference_terms']) for row in subset)
        summaries.append(summary)
    out = {'scope': 'Independent lexical answer-prefix evaluation; not formal or simulated circuit equivalence',
           'functional_vocabulary': FUNCTION_TERMS, 'per_example': rows, 'summaries': summaries}
    (results / 'evaluation.json').write_text(json.dumps(out, indent=2) + '\n')
    lines = ['seed\tarm\tsplit\tintervention\tn\trouge_l\tfunctional_f1\trepeated_bigrams']
    for x in summaries:
        lines.append('\t'.join(map(str, [x['seed'], x['arm'], x['split'], x['intervention'], x['n'], x['rouge_l_f1'], x['functional_terms_f1'], x['repeated_bigram_fraction']])))
    (results / 'evaluation.tsv').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
