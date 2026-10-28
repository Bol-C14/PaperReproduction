# 行为复现契约（当前主要成功标准）

## 最新有界机制轮次：归因/双向cost/后继rollback已补齐，但无稳定优势

详见ATTRIBUTION_ROUND.md、configs/attribution_round.json和全部新日志results/attribution_round、logs/attribution_round。先检查原环境可恢复（egglog/Z3、5CPU、约17GiB），无LLM API、新安装或付费。只在预设64次综合硬上限内推进：4次pilot、48次完整对照、5次被裁剪FIR，共57 synthesis+57生成RTL-to-reference SAT；114条真实EDA ledger、工具失败0。此前941条另计，全任务可审计计数1055。

cell src归因路线实测0覆盖，已裁剪；替代为保留命名运算wire的门级fan-in边界锥，共享cell均分，属于启发式而非因果边际面积。FIR在固定策略第5点丢失3/7运算边界（仅57.14%），按先行门槛停止，保留其346门/depth24的失败归因点和全部花费；以前瞻提交3a5a66c记录有界修订，用预先列出的MCM(5,93)W16替代完整对照，未运行剩余FIR策略。

两个完成条件为MCM71931 W12与MCM593 W16，每臂固定6次真实综合/SAT、同冻结图、同规则池/宽度/工具、同有界next-best去重约束。57次共28份unique tagged RTL，所有完整臂6/6无重复；不等于28份独立硬件结构。均已保存原始代表JSON网表、实际候选/配对depth和重算脚本。归因、cost增加/下降和rollback的纯抽取干预测试均改变后继；实际数值策略8项上调、4项下调、9次rollback（7次非终止），其中2次确实改变执行的下一条新候选，反事实只做抽取而未额外综合。

外部best/最后candidate门数：W12 fixed237/237、random266/341、numerical217/355、open-loop217/237；W16 fixed326/355、random326/402、numerical326/340、open-loop326/355。数值策略best只追平开放环，且W12最后更差；W16全未改善基线。**本轮完成机制验证和受控比较，但不支持数值归因策略有稳定质量优势。** 一个seed、小型构造，不泛化为LLM/ASPEN优劣。best是统一会话后评估，不是开放环或数值策略偷偷返回的最佳RTL。

当前新替代策略已实现显式双向cost和有后继作用的rollback；下文旧轮次“未实现cost下降”仅指旧策略。LLM和原论文K-way归因仍未实现。SAT仍只证明生成RTL对reference，而非综合网表等价；gate/depth不是商业PPA。锥覆盖/命名边界可能丢失，失败已暴露而未强行修成正结果。到此停止本轮，不开新sweep。

## 此前轮次记录（原样保留范围与历史计数）

## 最新因果审计：开放环对照未显示response增益

预注册提交297cfc80f338e4d79ebecf40889fbab3a68da22f固定“相同结构节点选择、静态规则、永远+3、不读response、不rollback”的开放环，再新增3会话×7次真实综合及7次RTL SAT，复用既有feedback controls。MCM-expanded两者轨迹均146,146,146,130,146,146,130；FIR-initial均162,162,162,158,162,162,158；x×11均59,59,59,61,59,59,61。最后输出分别为(130,11)、(158,18)、(61,10)；统一外部best-gates为130、158、59（对应depth11、18、11），开放环不使用这些response选择输出。三个条件的逐步RTL hashes亦相同。

因此先前的动态cost-arm收益只支持结构cost扰动有效，不能隔离真实response信息价值。x×11 rollback发生在query4/7之后，下一外循环cost重置或运行结束，本预算未使用分歧cost生成不同候选。详见RESPONSE_VALUE_AUDIT.md、openloop_comparison.json和预注册配置。

原346次综合仅14份byte-level unique RTL，16/48会话仅1份；加入21个新调用后367次仍14份unique，重复率96.19%。预算匹配是实际EDA调用数，不是独立候选数或相同有效搜索机会。累计367 synthesis+367 RTL SAT，734条新阶段ledger；加第一阶段207条合计941。

已纳入14份原始代表网表JSON及调用映射，可用标准库scripts/verify_unique_netlists.py独立重算gate/depth/hash。SAT只证明生成RTL对reference RTL，**没有综合后网表等价证明**。51个proposal义务是手写语义实例，**不是自动证明全部.egg规则**。Algorithm1分区归因、显式cost下降和在线LLM未实现，保持行为partial。

