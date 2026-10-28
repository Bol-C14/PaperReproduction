# P10 资产核查 — Constraint-Aware E-Graph Rewriting for Hardware Performance Optimization

核查日期：2026-10-28。工作目录：所选云环境 `/workspace/PaperReproduction/P10`。仅访问公开论文、作者页面及公开 README/code/config/license；未安装、编译、运行优化器、SAT/SMT、综合、实验或模型推理；无服务 API 调用、登录、许可接受、发布或设置更改。

## 结论与路线分级

| 路线 | 分级 | 置信度 | 判断边界 |
|---|---|---|---|
| 最小忠实机制学习 | **L4：确认原实现未开源，有限范围实现成本低** | 中高；未开源证据高，低成本判断中 | 从作者接受稿实现一个小型、显式位宽的组合表达式子集，贯通上下文约束、值域、条件改写、成本提取与独立等价检查。不是完整 ROVER，也不承诺论文指标。 |
| 完整论文路线 | **L5：确认原实现未开源，完整重建成本高** | 高 | 需重建完整 RTL 流程并核实全部规则、工业 benchmark、商业综合/EC 与工艺库；当前资产不能支持直接复跑。 |

这里的“确认未开源”依据作者博士论文 §1.3（印刷页 9 / PDF 页 30）明确说明工业背景使软件不能开源，而非依据搜索失败；§1.4、§1.5 将约束感知 ROVER 与本篇工作关联到 Chapter 5。[S3] 这是 2025 年作者声明；本次未核实到后续完整公开发行版，不据此断言未来或所有代码均不存在。公开基础库和作者 extraction-gym fork 不能使本篇变为 L1/L2/L3。

L1=代码及直接所需资产齐备；L2=有代码、低成本补齐；L3=有代码、高成本补齐；L4=确认无公开原实现、低成本有限实现；L5=确认无公开原实现、高成本完整实现。

## 论文身份与全文

Imperial 官方记录：[S1]；DOI `10.1109/TCAD.2024.3483096`；作者 Samuel Coward、Theo Drane、George A. Constantinides；在线 2024-10-17；2025-04-01 期刊期次，44(4):1366–1379。仓库列出 `CowardTCAD25.pdf`，约 1.03 MB、14 页、作者接受稿，CC BY 4.0。**已通过阅读工具读取全文，不再停留在摘要。**[S1,S2]

IEEE 页面出现机器人/JavaScript 验证，未继续。云环境直接下载官方 PDF 返回 HTTP 403，未重试或绕过，故没有本地 PDF、校验和或全文文本文件；合法公开全文已由阅读工具呈现，两种访问状态分别记录。作者网站也列出本篇与旧版 ROVER 为独立条目。[S4]

## 机制核对与版本区别

以下为全文要点核对，不是从摘要补写算法：[S2, §III–V]

| 项目 | 已核对机制 | 实现资产状态 |
|---|---|---|
| 上下文/guarded rewrites | ASSUME 编码子域等价，mux 引入并传播条件；值域证明后触发条件或动态改写。 | 原实现未开源；规则补充页被阻断。 |
| 值域 | e-class 上的无符号整数区间并集；按 Verilog 符号及截断语义转换。 | 定义可读；完整 operator transfer functions 未逐项以代码核实。 |
| 延迟成本 | 固定算子架构的二输入门级延迟估计；沿最长组合路径累积。 | 论文模型不等于工艺映射后的 STA。 |
| 提取 | greedy 得到最小模型延迟；CBC 求面积最小且满足延迟约束的无环实现，扫描 Pareto。 | 公式可读；本篇 extractor 原码不可得。 |
| 等价验证 | 输出中间 Verilog 链交给商业 EC；不是已核实的公开 SAT/bitvector 端到端脚本。 | 具体 EC 版本、脚本、超时未核实。 |

旧版《ROVER: RTL Optimization via Verified E-Graph Rewriting》（DOI `10.1109/TCAD.2024.3410154`、arXiv 2406.12421）主要提供混合精度 RTL 改写、面积成本、ILP 与验证链。[S5] 本篇必须另外保留约束上下文、signed bitvector 值域及 area–delay 提取；把旧版或其第三方重实现直接当本篇代码会漏掉核心方法。

