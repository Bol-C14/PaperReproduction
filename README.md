# ASPEN MLCAD 2025：部分复现审阅包

完整复现 No-Go；免费替代机制 pilot 已完成。请先读 REPRODUCTION.md，再读 EVIDENCE_AUDIT.md、BASELINE_COMPARISON.md 和 RESEARCH_OPPORTUNITIES.md。所有官方结论、替代结果与语义前提分开报告。

运行/重建命令见 REPRODUCTION.md；固定依赖在 configs/requirements.lock 与 configs/analysis-requirements.txt。结果图在 results/*.png，逐候选与逐种子查询记录在 results/*.json，必要原始日志在 logs/。可执行静态交叉核验：

```bash
python scripts/verify_artifacts.py
```

ZIP 的 git/ 目录含本分支全历史 bundle 和含 binary 图的完整 root patch；RELEASE.json 给出 branch/完整 commit。恢复完整历史：

```bash
git clone git/aspen-review.bundle restored
git -C restored switch reproduction/aspen-mlcad2025
```

EXCLUSIONS.md 记录未包含文件与重建方法。审阅包不是完整商业 EDA/ASAP7 或在线 LLM 运行环境。90 项回归中 21 项是预期反例；不是 90 条规则均等价。