## 先前阶段记录（下列346次等计数为开放环补充前口径）

**结论：核心行为部分复现 / Go。** 已跑通真实 egglog→抽取→Yosys→反馈→再次抽取→RTL SAT；在线 LLM 能力与 netlist 分区/归因没有复现。原论文数值是次级对照，缺商业工具不再是停止行为复现的理由。上一阶段68候选枚举/180回放保留为独立 pilot，不改称 ASPEN。

机器配置：`configs/behavior.json`；逐模块机器契约：`configs/behavior_contract.json`。来源修正在四份报告中一致记录。

| 模块 | 输入→输出 / 状态 | 可观察行为与不变量 | 本次判定 / 替代假设 |
|---|---|---|---|
| Rule Proposal | 初始规则+fixture→扩展规则池；一次性阶段 | 固定 Appendix A replay；51个手写公式/实例义务 UNSAT，未证明全部.egg规则，最终表达式仍另验证 | Partially Replicated；没有在线LLM提议/修复，不能主张发现能力 |
| Rule Selection | 设计+历史真实门数→full/constants_only | 初次full；未改善reference时下一外循环选择constants_only；同池、同起始AST；干预响应可改变选择 | Partially Replicated；确定性两选项启发式，非LLM |
| E-Graph Rewriting | AST+已选规则→真实native egglog e-classes/e-nodes | 3轮有界重写，保留原根等价类、congruence；每次输出完整图快照和原始RunReport | Replicated（所列算术域）；并非全RTL/全TableI或完全饱和 |
| Extraction | e-graph+局部cost→无环表达式/DAG选择 | 正operator cost，leaves=0；bottom-up与greedy-DAG Python适配；12个固定cost场景与native Rust tree extractor成本一致 | Replicated（成本驱动抽取行为）；非原Rust实现速度/全局DAG最优 |
| Synthesis Feedback | 实际RTL→generic gates+depth+JSON netlist | 每一步真的调用Yosys，禁cache；不预先测候选oracle；每会话7次综合（含reference） | Replicated（反馈闭环）；generic指标不等于ASAP7 area/delay |
| Cost Update/History | 响应+selected nodes+history→局部cost和回退 | 每外循环cost重置1；选中MUL优先、否则ADD；+3，差于best时回退快照后+6；真实出现20次rollback | Partially Replicated；局部结构启发式代替LLM netlist attribution，没有K-way partition |
| Equivalence | extracted AST / emitted RTL与独立reference→UNSAT / SAT证书 | unknown/timeout失败关闭；每次综合前Z3、之后实际RTL miter SAT；本阶段346/346通过 | Replicated（8位受控fixtures）；非通用混合精度或任意Verilog保证 |
| Pareto | 同一已验证实现的(gates,depth)→非支配点IDs | 不拼独立minima；完整配对与所有point IDs保存 | Replicated（已观察点的frontier行为）；不保证全局Pareto或原Figure7点集 |

## 实验范围与预算

三个可重跑fixture：论文Figure4的x×11；根据论文常数重建的MCM(7,19,31)；独立编写的3项FIR-style表达式（12,41,21系数）。后两者不是官方benchmark字节，FIR-style不冒充论文FIR；输入为白名单AST，未实现通用RTL前端。W=8，所有中间值/输出模2^8、无符号、无X/Z、无sequential state；shift counts为非负i64常量，避免先前wrapped-count歧义。

Table I实现算术家族：commutativity、双向associativity、identity、distributivity（涵盖表中Estrin形式）、2^1..2^7、奇/偶常数展开、shift simplification、addition balancing；MUXAR因符号/类型前提未明确而排除。规则与局部成本写在 `behavior/table_i_rules.egg` 和源码中；Python egglog 14.0.0是明确版本替代，不能说等于论文Rust egglog0.4.0。底层wheel有MIT元数据，未确认编译的Rust引擎commit。

factorial为 pool(initial/expanded) × selection(static/feedback) × cost(static/feedback)，3 fixtures × 2重复标签 = 48会话，各reference1次+2外循环×3内循环=7真实综合+7真实SAT。因控制器确定性，0/1不是独立随机探索种子，24/24配对复跑指标一致。每个因素的对照固定其余因素、输入图hash、工具、宽度、正确性和真实综合预算；selected rules会有意改变重写后的图。旧字段initial_graph_sha256/initial_graph_hashes实际存的是初始构造程序hash，不是图快照字节hash；在相同native engine和确定性输入下匹配起始图，字段名称不应被误读为序列化图字节证明。静态cost=uniform1，不是未披露系数的原ROVER area model。

