# Evidence audit

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

## 交付计数与预算口径（最终一致性说明）

90 项是 **15 个语义 case × 6 个有限位宽的回归 obligations**，不是 90 条规则均等价：69 个 mismatch UNSAT、21 个预期反例 SAT、0 unknown，90 个 expected-result assertions 全部通过。SAT 仅说明明确建模语义下可产生反例，不能泛指官方实现错误。最终 pilot 有 68 个不同候选，表达式 Z3 68/68、实际 Verilog miter SAT 68/68 通过。

180 个 offline replay sessions = 6 tasks × 10 seeds × 3 methods，各 4 次查询，合计 720 次**逻辑查表查询**；这些没有额外运行 EDA。开发记录是两轮各 68 次候选综合=136 次，另 68 次 RTL SAT 与 3 次 smoke（1 次输入路径失败），合计 207 次研究/诊断 EDA invocations；不把版本查询算作综合。第一轮 raw logs 被第二轮替换，不能从当前原始日志完整重算所有开发耗时。最终候选 sweep wall time 9.686 秒仅为该轮，不是端到端研究成本。

4-query budget 仅计目标响应，不含候选生成、全部候选结构特征提取、全池特征标准化、回归拟合或策略 CPU 时间。全部候选已离线综合构成 oracle；oracle labels 用于查表响应/事后评价，选择器只看到已查询 labels，但池结构和全部候选特征事先可见（transductive 固定池设定）。特征深度修正后使用同一个池重跑一次，开发代价计入 136 次综合。没有进行测试集调参搜索，也没有报告包含这些开销的在线 wall-time 竞争力。故 equal-query 不是 equal-total-compute。
