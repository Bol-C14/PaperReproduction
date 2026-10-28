# CROP：单 seed 无检索 guidance 对照

复用原有公开教学 RTL 的摘要缓存，保持模型 Gemini 2.5 Flash、参数、c0 初始配置、3 次后续测量预算、后端和正确性要求一致，移除检索上下文。

| 搜索阶段 | 原检索轨迹 | 无 guidance 对照 |
|---|---:|---:|
| 请求数 | 3 | 3 |
| 费用 USD | 0.0007446 | 0.0006195 |
| 输入 token | 2082 | 1665 |
| 输出 token | 48 | 48 |
| 提案 | c2、c1、c4 | c2、c1、c4 |
| 最佳目标值 | 3784 | 3784 |

四项测量目标值均为 3784、4992、3978、4212。独立审计复核了 CEC 日志、1,024 次向量检查和指标；逐轮恢复两个检索字段后，其余提示词字节一致。本次未观察到 guidance 优势。

这是不同时间窗口下的后置单 seed、缓存条件对照，不是严格配对或统计证据。模型权重／provider 修订未固定，共享安全路由策略曾更新；不能作完整流水线成本比较、工业 PPA 或完整论文复现声明。

对照实际使用 3 次请求，reasoning token 均报告为 0，无未知费用。CROP 实验累计 20 请求、0.0098335 USD。两次前置键序校验失败均未调用模型；已正确测量的 c0 被复用，综合总数仍为 4。

本公开包仅含已审阅的 7 份结果子集；原始响应、完整日志及命令／失败记录继续私有保全。

- [outcome.json](no_guidance_reviewed_subset/outcome.json)
- [target_archive.json](no_guidance_reviewed_subset/target_archive.json)
- [shared-ledger-summary.json](no_guidance_reviewed_subset/shared-ledger-summary.json)
- [comparison.json](no_guidance_reviewed_subset/comparison.json)
- [contexts/1.json](no_guidance_reviewed_subset/contexts/1.json)
- [contexts/2.json](no_guidance_reviewed_subset/contexts/2.json)
- [contexts/3.json](no_guidance_reviewed_subset/contexts/3.json)
