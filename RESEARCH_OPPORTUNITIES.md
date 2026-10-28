# Research opportunities and falsification pilots

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

## 当前主要结论：行为部分复现 / Go

成功标准已调整为可观察行为，不要求复刻原始PPA数值。真实native egglog重写、e-graph抽取、免费Yosys综合反馈、局部cost更新/回退、再次抽取和实际RTL SAT闭环已运行；在线LLM及netlist K-way partition/归因仍未复现。完整逐模块契约、替代假设、命令、预算和失败记录见 **BEHAVIOR_CONTRACT.md** 与 configs/behavior_contract.json。原数值Not Replicated是次级对照，不是行为工作停止理由；上一阶段68候选枚举/180回放仍是独立pilot。

本阶段：3个受控8位fixture × pool/selection/cost三因素各2级 × 2个确定性重复标签 = 48会话，每会话7次真实综合与7次RTL SAT。factorial336 + 起步pilot7 + Figure4探针3 = **346次综合、346次SAT**；无offline target oracle、无cache；第一阶段207 EDA调用单列，合计899。0/1不是独立随机种子，24/24复跑指标相同。每个因素对照固定其他因素与初始构造程序、宽度、工具、正确性和真实综合预算。结构/抽取/控制器时间及约70.81s会话wall已保存，安装、一次性规则检查、最终汇总/绘图和研究平台用量单列，不宣称equal-total-research-cost。第一阶段90义务=69 UNSAT+21预期SAT；新增proposal验证另有51个有限义务UNSAT，不能合称“所有规则均正确”。

关键结果：MCM expanded pool加cost反馈146→130门；FIR-style cost反馈162→158门；x×11 best仍59门；本选择启发式无收益。pool扩展与反馈有交互，不能将收益归于LLM。Figure4三种成本设置确实抽出原乘法/完全展开/部分展开三类表达式，但本地门数为59/57/61，未重现论文面积排序。Figure4静态MUL10还优于本有限预算在线controller的门数，反映cost先验/搜索预算限制。20次真实rollback已记录，配对frontier见results/behavior/online_pareto.json与图，未拼接独立最优。

来源和blocker修正（已查原文）：第一作者 [zzzdavid.tech](https://www.zzzdavid.tech/) 的ASPEN出版条目仅见paper链接；[NVIDIA出版页](https://research.nvidia.com/labs/electronic-design-automation/publication/deng2025aspen/) 未定位完整artifact链接，故ASPEN完整代码/artifact仍是“未定位”，不是“不存在”。[Coward博士论文](https://samuelcoward.co.uk/assets/pdf/Thesis_Imperial.pdf)印刷p9/PDF30§1.3说明Intel IP限制，印刷p155/PDF176明确ROVER closed-source。**ASPEN§IV-B的ROVER是作者按TableI+fixed e-node cost自建的基线，不是原闭源软件，拿不到原ROVER不妨碍独立重实现这条机制。**

[cowardsa/extraction-gym](https://github.com/cowardsa/extraction-gym)是ROVER extraction testcases的fork，root LICENSE为MIT，不是完整ROVER；[egraphs-good/extraction-gym](https://github.com/egraphs-good/extraction-gym)是ASPEN引用的MIT抽取工具。已安全只读核查源码和converter格式，未执行下载来的Makefile/convert.py；源码算法用于Python适配并保留MIT notice。数据目录浏览返回restricted URL，未换通道绕过，故具体case覆盖、逐文件data声明及与ASPEN七个benchmarks的关系未核实，未使用这些数据跑结果。Rust编译器缺失不阻断免费wheel路径：Python egglog14.0.0实际可用，版本替代明确，不冒充Rust0.4.0；12个native/Python tree成本场景一致。模型实际预检未发现torch/transformers/模型权重，未核实任何免费API额度、未检查凭证或调用API，确定性proposal replay和控制器仅为非在线LLM对照。

下一步Go：继续在免费算术域检验真实e-graph规则池/固定cost/random或数值策略、扩展可验证fixtures和归因代理；无需等待闭源ROVER。仍需补齐通用RTL前端、MUXAR类型前提、公开真实benchmark数据许可/覆盖、在线LLM能力和netlist分区归因。商业ASAP7/指定付费模型只限制原数值对照，不阻止行为复现。

## 第一阶段：保留的次级数值对照与离线pilot

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

原数值复现最小放行资源：官方 commit+license、RTL hashes/params、工具/PDK/constraints、prompts、cost update/partition 配置、sample runs、预算与 seed。论文模型无免费额度仍是完整复现 No-Go；可继续免费工具的机制研究，但始终分开报告。

## 第一阶段交付计数与预算口径（历史口径）

90 项是 **15 个语义 case × 6 个有限位宽的回归 obligations**，不是 90 条规则均等价：69 个 mismatch UNSAT、21 个预期反例 SAT、0 unknown，90 个 expected-result assertions 全部通过。SAT 仅说明明确建模语义下可产生反例，不能泛指官方实现错误。最终 pilot 有 68 个不同候选，表达式 Z3 68/68、实际 Verilog miter SAT 68/68 通过。

180 个 offline replay sessions = 6 tasks × 10 seeds × 3 methods，各 4 次查询，合计 720 次**逻辑查表查询**；这些没有额外运行 EDA。开发记录是两轮各 68 次候选综合=136 次，另 68 次 RTL SAT 与 3 次 smoke（1 次输入路径失败），合计 207 次研究/诊断 EDA invocations；不把版本查询算作综合。第一轮 raw logs 被第二轮替换，不能从当前原始日志完整重算所有开发耗时。最终候选 sweep wall time 9.686 秒仅为该轮，不是端到端研究成本。

4-query budget 仅计目标响应，不含候选生成、全部候选结构特征提取、全池特征标准化、回归拟合或策略 CPU 时间。全部候选已离线综合构成 oracle；oracle labels 用于查表响应/事后评价，选择器只看到已查询 labels，但池结构和全部候选特征事先可见（transductive 固定池设定）。特征深度修正后使用同一个池重跑一次，开发代价计入 136 次综合。没有进行测试集调参搜索，也没有报告包含这些开销的在线 wall-time 竞争力。故 equal-query 不是 equal-total-compute。