本阶段真实计数：factorial336+pilot7+Figure4探针3 = 346 synthesis，另346 RTL SAT；逐调用ledger有692项、退出均成功。第一阶段207 EDA调用单列，全任务可审计计数899；版本查询和native extractor checks不算EDA。参考设计和重复RTL也消耗预算，没有cache。没有训练或离线target oracle。结构选择、graph building、两种extractor、controller计时均保存；48会话总wall约70.81s，包括每步综合/SAT和逐步记录，不含依赖安装、一次性51项rule检查、最终summary/绘图、研究/作者平台LLM用量。实验管线模型调用0、新增付费费用0，平台已有资源价格未知。

## 结果与失败模式

| fixture / pool | static selection + static cost | static selection + feedback cost | feedback selection + static cost | 两者feedback |
|---|---:|---:|---:|---:|
| x×11 / initial |59|59|59|59|
| x×11 / expanded |59|59|59|59|
| MCM / initial |146|146|146|146|
| MCM / expanded |146|130|146|130|
| FIR-style / initial |162|158|162|158|
| FIR-style / expanded |162|158|162|158|

数字是每会话预算内best generic gates，不能替代同一实现的配对深度。48会话逐对效应均值：pool+1.8265%，selection0%，cost+2.6495%；只是小型fixture上的描述性配对结果，没有显著性或LLM结论。扩展池与cost更新存在交互：仅扩展池、uniform cost不改善MCM。selection能改变动作但本策略没有改善best gates，是负结果。

Figure4静态探针的表达式行为得到复现：uniform→x*11（59 gates,11 depth）；global MUL10→全shift/add（57,11）；仅root MUL11 cost4→部分展开（61,10）。两extractor均给出这三类表达式。本地门数排序与论文ASAP7面积排序不同；局部部分展开带来depth/gates权衡。在线controller在x*11看见门数恶化并回退，未达到静态MUL10的57门，说明手工cost先验和有限预算很重要。

一次完整批处理在所有EDA结束后，因反馈干预测试比较了同一cost字典的两个别名而退出1；原traceback保留于 `logs/behavior/factorial.jsonl`。修复为copy-on-update，并仅重做不调用EDA的依赖干预测试，已通过；已有数值决策不变。native/Python tree成本另有12场景交叉验证。额外51项proposal检查是有限模型义务，不与第一阶段90项（69 UNSAT+21预期SAT）混为“全规则正确”。

## 从新运行目录重建

所有网络仅走已允许PyPI；不运行下载来的Makefile/convert.py。不要覆盖审阅包已有日志：

```bash
python -m venv .venv
.venv/bin/pip install --only-binary=:all: -r configs/behavior-requirements.lock
export ASPEN_BEHAVIOR_RUN_ROOT=.runs/rebuild1
.venv/bin/python scripts/behavior_loop.py --pilot
.venv/bin/python scripts/behavior_loop.py --full
.venv/bin/python scripts/analyze_behavior.py
.venv/bin/python scripts/verify_native_extraction.py
MPLCONFIGDIR=$PWD/.cache/matplotlib python scripts/plot_behavior.py
```

绘图的numpy/matplotlib按 `configs/analysis-requirements.txt` 安装到所用Python。新run目录必须未使用；默认审阅结果位于results/behavior、logs/behavior。图快照与原始工具输出为gzip，可解压检查；完整netlists排除Git/ZIP，可按命令重建，hash见每步记录。节点上限10000是在每轮后检查，不是峰值内存硬限制；本次最大1657 nodes，未触发资源上限。

## 下一阶段可执行范围

Go：在当前已验证算术域扩大真实RTL fixtures/位宽，并给static cost不同先验、random cost/rule、数值bandit同预算；先修复/评估归因启发式而非直接换大模型。可复用MIT extraction-gym序列化/算法，但作者fork数据目录本次受限，不能假装已确认完整数据覆盖或逐文件许可证。在线LLM、netlist K-way分区与可信e-node映射仍Not Replicated，需单独补齐。原ROVER闭源只限制原软件的字节级运行；ASPEN自身TableI+fixed-cost基线可独立重建，不应等待原ROVER源码。
