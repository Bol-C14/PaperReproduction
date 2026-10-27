# Baseline comparison

**完整 ASPEN vs ROVER 比较 Not Replicated / No-Go。替代机制比较已执行 / Go。**

## 原论文的比较对象

[ASPEN §IV-B / Figure 7](https://www.csl.cornell.edu/~zhiruz/pdfs/aspen-mlcad2025.pdf) 将其 ROVER baseline 描述为 Table I rules 加固定 costs 的自有复现。原 [ROVER paper](https://arxiv.org/abs/2406.12421) 包括 mixed-precision rewrite、area model 与 ILP extraction。两者不能直接视为同一官方实现。ASPEN 多点搜索与 baseline 单点的差异同时改变搜索机会；没有可比的 synthesis-call/wall-time/token 预算，无法把收益归于 LLM 本身。

Table II 的 ASPEN area 和 delay 是分别取 Pareto 最小值，必须报告对应的两个 implementation IDs；不能把独立 minima 拼成一个优于 baseline 的点。实际 Figure 7 原始点缺失；仅凭 Table II 不能核实逐点支配关系、hypervolume、可行频率或面积约束下的最佳延时。

## 本次统一约束对照

同一手写有限规则/表达式池、相同输入位宽、同一 Yosys 配置、同样正确性约束，全部候选 68/68 Z3 和 RTL SAT 通过；没有任何在线/离线付费 LLM。所有策略只在同任务候选集合内选择。

| 方法 | 选择规则 | 响应使用 | query budget |
|---|---|---|---:|
| random | 无放回随机 | 不使用响应决策 |4|
| structural | 3×MUL + ADD + SUB 的固定唯一节点成本，shift 免费 | 不使用响应决策 |4|
| ridge_lcb | 标准化节点计数+表达式深度，ridge=1，LCB 系数=.25 | 仅已查询门数 |4|

每种方法每任务 seed=0..9，原始候选与相同随机 warm start 共占前两次预算。候选标准化只使用结构特征、不使用未查询目标值；ridge 每次重新拟合，既不是 LLM，也不是已验证最优 BO/bandit 系统。没有做超参数搜索。结构启发式 tie 用候选 index；random warm start 对该方法也会消耗预算，所以该实验比较的是明确的混合 warm-start 策略。

| 方法 | 平均 best gates / 原始 gates ↓ | 平均与池内 oracle 差距 ↓ |
|---|---:|---:|
| random |0.821665|0.067282|
| structural |0.759625|0.005242|
| ridge_lcb |0.763258|0.008875|

6 个任务各 10 seeds 的描述性均值，数据见 `results/search_aggregate.json`，逐 query 日志见 `results/search_queries.json`。tasks 高度相关、数量少，不能当 60 个独立设计样本做显著性主张。数值学习未优于固定启发式，因此这里不支持学习一定优于规则知识的假设。没有把 gate count 换算成 μm²，逻辑深度没有换算为 ps。

本次先测量全部 68 个候选作为有限 oracle，再进行 180 个搜索 session 的回放，共 720 逻辑查询；实际综合计费不是 720 次。此设置可审查 equal-query 行为，但不包含在线工具启动/LLM latency，也不证明大 e-graph 下的可扩展性。深度最小值和门数最小值同样独立；配对 Pareto 图保留实际对应候选。

## 下一阶段合格比较

固定官方 benchmarks、合法工具/PDK、位宽/符号/约束、共享规则池与 e-graph；允许每策略相同的 unique synthesis calls、timeout、重复 seed 与总 wall time。分别比较 original-only/expanded pool，random/heuristic/ridge/bandit，静态抽取/数值反馈/LLM feedback。记录 rule proposal 一次性成本和 amortization、每分区 token、等价失败/timeout、重复 RTL/cache hits、Pareto verified points 与 paired bootstrap。预算在看结果前固定；无免费论文模型额度时，完整 LLM arm 保持 Not Replicated，不能偷偷替换模型。

## 交付计数与预算口径（最终一致性说明）

90 项是 **15 个语义 case × 6 个有限位宽的回归 obligations**，不是 90 条规则均等价：69 个 mismatch UNSAT、21 个预期反例 SAT、0 unknown，90 个 expected-result assertions 全部通过。SAT 仅说明明确建模语义下可产生反例，不能泛指官方实现错误。最终 pilot 有 68 个不同候选，表达式 Z3 68/68、实际 Verilog miter SAT 68/68 通过。

180 个 offline replay sessions = 6 tasks × 10 seeds × 3 methods，各 4 次查询，合计 720 次**逻辑查表查询**；这些没有额外运行 EDA。开发记录是两轮各 68 次候选综合=136 次，另 68 次 RTL SAT 与 3 次 smoke（1 次输入路径失败），合计 207 次研究/诊断 EDA invocations；不把版本查询算作综合。第一轮 raw logs 被第二轮替换，不能从当前原始日志完整重算所有开发耗时。最终候选 sweep wall time 9.686 秒仅为该轮，不是端到端研究成本。

4-query budget 仅计目标响应，不含候选生成、全部候选结构特征提取、全池特征标准化、回归拟合或策略 CPU 时间。全部候选已离线综合构成 oracle；oracle labels 用于查表响应/事后评价，选择器只看到已查询 labels，但池结构和全部候选特征事先可见（transductive 固定池设定）。特征深度修正后使用同一个池重跑一次，开发代价计入 136 次综合。没有进行测试集调参搜索，也没有报告包含这些开销的在线 wall-time 竞争力。故 equal-query 不是 equal-total-compute。