自动化范围也需保留：浮点减法案例的候选 case-split 是人工插入，随后由 ROVER 优化；不能将其描述成已实现自动发明 case-split。完整规则集合及调度仍需补齐，不能用少数示例规则代表原实现。[S2 §V-A、§VI]

SAT/SMT 适合作为未来小型重建的独立检查器，例如检查 `guard AND (lhs != rhs)` 是否不可满足，但这是建议的替代验证控制，不是声称作者发布了相应 Z3 脚本。必须保留实际位宽、signedness、溢出、移位及原始 mux 的全域输出语义。[S10]

## 可核实资产清单

| 资产 | 来源 / 版本 | 可用性、许可与具体限制 |
|---|---|---|
| 作者接受稿 | S1/S2，官方 14 页 | 浏览可读；本地下载 403；CC BY 4.0。 |
| 原 ROVER / 本篇扩展 | S3 §1.3、第 5 章映射 | 作者明确软件不能开源；无核实的源码包、commit、锁定依赖或可重跑 config。没有可授予使用的原实现源码许可。 |
| 规则补充资产 | `https://figshare.com/s/e3ab2850662d24991cbc`，S2 §IV-B 脚注 | 阅读工具不可访问，云端 curl HTTP 403。内容、文件数/大小、版本、许可未知；不能称为代码或缺失文件。 |
| DatapathBench | S6，作者账户，main | README、文件树及 `datapath.py` 可读；MIT。SV、固定实例 comb/datapath MLIR 与示例 SMTLIB。不是本篇原 benchmark 全集或优化器。 |
| extraction-gym 作者 fork | S7，main | README、Cargo.toml、LICENSE 可读；MIT 文本。Rust 2021、package 0.1.0；`ilp-cbc` 可选 feature、coin_cbc 0.1.6；egraph-serialize 固定 rev `951b829a434f4008c7b45ba4ac0da1037d2da90`。是 extraction 测试载体，不含已核实的 RTL 前后端/本篇完整扩展。data/ 页面被阅读工具限制；具体 ROVER case 文件、大小与论文对应关系未核实。 |
| egg | S8，公开 main | MIT；e-graph 基础库。当前 README 版本不能当论文版本。 |
| slang | S9，公开 main | MIT；SystemVerilog 前端。论文所用具体版本/构建参数未核实。 |
| CBC | S11，公开 master；论文引 2.10.10 | 当前 LICENSE 为 EPL 文本，历史版本许可证需按实际版本另核；未下载或安装 solver。 |
| Z3（候选替代控制） | S10，公开 master | MIT；非论文已核实必需品或已运行结果。 |
| 商业综合、商业 EC、TSMC 5nm 库 | S2 §V / Fig.3 | 论文评估依赖；产品版本、命令、corner、库包和许可权益未核实，未申请/接受任何许可。 |
| Intel 工业设计及完整评估配置 | S3 §1.3；S2 Table III | 混有闭源工业来源；公开替代品不自动覆盖原设计。不能宣称全部缺失，也不能认为已具备。 |
| 学习 checkpoint / 训练数据 | 方法性质 | 本核查没有证据表明该方法依赖学习权重；资产重点是 RTL、规则、工具和库，不能虚构 checkpoint 要求。 |

DatapathBench 的公开代码调用 Yosys、ABC、`libraries/asap7.genlib`，且 `verify_circt_synth` 中仍有 TODO。[S6-code] 这些是替代 harness 的事实，不代表本篇用了 ASAP7，也不代表仓库总 MIT 标签自动授予所有外部工艺资产权利。

未 clone、下载代码包或大数据；所有 main/master 页面是核查时动态视图，不构成不可变复现锁。机器规格、完整构建矩阵、RAM 峰值、整体时长和原始综合日志未核实。

## 最小方法学习的具体资源预算（仅规划，未执行）

建议把 L4 范围限定为少量显式位宽算子、一个已有 mux 分支示例及一个小型共享表达式例子；实现上述五项机制，读取论文公式，使用 egg/CBC 或同等基础设施，并加独立 bitvector 检查。手写结构化表达式可以暂时省去完整 SV parser，但必须保留位宽/符号语义。

规划上限：普通 Linux 云 CPU 4–8 核、RAM 16 GB、磁盘 10 GB、GPU 0；一位熟悉 RTL/Rust/SMT 的研究者约 3–7 个工作日完成受限贯通示例。此为工程估算，不是论文需求或性能测量；不能据此承诺完整 FP16 架构或全套结果。完整路线需另行估算数周以上开发与商业工具/工艺访问，当前无法给出可信采购金额或计算时长。

