"""Pure pilot interfaces. No transport, model, EDA tool, or filesystem side effects."""
import math

SYSTEM = ('You are a precise RTL synthesis assistant. Output exactly one valid JSON object '
          'with no markdown or explanations outside JSON. Use the exact requested keys.')


def messages(prompt):
    return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': prompt}]


def nearest_prior(caches, designs, target='fir3'):
    byid = {d['id']: d for d in designs}
    priors = [d['id'] for d in designs if d['role'] == 'prior']
    if not priors or any(byid[p]['family'] == byid[target]['family'] for p in priors):
        raise ValueError('Prior archive overlaps target family or is empty')
    vectors = {name: caches[name]['embedding'] for name in priors + [target]}
    for vec in vectors.values():
        if len(vec) != 384 or any(type(v) not in (float, int) or not math.isfinite(v) for v in vec):
            raise ValueError('Invalid semantic vector')
        if not math.isclose(sum(v*v for v in vec), 1.0, abs_tol=1e-5):
            raise ValueError('Semantic vectors must have L2 unit norm')
    ranked = sorted([(sum(a*b for a, b in zip(vectors[target], vectors[p])), p)
                     for p in priors], key=lambda item: (-item[0], item[1]))
    return ranked[0][1], ranked


def guidance(history, selected, backend_relation):
    """Only within-prior ratios travel to the model; never pool raw backend metrics."""
    if backend_relation not in ('matched_native_archive', 'cross_backend_archival_guidance'):
        raise ValueError('Unknown QoR backend relation')
    rows = history[selected]
    if not rows or len({r['config'] for r in rows}) != len(rows):
        raise ValueError('Missing or repeated prior configurations')
    for row in rows:
        if row['status'] != 'ok' or type(row['objective']) not in (int, float) or not math.isfinite(row['objective']) or row['objective'] <= 0:
            raise ValueError('Invalid prior observation')
    baseline = next(r['objective'] for r in rows if r['config'] == 'c0')
    return [{'config': r['config'], 'normalized_objective': r['objective'] / baseline,
             'normalization': 'same prior circuit and backend c0', 'backend_relation': backend_relation}
            for r in sorted(rows, key=lambda r: (r['objective'], r['config']))[:3]]


def observation(row):
    if row['status'] != 'ok' or row.get('formal') != 'ABC CEC: equivalent' or row.get('independent') != 'Python arithmetic versus LUT truth tables: pass':
        raise ValueError('Fresh observation lacks formal and independent correctness')
    if type(row.get('objective')) not in (int, float) or not math.isfinite(row['objective']) or row['objective'] <= 0:
        raise ValueError('Invalid fresh objective')
    if row['objective'] != row['lut_count'] * row['lut_depth'] or row.get('vectors_checked') != 256:
        raise ValueError('Fresh QoR/check accounting mismatch')
    return {key: row[key] for key in ('config', 'objective', 'status', 'invocation')}


class AttemptBudget:
    """All attempts, including malformed model outputs, consume the same budget."""
    def __init__(self, max_total=34):
        self.stages = {}
        self.total = 0
        self.max_total = max_total

    def consume(self, stage):
        if self.total >= self.max_total or self.stages.get(stage, 0) >= 2:
            raise ValueError('Model attempt budget exhausted')
        self.stages[stage] = self.stages.get(stage, 0) + 1
        self.total += 1
        return {'stage': stage, 'attempt': self.stages[stage], 'total_attempts': self.total}


def proposal_context(configs, selected, prior_guidance, archive, design_summary, iteration):
    if len(archive) != iteration or len({r['config'] for r in archive}) != len(archive):
        raise ValueError('Target context must contain only distinct preceding observations')
    if any(r['status'] != 'ok' for r in archive):
        raise ValueError('Failed observation cannot be guidance')
    return {'arm': 'semantic_llm', 'seed': 23, 'iteration': iteration,
            'legal_configs': configs, 'retrieved_prior': selected,
            'retrieved_guidance': prior_guidance, 'target_history': list(archive),
            'objective': 'LUT4 count * maximum unit LUT depth; lower is better',
            'design_summary': design_summary,
            'comparison_policy': 'Prior ratios are guidance only; target QoR comparisons use this fresh native run only'}


def ascii_chat_token_bound(chat_messages):
    """Upper bound ONLY for an approved byte-BPE model with <=256 framing tokens.

    All visible text is ASCII. Each byte-BPE content token consumes at least one
    byte. The parent must confirm the serving template/hidden input overhead
    fits the separately reserved 256 tokens before authorizing this profile.
    """
    size = 256
    for message in chat_messages:
        if set(message) != {'role', 'content'} or message['role'] not in ('system', 'user'):
            raise ValueError('Unexpected chat message')
        for value in message.values():
            size += len(value.encode('ascii'))
    return size
