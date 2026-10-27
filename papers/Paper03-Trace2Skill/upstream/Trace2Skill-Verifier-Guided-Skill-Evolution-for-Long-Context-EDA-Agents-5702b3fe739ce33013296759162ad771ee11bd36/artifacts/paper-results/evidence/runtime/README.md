# C3/C4 model-call and retry audit

This directory is a strict allow-list extraction from the 16 completed C3/C4
runs and three private batch logs. It contains no timestamps, call IDs,
prompts, responses, error bodies, raw rollout records, endpoint values,
credentials, or machine paths.

## Files

- `llm_calls.csv`: 1,517 model-call attempt rows. Reviewers can group by
  condition, purpose, model, status, attempt, and temperature. Token counts and
  finish reasons are retained; only coarse error class names are retained.
- `rollout_retries.csv`: four rollout-collection retry events. A corresponding
  replacement artifact is present for each event; the
  `replacement_artifact_present` Boolean records file presence only and is not
  an independent validity judgment.
- `launch_settings.json`: path-free launch-header fields and source hashes from
  the C3 primary, C3 restart, and C4 primary batch logs. The recorded endpoint
  value and raw header lines are withheld.
- `source_file_hashes.json`: SHA-256 hashes for the 16 private `llm_calls.jsonl`
  logs, four private rollout-retry logs, and three private batch logs used by
  the allow-list builder.

## Optimizer-call policy and observed calls

The historical optimizer wrapper allowed up to three **total attempts** per
oracle, mutation, integration-repair, or compression call. Retryable errors used
exponential backoff from 10 seconds plus jitter, capped at 120 seconds.

| Condition | Purpose/model | Attempt rows | Observed result |
|---|---|---:|---|
| C3 | GPT-5 oracle stages | 583 | all successful on attempt 1 |
| C3 | Sonnet 4.5 primary mutation, temp. 0.35 | 120 | all successful on attempt 1 |
| C3 | Sonnet 4.5 integration repair, temp. 0.2 | 32 | all successful on attempt 1 |
| C3 | Sonnet 4.5 compression, temp. 0.3 | 27 | all successful on attempt 1 |
| C4 | GPT-5 oracle stages | 589 | all successful on attempt 1 |
| C4 | Sonnet 4.5 primary mutation, temp. 0.35 | 119 | 116 attempt-1 successes, two attempt-1 errors, one attempt-2 success |
| C4 | Sonnet 4.5 integration repair, temp. 0.2 | 31 | all successful on attempt 1 |
| C4 | Sonnet 4.5 compression, temp. 0.3 | 16 | all successful on attempt 1 |

The two C4 mutation errors were one non-retryable authentication-class error and
one retryable internal-server-class error; the latter succeeded on attempt 2.
Compression temperature is source-derived because that field was not written to
the call log; other listed temperatures come from call context or completed-run
configuration. Compression is a conditional LLM call, not a deterministic
operation.

The oracle OpenAI client also set SDK `max_retries=1`, so one logged wrapper
attempt could contain up to two SDK transport attempts. The Sonnet
mutation/repair/compression client set SDK `max_retries=0`. The packaged wrapper
audit does not expose whether the GPT SDK's additional transport attempt
occurred, so wrapper-attempt counts must not be read as wire-request counts.

## Rollout-collection retry policy and observations

The completed-run configuration set `response_error_retries: 3`, meaning one
initial collection plus at most three retries (four total collection attempts),
with a 180-second sleep and reuse of already valid cached outputs. Four actual
retry events were recorded: three in C3 and one in C4. Each event archived five
files from an invalid response attempt, and a corresponding replacement
artifact exists. The exact public coordinates are in `rollout_retries.csv`;
the presence flag alone does not revalidate the replacement contents.

The NeMo Gym request bridge separately configured one total internal attempt
(zero retries) and three total external attempts (two retries), with 0.5-second
retry sleep. Its HTTP limits were 21,600 seconds total and 7,200 seconds socket
read. These semantics are inspectable in the packaged nearest-commit
`nemogym/nemo_gym/server_utils.py`; the collection-loop semantics are in
`optimizer/fitness.py`, and optimizer-call retry behavior is in
`optimizer/llm_audit.py`.

The three private batch headers also recorded the NeMo Gym OpenAI-compatible
retry loop: five initial maximum attempts, extensible by retryable statuses to
an absolute maximum of 12, with exponential backoff capped at 60 seconds. These
headers establish the configured policy, not how often that layer retried;
request-level occurrences are not present in the public audit. They also
recorded a concrete inference endpoint. Its value is intentionally withheld;
the `azure/...` model strings are service aliases routed internally through
that endpoint and do not identify an immutable deployment revision or model
snapshot.

Regenerate the allow-listed tables only in the author-side environment:

```bash
python scripts/build_runtime_audit.py \
  --source-map /private/path/c3c4_source_map.json \
  --batch-log c3_primary:C3:/private/path/c3_primary.log \
  --batch-log c3_restart:C3:/private/path/c3_restart.log \
  --batch-log c4_primary:C4:/private/path/c4_primary.log \
  --output-dir /tmp/trace2skill-runtime-audit
```
