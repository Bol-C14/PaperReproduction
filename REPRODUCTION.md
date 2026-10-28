# ASPEN (MLCAD 2025) reproduction

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

**结论：Partially Replicated；完整论文结果 No-Go，免费机制 pilot Go。** 本分支位于统一仓库 Bol-C14/PaperReproduction 的 `reproduction/aspen-mlcad2025`，没有新建远端仓库、推送或 PR。这里没有把重建的 MCM 小例子称为完整 ASPEN 复现。

## 复现契约与实际范围

机器可读契约：`configs/reproduction_contract.json`；资源证据：`logs/environment.json`、`sources/manifest.json`。

| 主张 | 判定 | 实际证据 / Go-No-Go |
|---|---|---|
| Table II 原始数值及平均提升可计算 | Replicated（仅算术） | `sources/table_ii.csv` → `results/table_ii_arithmetic.json`；Go |
| Table II 商业 EDA/ASAP7 端到端指标 | Not Replicated | 缺指定商业流程、官方 RTL/脚本、模型及调用记录；No-Go |
| Figure 6 消融及独立因果贡献 | Not Replicated | 无原始 runs；存在分母/取点配置的 reporting ambiguity；No-Go |
| Figure 7 官方 Pareto 点集 | Not Replicated | 无逐点 area/delay/RTL；不能由两列最小值重建；No-Go |
| 提议规则的位向量语义 | Partially Replicated | 独立 Z3，90 项检查，69 unsat、21 sat、0 unknown；只覆盖列明语义及规则子集；Go |
| 重写后实际 RTL 等价性 | Replicated（本地替代 pilot） | 68/68 Yosys SAT；不是官方候选；Go |
| LLM 比简单搜索更有效 | Not Replicated | 没有调用论文模型；数值学习对照未优于启发式；No-Go |

这些标签不意味着官方声明已被证伪。数值算术、公式语义、原始运行和替代实现是四类不同证据。

## 环境核查与可恢复性

从空仓库、无提交的 `work` 分支创建 orphan 目标分支，未覆盖任何已有文件。`/workspace` 与仓库内未发现 AGENTS.md 或本地 `.agents/skills`；父目录只做了只读检查。实际 Python 3.12.14，CPU affinity 5，MemTotal 18,440,112 kB（约 17.59 GiB），磁盘约 29.6 GiB 可用，无 NVIDIA 设备、无 cargo/rustc/原生 Yosys/商业综合或等价工具。RAM 不同于先前约 33 GiB 报告，不能把草稿环境当成本次事实。

已在 `.venv` 安装锁定的免费 binary wheels：Yosys WASM 0.50（b5170e139）和 Z3 4.13.4。版本、依赖和 wheel hashes 见 `configs/requirements.lock`、`configs/wheel-sha256.txt`。没有修改凭证、安全配置或调用付费 API。没有可验证的已发布环境快照/先前 EDA 安装，因此不能宣称恢复了旧环境；本次基础 Python 加隔离依赖可以重建。

## 算法和配置核对

