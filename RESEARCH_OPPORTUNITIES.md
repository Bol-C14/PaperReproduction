# Research opportunities and falsification pilots

**优先级：可信语义验证与可比预算 > 更换更强 LLM。** 以下是本次可执行或待资源解除后的研究假设，不预设正结果。

## H1：离线可复用常数重写能解释一部分收益

已跑。三个 MCM、两种位宽、四种表达式模式，共 68 个 verified 候选；无需在线模型就能改变 generic gate count。binary 全套在 6/6 task 优于原始乘法；signed 全套在 (7,19,31) 两个位宽优于 binary，但在另外四 task 更差。partial 全套有 5/6 task 比原始差。支持“规则/表达式选择本身重要”，不支持“所有看似便宜的展开都更好”。见 `results/hypotheses.json`。

**Go**：在官方相同池中加入 cached/offline proposed rules，提议成本单列，并把 signed forms 和共享中间项显式建模。**No-Go**：把本次门数收益等同于论文商业 PPA 或宣称无需 LLM 即达到 ASPEN。缺 full e-graph 与真实 mapping，无法决定这部分解释比例。

## H2：数值学习可以替代昂贵的在线语言反馈

已跑。ridge-LCB 只看到已查询响应、同 warm start、相同每 task 4-query budget、10 seeds。在 6 task 描述性均值上 random=0.821665、structural=0.759625、ridge=0.763258（normalized best gates，低为好）。ridge 比 random 好，但未超过固定启发式，**未支持“学习更优”假设**。没有观察到足够证据 justify 更贵/更复杂模型。

**Go**：若官方工具可用，比较同池在线 ridge/GP/Thompson sampling 与 LLM，先固定 20 个 unique synthesis calls 的小预算；超参不依据测试集调整，seed/task 为配对单位。保留失败、成本与首次发现 Pareto 点的曲线。**No-Go**：现在扩大模型参数搜索以追求正结果，或把本次 ridge 称为 BO 最强 baseline。

## H3：可信重建证明目标能阻止语义前提丢失

已跑语义检验。90 个 query 暴露 wrapped shift-count、vector mask/scalar MUX、bitwise/boolean complement 的区别；加入明确正确的前提/语义后相应公式可通过。本次所有 68 候选又通过实际 RTL SAT，避免仅验证手写 AST 而漏掉转译器。

**Go**：建立 typed rule schema（width、signedness、guard、count sort、MUX definition），由可信代码重建两端；接受条件仅为 mismatch UNSAT，unknown/timeout 失败关闭。对每个最终 Pareto point 生成独立 RTL certificate/hash。**No-Go**：根据这些反例指控官方软件存在未证实漏洞。

## 后续最有价值的因果实验

固定共享 e-graph、工具、正确性约束与预算，做 rule pool initial/expanded × selection random/heuristic/LLM × extraction static/numerical/LLM 的受控矩阵；先小规模筛选后扩展，避免一次跑全矩阵。在同一次实现上记录 area/delay/power、可行约束和 point ID，使用 paired Pareto hypervolume 或 fixed-delay area，不拼接独立 minima。把 proposal tokens、每个分区 prompt tokens、cache、失败率、等价检查次数、EDA calls、CPU wall time、已知付费费用和未知费用都列出。

最小放行资源：官方 commit+license、RTL hashes/params、工具/PDK/constraints、prompts、cost update/partition 配置、sample runs、预算与 seed。论文模型无免费额度仍是完整复现 No-Go；可继续免费工具的机制研究，但始终分开报告。

## 交付计数与预算口径（最终一致性说明）

90 项是 **15 个语义 case × 6 个有限位宽的回归 obligations**，不是 90 条规则均等价：69 个 mismatch UNSAT、21 个预期反例 SAT、0 unknown，90 个 expected-result assertions 全部通过。SAT 仅说明明确建模语义下可产生反例，不能泛指官方实现错误。最终 pilot 有 68 个不同候选，表达式 Z3 68/68、实际 Verilog miter SAT 68/68 通过。

180 个 offline replay sessions = 6 tasks × 10 seeds × 3 methods，各 4 次查询，合计 720 次**逻辑查表查询**；这些没有额外运行 EDA。开发记录是两轮各 68 次候选综合=136 次，另 68 次 RTL SAT 与 3 次 smoke（1 次输入路径失败），合计 207 次研究/诊断 EDA invocations；不把版本查询算作综合。第一轮 raw logs 被第二轮替换，不能从当前原始日志完整重算所有开发耗时。最终候选 sweep wall time 9.686 秒仅为该轮，不是端到端研究成本。

4-query budget 仅计目标响应，不含候选生成、全部候选结构特征提取、全池特征标准化、回归拟合或策略 CPU 时间。全部候选已离线综合构成 oracle；oracle labels 用于查表响应/事后评价，选择器只看到已查询 labels，但池结构和全部候选特征事先可见（transductive 固定池设定）。特征深度修正后使用同一个池重跑一次，开发代价计入 136 次综合。没有进行测试集调参搜索，也没有报告包含这些开销的在线 wall-time 竞争力。故 equal-query 不是 equal-total-compute。
