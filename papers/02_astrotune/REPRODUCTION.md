# Paper 02 — AstroTune 行为复现

论文：Runzhi Wang, Jingyu Pan, Yiran Chen, Jiang Hu, ISPD 2026, pp144–152, DOI10.1145/3764386.3779579。官方[全文](https://jpan.me/files/ISPD26_AstroTune.pdf)、[演讲稿](https://ispd.cc/slides/2026/protected/slides_9_1.pdf)、[Duke记录](https://scholars.duke.edu/publication/1817133)。本项目是独立实现，不是作者源码。

**结论：No-Go，不能宣称论文核心收益已复现。** 真实开源EDA行为框架已完成，三个主目标的十种方法在三种子下获得完全相同的最佳QoR（0.98566514、0.99898374、0.99749059）。独立divider压力测试中，BO/随机可达到104.44752692，AST多父方法均值104.45314849，未显示收益；全部divider结果仍有约4.45ns时序违例。无LLM推理，不推断其独立价值。

完成90组主实验、12组压力实验、10组历史成本对齐随机实验及1组剪枝分支探针。实际阶段尝试2,684次，2,680成功，4次为已修复早期pilot失败；全局321种完整配置、42种综合配置，只有20个不同网表字节哈希。累计阶段墙钟1,959.74秒（各调用时间相加，不是任务总耗时或端到端加速指标）。36种初始电路综合配置形式等价通过；divider一个配置30秒超时、其余5种未做形式证明。

默认剪枝0次；窄阈值后验探针2次，其被剪父后来均有子配置胜过当时baseline。未观察严格综合→放置QoR排名反转，未观察下游合法域改变。AST检索给divider的warmstart还劣于默认值，见`results/transfer_audit.json`。这些边界与七阶段价值见 `CROSS_STAGE_AUDIT.md`。

最终可重算表写入 `results/comparison.csv`、`results/ledger.json` 和 `results/summary.md`。阅读边界与预先写定的行为契约见 `CONTRACT.md`；来源、访问失败与许可见 `evidence/SOURCE_LEDGER.md`、`evidence/BLOCKERS.md`。

## 重跑

```bash
cd /workspace/PaperReproduction/papers/02_astrotune
python3 -m venv /workspace/scratch/astrotune/venv
/workspace/scratch/astrotune/venv/bin/pip install -r requirements.lock.txt
/workspace/scratch/astrotune/venv/bin/python src/bootstrap_tools.py
/workspace/scratch/astrotune/venv/bin/python src/experiment.py legacy
/workspace/scratch/astrotune/venv/bin/python src/experiment.py all
/workspace/scratch/astrotune/venv/bin/python src/extended.py
/workspace/scratch/astrotune/venv/bin/python src/supplement.py
/workspace/scratch/astrotune/venv/bin/python src/check_function.py
/workspace/scratch/astrotune/venv/bin/python src/check_pipe4.py
/workspace/scratch/astrotune/venv/bin/python src/check_equivalence.py
/workspace/scratch/astrotune/venv/bin/python src/audit_retrieval.py
/workspace/scratch/astrotune/venv/bin/python src/measure_overhead.py
/workspace/scratch/astrotune/venv/bin/python src/prune_probe.py
/workspace/scratch/astrotune/venv/bin/python src/audit_cross_stage.py
/workspace/scratch/astrotune/venv/bin/python src/audit_transfer.py
/workspace/scratch/astrotune/venv/bin/python src/summarize.py
/workspace/scratch/astrotune/venv/bin/python src/collect_evidence.py
```

完整重跑前将已有 `results/` 与 `work/` 移到别处，重新创建空目录；搜索会跳过已有 summary，且 JSONL 使用追加写入，不能把重复执行混为新种子。默认工具位于 `/workspace/scratch/astrotune/tools`，平台位于相邻 `platform/`；可通过 `ASTROTUNE_TOOLS`、`ASTROTUNE_PLATFORM` 配置，下载位置通过 `ASTROTUNE_SETUP` 配置。bootstrap 无 root/凭证/API费用；需要公开网络及宿主 g++/make。平台与工具二进制不放入审阅 ZIP；ZIP 内的原始指标足以离线重算关键结论。

## 实际实现与原文差异

两阶段：Yosys 综合/映射 → OpenROAD 放置、合法化、放置寄生估计。无 CTS、布线、signoff；PPA 是放置阶段 Liberty/STA 估计，功耗使用工具默认活动率，无真实工作负载/VCD。统一时钟2ns，输入/输出延迟各0.2ns，输入转换0.05ns，输出负载0.005pF；组合逻辑用虚拟时钟，时序电路的 clk 建时钟，其余输入设 I/O 延迟。异步 reset 也受该输入约束，不声称为工业约束设置。

综合空间6项：ABC fast开关×延迟目标100/500/2000ps。放置空间12项：core utilization 0.25/0.35/0.45/0.55×placement density0.65/0.75/0.85，共72项全配置。实际布局下限15μm；小电路的部分 utilization 设置会产生相同尺寸。配置唯一性与网表/指标唯一性必须区分。

结构检索：Pyverilog1.3，节点类型、父子类型边、位宽与时钟token，忽略标识符；IO节点额外权重2。BLAKE2b，SimHash128bit，MinHash64×32bit，HASTE1024维；三个分数等权。位宽表达式的标识符/操作符文字统一SYM，独立节点类型仍保留。Pyverilog不接受逗号连续assign，故仅在解析输入上拆为等价的多条assign，未更改综合RTL。spec只加入统一时钟；源设计说明供TF-IDF控制使用，不能声称完整spec语义编码。

TF-IDF词/二元组是明确的非LLM文本控制。fusion_control先按文本取2个donor，再等权融合文本与3个AST分数；不等价于论文的LLM模块摘要、设计摘要、候选筛选或直接语义打分。免费模型下载403，在线/本地LLM推理次数0。

BO：sklearn固定Matérn+白噪声核GP，类别one-hot，EI acquisition；Optuna TPE每线程2个startup trial，固定种子。未采用作者未公开的超参数。单父路径先搜索综合空间，再调一个父网表的放置；多父调度在连续2次保持最佳时传播，继续上游搜索，有限空间终止时补至最多3父。线程顺序执行，未复现并行异步调度。子线程从检索的放置参数开始，首次QoR比当前最佳差5%则剪枝。长停滞 early-stop 未实现；全局18次阶段调用预算与有限空间终止替代。每次放置读取精确父网表并记录SHA256。

Eq8–10实现见 `src/qor.py`。本地常数：αA=αP=.5，λ1=.05，λ2=.1，λ3=.1，λ4=1，β=1，κ=100，αW=1。参考值统一取该设计默认完整流程，避免不同warmstart自归一导致不可比；这是公平比较选择，与论文按initial solution归一存在解释差异。最终QoR若slack<0为100+|slack|，否则为面积/功耗归一均值；对所有方法一致。

源码、模型与算法的完整差异应与 `EVIDENCE_AUDIT.md` 一起阅读。四个目标实际映射单元范围分别为adder32 182–496、multi_pipe8 441–658、barrel28–43、divider1320–7136；原三个目标较小且只有72种全配置，零收益不能外推到原文20个更大设计。divider作为后续独立压力层，原三目标结果全部保留。

原始数值复现独立判为 Not Replicated，不从上述替代数值推导论文的14%/2×结论。

## 审阅包

四份请求报告齐全，另有跨阶段专项审计。`logs/raw_eda_and_validation.tar.gz`含6,907个原始日志/命令/验证输入文件；`artifacts/netlists/`保留全部20个不同映射网表并按SHA寻址，每个placement的输入均已与这些字节核对。另保留一个真实placed DEF/ODB示例。没有PDK、模型权重、编译缓存或大数据库混入仓库。审阅ZIP另包含完整独立分支git bundle、文件哈希清单；原始CSV/JSON可仅用Python标准库重算，无需EDA或网络。
