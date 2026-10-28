# ABC-RL ICLR2024 — checkpoint mechanism study

This branch contains the CPU reproduction work for **Retrieval-Guided Reinforcement Learning for Boolean Circuit Minimization**.

Read [current method, graph-lifecycle correction and limitations](p09_abc_rl/ABLATION_METHOD.md), [frozen multi-seed protocol](p09_abc_rl/ABLATION_PROTOCOL.json), [paper-local overview](p09_abc_rl/README.md), and [separate repairs](p09_abc_rl/port/repairs.patch).

Real checkpoint inference, native ABC Area*Delay evaluation and CEC have run.
The first pilot's graph interface reuse was subsequently found to contaminate
retrieval features; its ADP/CEC logs remain evidence for those recipes. The new
multi-seed ablation uses fresh native interfaces and checks every candidate.
No full-paper numerical reproduction, full training or verified checkpoint
training-lineage claim is made. Historical preflight files retain their original
phase-specific metrics.

Existing inherited ASPEN files/history are retained from the base; they are not P09 results. Other reproduction branches are unchanged.
