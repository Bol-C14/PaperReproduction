# Novelty：它比总结、compact、generate/update skill 多了什么？

**区别主要在外部执行验证和跨 rollout 的选择制度，而不是“文本叫 skill”。** Trace→lesson→文档更新本身已有充分先例。这个发布树提供的具体组合是：EDA 可见工具/隐藏验证隔离、task-local population、实测选择、语义保留 gate、可审计 lineage，以及可选的 rollout 内 verifier 修复。机制存在不等于已证明它比成本相同的普通做法好。

## 操作层次

| 环节 | Trace2Skill 的可见实现 | 与普通方法的可检验差别 | 本轮证据 |
|---|---|---|---|
| 技能生成 | oracle 的成功/失败分层总结 + mutator 文档改写 | 若总结也接相同失败/工具输出，生成材料大幅重合 | prompt、代码；没运行 LLM |
| 候选选择 | 原 parent+children 均 rollout；pass优先，dense仅tie-break；语义退化直接block | 普通总结通常不比较多个新策略的实测表现；best-of-N 可以比较输出而不更新策略 | 19 helper 检查、320行分数 |
| 合并与保留 | lesson bank、KEEP/ADD/REMOVE/CHANGE、sanitizer/repair、parent fallback | 比盲覆盖更保守；不是每次都做多parent crossover | paper配置 crossover_rate=0；不能把通用GA代码当实际贡献 |
| verifier反馈 | C4私有副本反馈，编辑与成功compile之后，最多3次执行 | 纯摘要不产生新功能证据；但普通agent也可接同一feedback工具 | 静态路径+1052次公开计数，未容器重跑 |
| 压缩 | 超字符budget可调用Sonnet压缩；另有确定性condense | 是辅助预算管理，不是外层学习的替代定义 | C3 27/C4 16 compression calls |
| skill复用 | survivor注入该任务下一批新rollout，并重新评估 | 区别于同一会话自动compact保留当下状态；未证明跨任务skill transfer | carry/reset纯函数，task-local配置 |
| 执行闭环 | 内层RTL修复与外层policy文档搜索并存 | 若仅展示C4边改边测，不能单独归功外层skill更新 | gen1 seed案例不能证明evolution因果 |

必要行为契约不是任何摘要都能满足：**生成文档必须实际改变下一批独立 agent 的输入；候选必须接受同协议验证后才能成为父本；保留负例与旧教训；明确反馈可见性；完整记账选择成本。** 反过来，普通 update-skill 系统若满足这些条件，便属于相近的执行反馈驱动策略优化；不能因为换术语就判为新范式。

`skill_selector.py` 有旧语义 selector，测试会出现 `rollout_fitness_used_for_selection=False`。论文 standard EA 配置实际绕过该即时语义选择，将 child 延后到下一代 rollout；`run_optimizer.py` 4875、4935、5241附近是生效路径。不能仅按文件名或旧 selector docstring 判定论文选择了未评估 child。语义gate仍影响可生存性；它不是消失了。

## 有定义的对照，而不是名字相近

| 方法 | 适配状态与反馈 | 与 Trace2Skill 最接近/不同之处 | 当前可比较性 |
|---|---|---|---|
| 固定skill best-of-N | skill固定；N份RTL候选，用相同终验选输出 | 去掉外层policy改写，保留搜索预算，是优先必要对照 | 未运行，官方缺同预算80/task对照 |
| 普通trace总结/update skill | 用等量成功+失败trace产生单份总结再复用 | 很接近oracle+mutator；需给同样上下文、长度、角色模型预算 | 未运行；不把手工规则当LLM总结 baseline |
| 自动compact | 单次rollout上下文压缩；状态压缩而非跨rollout实测策略选优 | 主要优化context预算，可与外层EA同时存在 | 未运行；需单独固定最终输入/token预算 |
| 无verifier演化 | 外层更新读可见trace，但去掉runtime反馈；进一步去掉终验选择是另一因素 | C3仍使用最终hidden verifier标签，并非真正无verifier | 官方C3不是完整 no-verifier ablation |
| GEPA | 反思执行轨迹、提出并测试prompt更新；Pareto候选及互补经验组合 | 与外层反思/进化prompt优化高度重叠；Trace2Skill是task-local单survivor+EDA gate，并未证其优于GEPA | 概念对照；未安装、运行或声称实现GEPA |
| ACE（Context Engineering） | Generator/Reflector/Curator；带ID/计数的bullet、增量delta与确定性合并、grow/refine | 与lesson bank/保留经验相似，但数据结构与更新/选择不同 | 概念对照；没有把简化重排叫ACE |
| ACE-RTL | RTL-specialized generator + frontier reflector + evolving per-problem context + parallel scaling | 内层程序修复及上下文演化相关，模型训练与测试预算不同 | 原论文自己将其视为互补；不能搬原表格作等预算胜负 |

