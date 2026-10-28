# 基线、机会预算与结果解释

> **GP审计修订 v2（原v1结果未删除）**：旧整配置ID one-hot + 固定各向同性Matérn使所有未见候选的后验均值/方差/EI相同，索引argmax退化；其GP arm是**无信息GP**，不得据此评价BO收益。原单父穷举6/6综合候选，终态也不能检验综合GP选择价值。v1报告/CSV/ledger原文保存在`evidence/v1_163c5fd/`，原2684次记录及git历史保留。修正使用fast二值+标准化log(delay)，放置util+density标准化；非对称EI及各20次ID重排回归通过。新证据在`GP_CORRECTION.md`与`results/gp_fix_summary.md`，只跑非穷举小预算pilot，不与v1合并。无在线LLM、七阶段未测；No-Go边界不变。


完整逐run表见 `results/comparison.csv`；离线可重算汇总见 `results/summary.md`，图见 `results/comparison.png`。`results/ledger.json`区分实际执行数、全配置唯一数、网表唯一哈希数、种子搜索和确定性重复。这里的标签是本地对照，不能冒用为作者的CROP/FlowTuner/ORFS-agent实现。

| 本地方法 | 检索与初始化 | 搜索/传播 | 隔离的问题 |
|---|---|---|---|
| random | 默认(0,0)，无历史 | 随机未见全配置，已付费的综合产物可复用 | 无模型、无检索 |
| gp_single | 默认，无历史 | GP综合→TPE放置，只传播最佳综合父 | BO相对随机；名称不是所有阶段都GP |
| ast_single | 三个AST分数等权、完整donor参数 | 同上 | 相对无检索BO的结构warmstart效应 |
| numeric_single | AST节点/边/宽度计数向量距离 | 同上 | 复杂hash签名是否胜过简单计数 |
| text_single | design_description的TF-IDF | 同上 | 简单文本检索；无LLM |
| fusion_control_single | 文本前2→文本+AST等权 | 同上 | 确定性融合；不是AstroTune完整PhaseI |
| ast_tournament | AST warmstart | GP/TPE、多父、动态baseline、首次子线程5%阈值剪枝 | 相对单父的机会分配变化 |
| ast_tournament_no_prune | 同上 | 同多父调度，关闭剪枝 | 剪枝是否真正发生并解释收益 |
| ast_gp_all | AST warmstart | 单父，各阶段GP | 统一GP与阶段异质模型 |
| ast_tpe_all | AST warmstart | 单父，各阶段TPE | 统一TPE与阶段异质模型 |
| random_inclusive | 无历史 | 随机72次阶段调用 | 对齐一次使用的全部54次历史库准备+18次在线调用 |

三个主目标×10种方法×3种搜索种子，共90组；每组18次阶段调用。另一个divider压力目标×4种方法×3种子，共12组，单独标记、不能与原三例平均。它在原小电路结果平坦后前瞻加入，保留原全部零收益结果。inclusive random在三主目标各3种子，压力目标仅1种子：这是成本诊断，不给单种子置信结论。额外donor转移矩阵与确定性复测属于审计预算，绝不回填搜索。另有1组18次预算窄阈值prune_probe，只作真实剪枝分支覆盖，不是性能arm；不能把其后验策略选择与主实验混报。

## 什么被匹配，什么未被匹配

