# CROP 真实 pilot：精简公开摘要

在公开教学 RTL 上，使用 Gemini 2.5 Flash 和固定 MiniLM 编码器，完成了真实摘要、检索、提案及测量反馈闭环。17 次请求费用为 0.009214 USD。检索选中 multiply；FIR3 四次测量目标值依次为 3784、4992、3978、4212，均通过正确性检查，最佳仍为初始配置，未观察到改善。该实验仅覆盖单目标、单种子和替代工具，尚无匹配的 LLM 对照，不能据此宣称质量优势或完整论文复现。

本公开包仅包含已逐字段审阅的 7 份证据子集；完整原始证据继续私有保全。

- [outcome.json](real_pilot_reviewed_subset/outcome.json)
- [target_archive.json](real_pilot_reviewed_subset/target_archive.json)
- [retrieval.json](real_pilot_reviewed_subset/retrieval.json)
- [shared-ledger-summary.json](real_pilot_reviewed_subset/shared-ledger-summary.json)
- [contexts/1.json](real_pilot_reviewed_subset/contexts/1.json)
- [contexts/2.json](real_pilot_reviewed_subset/contexts/2.json)
- [contexts/3.json](real_pilot_reviewed_subset/contexts/3.json)