定义来源：[GEPA 原论文](https://arxiv.org/abs/2507.19457)、[GEPA 官方实现](https://github.com/gepa-ai/gepa)、[ACE §3](https://arxiv.org/html/2510.04618v1)、[ACE-RTL §3](https://arxiv.org/html/2602.10218v1)。已读取这些定义；本审评不宣称运行任何一个基线。ACE 与 ACE-RTL 亦非同一个具体实现。

## 可执行的有界消融：只重排已知人口

`metrics/selector_replay.csv` 有80个人口×5种规则共400行；最低individual index作确定性tie-break。只使用已采样结果，**不是生成反事实后续trace的干预实验**。字段 archived_formula_winner 指公开SelectQ推得赢家，不是声称恢复所有隐藏survivor日志。

| 重排规则 | 改变首选 / 80 | 首选tie / 80 | 原SelectQ赢家不在该规则并列最优中 |
|---|---:|---:|---:|
| 冻结实现 | 0 | 7 | 0 |
| 论文权重、保留gate | 0 | 7 | 0 |
| 只看sparse pass、保留gate | 32 | 40 | 0 |
| 去掉语义gate | 11 | 7 | 11 |
| 只看SkillQ、保留gate | 22 | 20 | 12 |

解释：sparse-only的32次变化全是tie处理差别，不能当dense分数带来更高功能收益；论文/代码权重数值差异在这个已知人口上没有改变选择；语义gate实际约束候选，去掉会改11/80，但不能推出终验更好或更坏。由于下游未重新生成，所有选中候选的pass fraction均为in-sample，不能把挑出的最高值当held-out准确率。

## 泄漏、选择与机制/预算混淆

- 任务筛选：先挑seed失败再扩展到每任务80次，比较32与640不是隔离EA贡献；筛选出的失败会回归均值。后续seed96审计在同八任务已有5/32，但不是官方C1，不拿它拼一个新主结果。
- 评价反馈用于选择：最终hidden verifier标签明确进入SelectQ，runtime反馈进入内层修复/外层总结。对于test-time optimization，这是被允许的适配信号；对于held-out评估，则是评价复用污染。标签“hidden”不等于整个搜索期间未接触评价信息。
- 工具隔离：源码在private copy运行harness并清理输出；sanitizer修复不可用工具/路径建议。没有证据证明偷看reference solution，也没有原始私有资料可证明绝无泄漏。sanitized功能信息仍可使策略学习特定harness语义，必须与泛化分开。
- task family：PCIe两个任务、802.11a多个任务与同仓库代码会共享知识；研究声称task-local聚合，未给跨家族锁定split。没有证据确证发生跨run训练泄漏；同样不能据无split宣称transfer已验证。
- 成功故事：公开两条trace与单个lineage是选择性案例；主分母没有仅留成功样本，但invalid-response替换属于观测缺口，quality图亦排除blocked候选。
- 角色模型与预算：oracle GPT-5、mutator/repair/compress Sonnet、rollout Opus一起参与。C4并非纯“多一种文字表示”，它还得到1052次新的外部功能观测和更高token消耗。C3/C4时段也不同，历史routing revision缺失，模型漂移不能排除。

最合理的novelty定位是**EDA场景中带可见性约束、语义保留和实测选择的工程组合及可审计过程**。一般性的“轨迹转skill并更新”与已有prompt/context adaptation有明显重叠；“新机制而非更多搜索/反馈预算”尚未被识别。
