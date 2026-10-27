# Paper 02 — AstroTune 行为复现

论文：Runzhi Wang, Jingyu Pan, Yiran Chen, Jiang Hu, ISPD 2026, pp144–152, DOI10.1145/3764386.3779579。官方[全文](https://jpan.me/files/ISPD26_AstroTune.pdf)、[演讲稿](https://ispd.cc/slides/2026/protected/slides_9_1.pdf)、[Duke记录](https://scholars.duke.edu/publication/1817133)。本项目是独立实现，不是作者源码。

实验正在执行，最终可重算表写入 `results/comparison.csv`、`results/ledger.json` 和 `results/summary.md`。阅读边界与预先写定的行为契约见 `CONTRACT.md`；来源、访问失败与许可见 `evidence/SOURCE_LEDGER.md`、`evidence/BLOCKERS.md`。

## 重跑

```bash
cd /workspace/PaperReproduction/papers/02_astrotune
python3 -m venv /workspace/scratch/astrotune/venv
/workspace/scratch/astrotune/venv/bin/pip install -r requirements.lock.txt
/workspace/scratch/astrotune/venv/bin/python src/bootstrap_tools.py
/workspace/scratch/astrotune/venv/bin/python src/experiment.py legacy
/workspace/scratch/astrotune/venv/bin/python src/experiment.py all
/workspace/scratch/astrotune/venv/bin/python src/supplement.py
/workspace/scratch/astrotune/venv/bin/python src/check_function.py
/workspace/scratch/astrotune/venv/bin/python src/check_pipe4.py
/workspace/scratch/astrotune/venv/bin/python src/check_equivalence.py
/workspace/scratch/astrotune/venv/bin/python src/audit_retrieval.py
/workspace/scratch/astrotune/venv/bin/python src/measure_overhead.py
/workspace/scratch/astrotune/venv/bin/python src/summarize.py
```

完整重跑前将已有 `results/` 与 `work/` 移到别处，重新创建空目录；搜索会跳过已有 summary，且 JSONL 使用追加写入，不能把重复执行混为新种子。默认工具位于 `/workspace/scratch/astrotune/tools`，平台位于相邻 `platform/`；可通过 `ASTROTUNE_TOOLS`、`ASTROTUNE_PLATFORM` 配置，下载位置通过 `ASTROTUNE_SETUP` 配置。bootstrap 无 root/凭证/API费用；需要公开网络及宿主 g++/make。平台与工具二进制不放入审阅 ZIP；ZIP 内的原始指标足以离线重算关键结论。

## 实际实现与原文差异

两阶段：Yosys 综合/映射 → OpenROAD 放置、合法化、放置寄生估计。无 CTS、布线、signoff；PPA 是放置阶段 Liberty/STA 估计，功耗使用工具默认活动率，无真实工作负载/VCD。统一时钟2ns，输入/输出延迟各0.2ns，输入转换0.05ns，输出负载0.005pF；组合逻辑用虚拟时钟，时序电路的 clk 建时钟，其余输入设 I/O 延迟。异步 reset 也受该输入约束，不声称为工业约束设置。

综合空间6项：ABC fast开关×延迟目标100/500/2000ps。放置空间12项：core utilization 0.25/0.35/0.45/0.55×placement density0.65/0.75/0.85，共72项全配置。实际布局下限15μm；小电路的部分 utilization 设置会产生相同尺寸。配置唯一性与网表/指标唯一性必须区分。

结构检索：Pyverilog1.3，节点类型、父子类型边、位宽与时钟token，忽略标识符；IO节点额外权重2。BLAKE2b，SimHash128bit，MinHash64×32bit，HASTE1024维；三个分数等权。位宽表达式的标识符/操作符文字统一SYM，独立节点类型仍保留。Pyverilog不接受逗号连续assign，故仅在解析输入上拆为等价的多条assign，未更改综合RTL。spec只加入统一时钟；源设计说明供TF-IDF控制使用，不能声称完整spec语义编码。

TF-IDF词/二元组是明确的非LLM文本控制。fusion_control先按文本取2个donor，再等权融合文本与3个AST分数；不等价于论文的LLM模块摘要、设计摘要、候选筛选或直接语义打分。免费模型下载403，在线/本地LLM推理次数0。

BO：sklearn固定Matérn+白噪声核GP，类别one-hot，EI acquisition；Optuna TPE每线程2个startup trial，固定种子。未采用作者未公开的超参数。单父路径先搜索综合空间，再调一个父网表的放置；多父调度在连续2次保持最佳时传播，继续上游搜索，有限空间终止时补至最多3父。线程顺序执行，未复现并行异步调度。子线程从检索的放置参数开始，首次QoR比当前最佳差5%则剪枝。长停滞 early-stop 未实现；全局18次阶段调用预算与有限空间终止替代。每次放置读取精确父网表并记录SHA256。

Eq8–10实现见 `src/qor.py`。本地常数：αA=αP=.5，λ1=.05，λ2=.1，λ3=.1，λ4=1，β=1，κ=100，αW=1。参考值统一取该设计默认完整流程，避免不同warmstart自归一导致不可比；这是公平比较选择，与论文按initial solution归一存在解释差异。最终QoR若slack<0为100+|slack|，否则为面积/功耗归一均值；对所有方法一致。

源码、模型与算法的完整差异应与 `EVIDENCE_AUDIT.md` 一起阅读。原始数值复现独立判为 Not Replicated，不从上述替代数值推导论文的14%/2×结论。
