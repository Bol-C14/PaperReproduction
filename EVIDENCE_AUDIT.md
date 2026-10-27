# Evidence audit

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

**证据等级：算术与本地反例可验证；官方算法结果未复现。** 所有论文来源核验日期 2026-10-27，源清单及取回限制在 `sources/manifest.json`。这里的疑点不等于官方软件存在已验证 bug。

## Reporting ambiguity：归一化和运行/取点配置无法唯一确定

[论文 Figure 6](https://www.csl.cornell.edu/~zhiruz/pdfs/aspen-mlcad2025.pdf) caption 将图中 improvement 定义为 over commercial baseline，但 full ASPEN FIR area 标为 12.7%，Table II 数据相对 commercial 为 29.46%，相对 ROVER 为 12.66%。MCM(7,19,31) delay 标为 22.0%，commercial 分母算出 31.62%，ROVER 分母算出 22.01%。这两组显示值不能由统一的 caption 分母直接复算，但缺少原始 run/point 信息，最终分类为 **reporting ambiguity**；不径称已验证论文错误，也不判断究竟是 caption、标签转录、柱数值、不同运行或 Pareto 取点配置造成。机器计算见 `results/table_ii_arithmetic.json`；不能用这一问题反推实际 RTL 不正确。

Table II 的四个均值由显示的绝对数重算为 24.2244%、12.4261%、16.5108%、6.6540%。与报告均值基本相符（首项显示 24.23% 的微差可由未显示精度造成），不是证实的算术错误。

## 已验证的公式反例，受语义限定

`scripts/rule_audit.py` 由独立固定公式产生 mismatch query。它仅把 unsat 视为该有限位宽模型的通过。未执行论文或 LLM 提供的“证明脚本”。W=1,2,4,8,16,32；15 个 case（包括同公式不同前提），共 90 个 query。69 unsat、21 sat、0 unknown。这不是随机测试，也不是任意位宽的归纳证明。

* shift 合并：若两个 shift counts 都是 W 位、相加会截断，则不普遍等价。8 位反例 x=127,c=1,k=255，左值 0、右值 127。若 counts 是无界非负整数或加法先扩位，该反例不适用。
* bitwise AND/OR 转 scalar MUX：vector mask 与 scalar selector 语义不同。8 位 a=254,b=0,s=1 时 `(a & ~s)|(b & s)` 为 254，但 scalar MUX 为 0。仅限制 s∈{0,1} 仍不够；s∈{0,255} 的 full-mask 前提在本次位宽均通过。
* arithmetic MUX 的 `~b`：对 vector bitwise complement 解释会失败；换成 boolean complement `1-b` 并限制 b∈{0,1} 在本次位宽均通过。

以上是**打印规则在明确 vector 语义下的已验证错误/缺失前提**；官方 MUXAR/DSL 的类型、mask 定义、Z3 scripts 未取得，因此**官方实现是否违反这些前提未知**。常数乘法、factor shift 等抽测规则通过，仅适用于 uniform modular width。混合精度、sign extension、Verilog unsized literals、X/Z、溢出后再扩位均需另行模型。

## 报告歧义与方法限制

1. 提议代理同时产生规则和证明程序。若验证器只检查脚本退出成功，而非可信 parser 重建语义后检查准确的 lhs≠rhs UNSAT，会存在证明目标错配风险。这是方法审查提出的威胁，**没有证据表明官方实现如此处理**。
2. 规则正确不保证 RTL translator、e-graph representation、extraction 或 signed widths 正确；最终 RTL equivalence 是必要独立屏障。本次额外验证实际 emitted RTL 68/68，不能替代官方 Pareto checker logs。
3. Figure 6 同时删改若干组件及规则池，缺 repeated seeds 与 equal EDA budgets；不能区分语言模型能力、规则扩容、adaptive search 和更多候选。需要 factorial controlled comparison。
4. 反复综合选最优可能挑到工具噪声；未提供重复综合/噪声地板。DCT 等微小提升尤其需要配对重跑。
5. e-node costs 是可学习搜索代理。真实综合反馈不等于没有 cost model，也不能证明 additive e-node cost 对共享 DAG、关键路径和 technology mapping 一致。local attribution 的准确性没有本次可核实的 ground truth。
6. 功率可扩展性与实际功率优化不同；本次和主要表格均不提供 power replication。
7. Appendix B 的勾选集合不能复原每次外循环轨迹，也没有每个 Pareto point 的独立 rule subset / cost / RTL 映射。正文与附录对规则适用设计的概括不能充当机器配置。

## 资源、许可证及未跑项

官方 Cornell/NVIDIA publication 已核验；前者含 A/B 附录。未在已检查出版页找到指向 ASPEN 官方代码、RTL、prompt 或数据的 artifact 链接；搜索无定位不能证明它们不存在。对猜测的 cornell-zhang/aspen URL 的 404 也不构成全面不存在证据。ASPEN 代码与 benchmark licenses **未核实**，未复制来历不明的代码。

extraction-gym 上游 MIT license 与 Cargo manifest 已取回，HEAD=903ba0f818b50608fe20ae9e0f03c35cb27bc50a；未执行其代码。egglog v0.4.0 license 已取回；Python PyPI egglog 同名版本不能直接当成论文 Rust egglog 版本，未作这种替换。Z3/yowasp 包许可证来自安装 metadata，见 `sources/dependency_licenses.json`。Yosys 常见 ISC、Z3 MIT、runtime/wasmtime 等仍按各包记录约束；没有声称商业 EDA 或所有 benchmark 可以免费重分发。

未跑：官方 LLM proposal/selection/feedback、官方 egglog extraction-gym flow、商业 synthesis/LEC、ASAP7 PPA、FIR/DCT/Polynomial/Watermark、官方 Figure 6 消融、Figure 7 点集。没有权限审批被拒；shell HTTP 403 是下载通道受限，浏览读取成功，PDF hash 不可得。未申请购买许可证或调用模型 API。

修正回归：`merge_shifts_widened_count` 将 x 和两个 counts 扩展到 2W 位再对 counts 相加并移位，最后截取低 W 位；6/6 位宽 mismatch UNSAT。脚本对每个 case 的 expected SAT/UNSAT 作断言，意外变化会失败。MUX fullmask 与 arithmetic boolean-complement 的修正也有可执行断言。原文没有在已取得的 Table I/IV 文本中给出足以确认上述 vector/Boolean 解释的完整 MUXAR 类型定义，因此这些回归约束是本次独立模型，不能倒推官方使用了相同语义。

复算定位和手工值：Table II 在 PDF 第 5 页（论文 §IV），Figure 6 在 PDF 第 6 页。`sources/figure6_labels.csv` 是从浏览工具的 PDF 文本提取结果手工转录的两个 full ASPEN 标签，不是原始绘图数据；没有完成独立像素级校对。FIR area 公式 `100*(1-169.52/240.31)=29.4578%`（commercial）与 `100*(1-169.52/194.10)=12.6636%`（ROVER）；MCM(7,19,31) delay 为 `100*(1-316.12/462.33)=31.6246%` 与 `100*(1-316.12/405.34)=22.0111%`。原始小数未知，±0.005 的显示取整通常不能解释这些差距，但不同 runs/约束可以，所以不能唯一归因。此处是单 benchmark 比率，mean/geomean 不适用；Table II 平均行另算 arithmetic mean of per-benchmark ratios、geometric mean of ratios 与 ratio of sums，结果见 `results/reporting_ambiguity.json`。后两者不是同一种估计量，不能相互替代。Figure 6 是否与 Table II 共用 seed、pool、constraints 与相同的单目标 Pareto minima 未知，联合最优也不能凭单列 minima 推得。

## 第一阶段交付计数与预算口径（历史口径）

90 项是 **15 个语义 case × 6 个有限位宽的回归 obligations**，不是 90 条规则均等价：69 个 mismatch UNSAT、21 个预期反例 SAT、0 unknown，90 个 expected-result assertions 全部通过。SAT 仅说明明确建模语义下可产生反例，不能泛指官方实现错误。最终 pilot 有 68 个不同候选，表达式 Z3 68/68、实际 Verilog miter SAT 68/68 通过。

180 个 offline replay sessions = 6 tasks × 10 seeds × 3 methods，各 4 次查询，合计 720 次**逻辑查表查询**；这些没有额外运行 EDA。开发记录是两轮各 68 次候选综合=136 次，另 68 次 RTL SAT 与 3 次 smoke（1 次输入路径失败），合计 207 次研究/诊断 EDA invocations；不把版本查询算作综合。第一轮 raw logs 被第二轮替换，不能从当前原始日志完整重算所有开发耗时。最终候选 sweep wall time 9.686 秒仅为该轮，不是端到端研究成本。

4-query budget 仅计目标响应，不含候选生成、全部候选结构特征提取、全池特征标准化、回归拟合或策略 CPU 时间。全部候选已离线综合构成 oracle；oracle labels 用于查表响应/事后评价，选择器只看到已查询 labels，但池结构和全部候选特征事先可见（transductive 固定池设定）。特征深度修正后使用同一个池重跑一次，开发代价计入 136 次综合。没有进行测试集调参搜索，也没有报告包含这些开销的在线 wall-time 竞争力。故 equal-query 不是 equal-total-compute。
