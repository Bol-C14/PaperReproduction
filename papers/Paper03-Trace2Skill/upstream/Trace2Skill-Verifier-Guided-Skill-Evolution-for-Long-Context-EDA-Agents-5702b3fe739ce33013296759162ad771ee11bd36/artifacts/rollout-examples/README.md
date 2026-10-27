# Sanitized rollout examples

This directory contains two small, real action traces selected from the
archived paper runs:

- `c3_noobscpu_sparse_example.jsonl`: C3 sparse-reward failure.
- `c4_noobscpu_dense_example.jsonl`: C4 dense-feedback pass.

Both records use task `NoobsCpu-8bit_0002`, generation 1, individual 0,
scheduler repeat 2, and the same seed-skill SHA-256. They are independently
sampled rollouts, not a matched counterfactual pair. Their purpose is to make
the mechanics of C3 versus C4 inspectable without publishing raw model or
verifier material.

## What a record retains

Each record includes the task/generation/individual/repeat coordinate, final
reward, individual pass rate, SelectQ, SkillQ, AgentProgressQ, AgentVarianceQ,
AgentAdherenceQ, ordered tool names, action classes, byte counts, and SHA-256
commitments. For C4, only numeric and Boolean fields from the already
agent-visible sanitized verifier response are retained.

The archive's `_ng_rollout_index` is used as the semantic repeat identifier.
Because completed rollouts can be written to JSONL out of scheduler order, the
zero-based JSONL storage ordinal is recorded separately in `provenance`.

## What is excluded

The exporter omits all prompts, task/context bodies, assistant prose and
reasoning, generated RTL and patches, filenames, path values, command text,
tool-result text, test names, detailed failure text, signal names, provider
metadata, endpoint information, container logs, hidden-verifier source/output,
and machine-local paths. A hash is a provenance commitment, not a claim that
the withheld raw archive is part of the public artifact.

See [`paired_trace_summary.md`](paired_trace_summary.md) for a compact reading
of the pair and [`schema.json`](schema.json) for the machine-readable schema.

## Validation and regeneration

Validate the committed samples without access to the private archive:

```bash
python3 scripts/export_public_rollout_example.py check \
  artifacts/rollout-examples/c3_noobscpu_sparse_example.jsonl \
  artifacts/rollout-examples/c4_noobscpu_dense_example.jsonl
```

The `export` subcommand regenerates a record when an authorized evaluator has
the raw JSONL, matching individual metadata, and the packaged public rollout
and quality evidence. Run `--help` for its explicit inputs. The exporter fails
closed on unknown tools, argument fields, inconsistent metrics, or text that
resembles a private path, internal endpoint, or credential.
