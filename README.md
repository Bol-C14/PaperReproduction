# ASPEN MLCAD 2025：行为复现与批判性审评

当前新轮次见[ATTRIBUTION_ROUND.md](ATTRIBUTION_ROUND.md)：已完成归因、cost增减及持续rollback的后继作用验证，并跑完8个6-call对照臂；数值策略未显示稳定优势。本轮57综合+57 RTL SAT、28份unique tagged RTL，另含被裁剪的FIR失败记录。无LLM API。

```bash
.venv/bin/python scripts/verify_attribution_round.py
```



**当前主要结论：行为部分复现 / Go。** 真实native egglog重写/抽取→免费Yosys综合反馈→局部cost更新和回退→再次抽取→实际RTL SAT已完成。在线LLM和netlist分区归因未复现；原始Table II / Figure 6 / Figure 7数值是次级未复现对照，商业EDA缺失不再是结束行为工作的理由。

先读 [RESPONSE_VALUE_AUDIT.md](RESPONSE_VALUE_AUDIT.md)（开放环与反馈轨迹相同，未隔离response收益），再读 [BEHAVIOR_CONTRACT.md](BEHAVIOR_CONTRACT.md)，再读四份报告：REPRODUCTION.md、EVIDENCE_AUDIT.md、BASELINE_COMPARISON.md、RESEARCH_OPPORTUNITIES.md。第一阶段的68候选离线枚举保持pilot身份；第二阶段48会话使用真实在线综合，每会话7次、含reference，不是查表。完整预算、负结果、替代假设、来源修正和复现命令均在契约中。

- 当前结果、原生e-graph快照、配对frontier与图：`results/behavior/`
- 原始压缩工具日志与逐次调用ledger：`logs/behavior/`
- 固定环境：`configs/behavior-requirements.lock`
- 输入fixtures与规则：`benchmarks/behavior_fixtures.json`、`behavior/table_i_rules.egg`

已有结果静态核验（不新增EDA）：

```bash
python scripts/verify_artifacts.py
python scripts/verify_unique_netlists.py
.venv/bin/python scripts/verify_behavior_artifacts.py
```

行为重跑请使用契约中的新目录 `ASPEN_BEHAVIOR_RUN_ROOT=.runs/rebuild1`，避免覆盖已有证据。补充后累计367次综合+367次生成RTL-to-reference SAT全部通过，只有14份byte-level unique RTL；没有post-synthesis网表等价验证。另有51个手写公式/实例义务UNSAT，非全部.egg规则证明；第一阶段90项是69 UNSAT和21个预期SAT反例，不是90条规则均等价。

ZIP内 `git/` 含完整分支bundle和binary root patch，`RELEASE.json`给出完整commit：

```bash
git clone -b reproduction/aspen-mlcad2025 git/aspen-review.bundle restored
```

未包含依赖、缓存和完整生成netlists，见EXCLUSIONS.md。原ROVER闭源的来源已核实，但ASPEN自己的TableI+fixed-cost baseline可以独立重建；作者extraction-gym fork并不是完整ROVER。所有数值、非在线LLM替代和官方原始数据严格分开。

14份原始代表JSON网表已包含于results/behavior/unique_netlists，支持独立结构指标重算。开放环永远+3，不读response、不rollback；最后candidate与统一外部best-so-far分别报告。Algorithm1分区归因、cost下降、online LLM仍未实现。
