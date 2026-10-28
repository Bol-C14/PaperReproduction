# ABC-RL ICLR2024 — checkpoint mechanism study

This branch contains the CPU reproduction work for **Retrieval-Guided Reinforcement Learning for Boolean Circuit Minimization**.

Read [completed multi-seed results](p09_abc_rl/ABLATION_REPORT.md), [method, graph-lifecycle correction and limitations](p09_abc_rl/ABLATION_METHOD.md), [frozen protocol](p09_abc_rl/ABLATION_PROTOCOL.json), and [separate repairs](p09_abc_rl/port/repairs.patch).

Real checkpoint inference, native ABC Area*Delay evaluation and CEC have run.
The first pilot's graph interface reuse was subsequently found to contaminate
retrieval features; its ADP/CEC logs remain evidence for those recipes. The completed
multi-seed ablation uses fresh native interfaces: 362 ADP evaluations and362 CEC
checks passed. Adaptive retrieval showed no stable advantage in this small study.
No full-paper numerical reproduction, full training or verified checkpoint
training-lineage claim is made. Historical preflight files retain their original
phase-specific metrics.

Existing inherited ASPEN files/history are retained from the base; they are not P09 results. Other reproduction branches are unchanged.