| 替代 | 可以学习什么 | fidelity loss |
|---|---|---|
| 小型手写 bitvector IR | ASSUME、值域、规则 guard 与提取的交互 | 不验证完整 SystemVerilog elaboration/frontend，不覆盖作者全部规则。 |
| DatapathBench / 自拟小电路替代工业 RTL | 在公开输入上检验机制 | 无法重现原 benchmark 分布、商业设计复杂度及平均收益。 |
| 开放综合与公开工艺库替代商业工具/TSMC5 | 模型排序与映射趋势 | 失去原 technology、时序约束和工具启发式；不能转述为复现原物理收益。 |
| Z3/其他 bitvector checker 替代商业 EC | 小设计全域功能等价及 guard 正确性 | 不能假定工业 datapath 的证明收敛性、证书接口或运行时相同。 |
| 仅复跑 extraction-gym | 比较提取方法 | 缺少约束发现、值域精化、RTL 生成；单独使用不满足最小忠实机制路线。 |

## 一个可检验 gap 与控制（仅提出，未运行）

**Gap：约束相关 mux 增多时，上下文复制的可扩展性边界尚需独立量化。** 论文 max-tree 案例需关闭 ASSUME 或分两次处理。[S2 §V-B/C] 后续可在同一组小型等价电路上逐渐增加共享条件的 mux 数，固定规则、迭代与资源上限；比较 ASSUME 全开、关闭和两阶段策略。记录 e-node/e-class 数、峰值 RAM、超时、模型 area/delay，并对每个输出做 bitvector 等价检查；相同资源限制下报告质量与失败率。这是检验适用边界的控制，不是正确性指控。

## 访问结果与停止点

- 完成：官方身份/许可、合法全文、作者未开源声明、旧版差异、基础库和作者公开资产 README/config/code 检查、两条路线分类。
- 403 阻断：官方 PDF 的云端本地下载；Figshare 补充入口。结果为**已拒绝访问、未取得文件**，不是许可审批待办；没有绕过或自动审批拒绝。
- 阅读工具限制：作者 extraction-gym data/ 和 GitHub repository-tab，具体数据清单未验证。其余公开页面继续独立核查。
- 阻碍完整路线：原实现未公开；工业输入与商业工具/工艺权益和配置未核实。没有把“未核实”改写成“不存在”。
- 本次到此停止，不进行实现或任何运行。

## Sources

- S1: [Imperial 官方记录与许可](https://spiral.imperial.ac.uk/entities/publication/b658a803-9cc4-4747-900e-cb1f42414d1f)
- S2: [作者接受稿](https://spiral.imperial.ac.uk/bitstreams/de68c6e8-a66d-42d6-ae3e-16eab9fc9782/download)，§III–V、Fig.3、Table II/III；全文阅读成功，本地下载 403。
- S3: [作者博士论文](https://samuelcoward.co.uk/assets/pdf/Thesis_Imperial.pdf)，§1.3、§1.4–1.5；原实现未开源、工业 benchmark 与章节映射。
- S4: [作者 publications](https://samuelcoward.co.uk/publications/)
- S5: [旧 ROVER 作者预印本](https://arxiv.org/abs/2406.12421)
- S6: [DatapathBench README/许可/文件树](https://github.com/cowardsa/DatapathBench)
- S6-code: [DatapathBench datapath.py](https://github.com/cowardsa/DatapathBench/blob/main/datapath.py)
- S7: [作者 extraction-gym fork](https://github.com/cowardsa/extraction-gym)；[Cargo.toml](https://github.com/cowardsa/extraction-gym/blob/main/Cargo.toml)；[LICENSE](https://github.com/cowardsa/extraction-gym/blob/main/LICENSE)
- S8: [egg](https://github.com/egraphs-good/egg)
- S9: [slang](https://github.com/MikePopoloski/slang)
- S10: [Z3](https://github.com/Z3Prover/z3)
- S11: [CBC](https://github.com/coin-or/Cbc)；[LICENSE](https://github.com/coin-or/Cbc/blob/master/LICENSE)
- S12: [IEEE 原入口](https://ieeexplore.ieee.org/document/10720856/)，机器人验证阻断。