- 在线主实验：每次真实综合+STA是1次阶段评估，每次真实placement/STA是1次；初始默认参考、warmstart、子线程首评估全部计费。每组fresh EDA执行，无跨run QoR缓存。复用本run已付费父网表不新增综合执行；随机方法享有相同权限。unique full configurations按(s,p)计，unique synthesis按s计；另报网表哈希，避免把等价配置当独立电路。
- 历史库：3个donor各18次，共54次阶段调用。它固定在目标搜索之前，每个检索方法都读取同一份选中参数；不通过目标结果选库。一次使用的保守inclusive成本是72次。random_inclusive实际得到72次在线阶段调用，而非仅把数字加到账本。多目标摊销时该54次可以一次计入整个项目，但不能假设历史免费。
- CPU与时间：工具每次1线程；记录真实subprocess与搜索墙钟，GP/TPE额外开销为搜索墙钟减EDA墙钟。检索初次运行不在搜索stopwatch内，因此单独重新测量，明确标记remeasured；全额history墙钟加该次测量只是inclusive估计，**不声称精确端到端墙钟匹配或2×加速**。下载/解包/模型失败尝试时间没有完全instrument，不隐藏该限制。
- 原论文预算：七阶段每阶段20次、并行线程/剪枝与历史生成总机会数未公开，无法精确复刻。本地统一18次总阶段预算是有意设计的可比机会预算，不是作者默认轮数。一个放置调用与一个综合调用成本也不同，所以调用匹配不能替代CPU秒匹配；分阶段耗时与次数均保留。
- 功耗与正确性：功耗默认活动率估计；无VCD、无routing寄生、无signed-off PPA。最终QoR必须使用同一默认完整流程参考值，不能每方法以自己的warmstart再归一后直接比较。观察到的细小差异受工具功耗报告有效位数限制。

## 预先避免的错误解释

重复相同确定性EDA得到相同指标不算新的统计种子；三个搜索种子也不是三个独立设计。小样本不做显著性包装。多父方法和单父方法的综合/放置调用分布可能不同，表中明确保留，不能因候选数更多便称更智能。没有在线LLM时，text/fusion的收益或失败均不证明LLM效用。没有剪枝事件时，不声称剪枝带来速度或QoR收益；无剪枝对照与其相同正是可报告结果。

原文BO、Optuna、FlowTuner、CROP、LLM Search、logfile-aware LLM Search均没有在此被等同复现；我们实现的是较小、明确的算法对照。原表格面积/功耗/WS/分钟全部Not Replicated。

## 实际结论

主三设计所有10种方法、每种3个搜索种子的最佳QoR一致；额外72次随机机会没有改善这些已达到的小空间结果。较大的divider压力层（1320–7136映射单元）仍未出现AST多父优势，且所有解都有约4.45ns时序违例。不能把这种结果称为复现了论文的14%/2×。

事后donor配置迁移审计显示，AST为divider选的multi_pipe4配置QoR104.506767531，劣于默认104.494734490，也劣于adder8 donor的104.464037266。结构相似在此不是配置可迁移性的充分条件。barrel的最佳donor反而是功能不同的adder8，进一步说明功能HR和调参收益应分别测量。原始矩阵、选择规则与regret见`results/transfer_audit.json`。

四个目标各两次独立真实重复中，默认配置area/power/slack及网表哈希完全一致；这8条placement记录与对应8次synthesis属于16次确定性复测，不算8个新随机种子。配置空间72项、部分映射别名及功耗报告精度，也限制了本批小幅收益的解释空间。

**GP修订完成结果**：新24组408次真实调用全部成功（20×8次且每组≤3/6综合候选，4×62次历史成本匹配随机），0 EDA缓存命中；28条acquisition回放匹配，40次ID重排回归通过。累计3092次尝试/3088成功/4旧失败；v1/v2不混合。divider中部分修正GP arm胜过8次随机，但62次随机达到同样最佳值，n=2不足以归因或推广；multi_pipe8未见稳定优势。完整表及限制见`GP_CORRECTION.md`、`results/gp_fix_summary.md`。

## v3真实布线机制复核

已完成global-route→detailed-route→OpenRCX→显式SPEF回读STA，详见`ROUTING_MECHANISM.md`及`routing_v3/summary.json`。临时反转判断因缺少read_spef被撤回；核验后p9早期/最终均占优，single-parent与top-2同最佳PPA，观察regret0。15次实际工具调用（13成功/2失败，含3次明确额外时序修复校验），约37.74秒；累计3107次EDA尝试。无LLM API，未扩展divider/七阶段或donor泛化，已按负结果停止。
