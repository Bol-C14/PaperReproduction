# ASPEN (MLCAD 2025) reproduction

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
.venv/bin/python scripts/rule_audit.py > logs/rule_audit.log
.venv/bin/python scripts/pilot.py > logs/pilot.jsonl
.venv/bin/python scripts/verify_rtl.py > logs/rtl_equivalence.log
MPLCONFIGDIR=$PWD/.cache/matplotlib XDG_CACHE_HOME=$PWD/.cache python scripts/analyze.py > logs/analysis.log
```

分析/绘图使用预装 numpy 2.3.5、matplotlib 3.10.8（单独锁定见 configs/analysis-requirements.txt）。WASM 只映射当前目录，输入使用相对路径；最初 `/tmp` 输入 smoke 失败，已保留日志。每次候选综合 timeout=60s，Z3=5s；没有运行未知来源 shell 或模型生成的证明程序。

## 成本、运行及保存

最终 68 个候选的综合及表达式证明 wall time 见 `results/pilot_execution.json`；SAT 时长逐项在 `results/rtl_equivalence.json`。首次 68 候选 sweep 后修正了结构特征深度计算（共享节点的 visited 处理），完整重跑一次，因此开发过程共 136 次候选综合、136 次候选 Z3 checks、68 次额外 SAT、90 项规则检查；另有 3 次 smoke 调用（其中一次路径失败）。首次 sweep 日志被最终 sweep 替换，计数/原因在 `logs/run_history.json`，不能把最终 suite 时间冒称总研究时间。LLM 调用=0，token=0，新增付费成本=$0；平台已有运行资源的价格未知，没有估算为零。

Git 只保留小型源码、RTL、logs、metrics、图与 manifest，不纳入虚拟环境、wheel cache、PDF 或生成 netlists。netlist 可由脚本重建，逐项 hash 已记录。官方 PDF 的 shell 下载为 HTTP 403，没有 PDF 字节或可信 hash；不伪造 hash。浏览读到的版本未与 IEEE 字节版本校验。完整复现应在取得官方 artifacts 与合法免费可用工具/预算后另行放行。
