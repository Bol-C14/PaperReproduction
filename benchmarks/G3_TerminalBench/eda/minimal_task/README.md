# Minimal EDA task package (template, not runnable)

This extracts the useful Terminal-Bench boundary: instruction + pinned initial state + time/resource contract + final artifact acceptance. No EDA tool or benchmark is run here. Replace every `REQUIRED` value and freeze hashes before executing.

```
agent_bundle/
  instruction.md       # objective and permitted edits
  inputs/              # pinned RTL, SDC, library references; no solutions/history
  environment.lock.json
verifier_bundle/       # never visible to evaluated agent
  ACCEPTANCE.md
  golden/              # private equivalence baseline / hidden vectors
  verifier.lock.json   # tool image digest, versions, seeds and acceptance rules
trial/
  artifact_manifest.json
  candidate/design.v
  candidate/constraints.sdc
  candidate/change.json
  trajectory.atif.json
  result.json
```

Create agent/verifier images separately. Verify effective resource limits inside both. Copy only declared candidate files to the verifier; reject symlinks, unexpected files, oversized outputs, mismatched hashes, and missing artifacts. Collect reports freshly from trusted tools rather than trusting agent-generated timing/area summaries. Both reference and independently valid alternative circuits must pass, and a broken candidate must fail. Changes are classified by [CHANGE_RULES.md](../CHANGE_RULES.md).