官方材料：[Cornell PDF（含附录 A/B）](https://www.csl.cornell.edu/~zhiruz/pdfs/aspen-mlcad2025.pdf)、[NVIDIA publication](https://research.nvidia.com/labs/electronic-design-automation/publication/deng2025aspen/)。完整审计见 EVIDENCE_AUDIT.md；报告配置与未报告字段见 `configs/paper_reported.json`。

论文流程为：一次性提议规则并验证；外循环选择规则子集，egglog 饱和；每次外循环初始化 e-node costs=1；内循环抽取、RTL 转译、综合、netlist 分区、反馈增减局部成本，可按历史回退；最终 Pareto RTL 另行等价检查。论文报告 egglog 0.4.0、extraction-gym greedy/bottom-up、o3-20250416 提议与 gpt-4.1-20250414 选择/反馈；综合 effort=high。缺少外/内循环次数、步长、seed、温度、prompt、分区配置、具体 EDA 版本及完整约束，不能自行补齐并称忠实复现。

## 实际运行的 pilot

`configs/pilot.json` 固定三个 MCM 常数组、W=8/16、所有中间值/输出 W 位无符号模运算。四种表达式模式：原始乘法、平衡 binary shift-add、signed-digit、一次 partial unfolding。每任务最多 12 个组合，生成 seed=42，去重后共 68 个。这是有界表达式枚举，**没有完整 e-graph、egglog 饱和、LLM、netlist tracing 或 ASAP7 technology mapping**。

每候选先独立 Z3 验证表达式，再用 Yosys `synth -top top -noabc`，解析 generic combinational gates 和拓扑深度；另外把实际 Verilog 与独立参考乘法 RTL 做 miter SAT。采用 -noabc 是明确的替代流程配置，不是商业综合的近似等同物。不同门型不加权，深度不含物理延时、扇出、布线或 clock 约束。

| MCM | W | 原始门数 | binary | signed | partial | 最佳门数 |
|---|---:|---:|---:|---:|---:|---:|
| 3,7,21 | 8 |124|101|105|120|96|
| 7,19,31 | 8 |146|122|103|179|103|
| 5,93 | 8 |80|63|77|91|63|
| 3,7,21 |16|391|315|342|410|315|
| 7,19,31 |16|474|412|340|604|340|
| 5,93 |16|326|240|314|355|240|

同池 offline replay：random、固定结构启发式、ridge-LCB，全部以原始 RTL 加同 seed 的随机候选 warm start，各 4 次无重复查询，10 seeds × 6 tasks。oracle 已离线测量，用于回放与事后 gap；模型选择过程中只使用已查询候选的响应，不能把 720 次回放查询记为额外真实综合。结果见 BASELINE_COMPARISON.md。本地图：`results/pilot_pareto.png`、`results/search_comparison.png`；它们不对应论文 Figure 6/7 的数值。

## 重建

在仓库根目录：

```bash
python -m venv .venv
.venv/bin/pip install --only-binary=:all: -r configs/requirements.lock
python scripts/environment.py
python scripts/reporting_audit.py > logs/reporting_audit.log
.venv/bin/python scripts/rule_audit.py > logs/rule_audit.log
.venv/bin/python scripts/pilot.py > logs/pilot.jsonl
.venv/bin/python scripts/verify_rtl.py > logs/rtl_equivalence.log
MPLCONFIGDIR=$PWD/.cache/matplotlib XDG_CACHE_HOME=$PWD/.cache python scripts/analyze.py > logs/analysis.log
```

分析/绘图使用预装 numpy 2.3.5、matplotlib 3.10.8（单独锁定见 configs/analysis-requirements.txt）。WASM 只映射当前目录，输入使用相对路径；最初 `/tmp` 输入 smoke 失败，已保留日志。每次候选综合 timeout=60s，Z3=5s；没有运行未知来源 shell 或模型生成的证明程序。

## 成本、运行及保存

最终 68 个候选的综合及表达式证明 wall time 见 `results/pilot_execution.json`；SAT 时长逐项在 `results/rtl_equivalence.json`。首次 68 候选 sweep 后修正了结构特征深度计算（共享节点的 visited 处理），完整重跑一次，因此开发过程共 136 次候选综合、136 次候选 Z3 checks、68 次额外 SAT、90 项规则检查；另有 3 次 smoke 调用（其中一次路径失败）。首次 sweep 日志被最终 sweep 替换，计数/原因在 `logs/run_history.json`，不能把最终 suite 时间冒称总研究时间。LLM 调用=0，token=0，新增付费成本=$0；平台已有运行资源的价格未知，没有估算为零。

Git 只保留小型源码、RTL、logs、metrics、图与 manifest，不纳入虚拟环境、wheel cache、PDF 或生成 netlists。netlist 可由脚本重建，逐项 hash 已记录。官方 PDF 的 shell 下载为 HTTP 403，没有 PDF 字节或可信 hash；不伪造 hash。浏览读到的版本未与 IEEE 字节版本校验。完整复现应在取得官方 artifacts 与合法免费可用工具/预算后另行放行。

## 第一阶段交付计数与预算口径（历史口径）

90 项是 **15 个语义 case × 6 个有限位宽的回归 obligations**，不是 90 条规则均等价：69 个 mismatch UNSAT、21 个预期反例 SAT、0 unknown，90 个 expected-result assertions 全部通过。SAT 仅说明明确建模语义下可产生反例，不能泛指官方实现错误。最终 pilot 有 68 个不同候选，表达式 Z3 68/68、实际 Verilog miter SAT 68/68 通过。

180 个 offline replay sessions = 6 tasks × 10 seeds × 3 methods，各 4 次查询，合计 720 次**逻辑查表查询**；这些没有额外运行 EDA。开发记录是两轮各 68 次候选综合=136 次，另 68 次 RTL SAT 与 3 次 smoke（1 次输入路径失败），合计 207 次研究/诊断 EDA invocations；不把版本查询算作综合。第一轮 raw logs 被第二轮替换，不能从当前原始日志完整重算所有开发耗时。最终候选 sweep wall time 9.686 秒仅为该轮，不是端到端研究成本。

4-query budget 仅计目标响应，不含候选生成、全部候选结构特征提取、全池特征标准化、回归拟合或策略 CPU 时间。全部候选已离线综合构成 oracle；oracle labels 用于查表响应/事后评价，选择器只看到已查询 labels，但池结构和全部候选特征事先可见（transductive 固定池设定）。特征深度修正后使用同一个池重跑一次，开发代价计入 136 次综合。没有进行测试集调参搜索，也没有报告包含这些开销的在线 wall-time 竞争力。故 equal-query 不是 equal-total-compute。
