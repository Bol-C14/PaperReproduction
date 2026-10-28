# Paper 02 — AstroTune 行为复现

> **GP审计修订 v2（原v1结果未删除）**：旧整配置ID one-hot + 固定各向同性Matérn使所有未见候选的后验均值/方差/EI相同，索引argmax退化；其GP arm是**无信息GP**，不得据此评价BO收益。原单父穷举6/6综合候选，终态也不能检验综合GP选择价值。v1报告/CSV/ledger原文保存在`evidence/v1_163c5fd/`，原2684次记录及git历史保留。修正使用fast二值+标准化log(delay)，放置util+density标准化；非对称EI及各20次ID重排回归通过。新证据在`GP_CORRECTION.md`与`results/gp_fix_summary.md`，只跑非穷举小预算pilot，不与v1合并。无在线LLM、七阶段未测；No-Go边界不变。


论文：Runzhi Wang, Jingyu Pan, Yiran Chen, Jiang Hu, ISPD 2026, pp144–152, DOI10.1145/3764386.3779579。官方[全文](https://jpan.me/files/ISPD26_AstroTune.pdf)、[演讲稿](https://ispd.cc/slides/2026/protected/slides_9_1.pdf)、[Duke记录](https://scholars.duke.edu/publication/1817133)。本项目是独立实现，不是作者源码。

**结论：No-Go，不能宣称论文核心收益已复现。** 真实开源EDA行为框架已完成，三个主目标的十种方法在三种子下获得完全相同的最佳QoR（0.98566514、0.99898374、0.99749059）。独立divider压力测试中，BO/随机可达到104.44752692，AST多父方法均值104.45314849，未显示收益；全部divider结果仍有约4.45ns时序违例。无LLM推理，不推断其独立价值。

**v1归档统计**：完成90组主实验、12组压力实验、10组历史成本对齐随机实验及1组剪枝分支探针。实际阶段尝试2,684次，2,680成功，4次为已修复早期pilot失败；全局321种完整配置、42种综合配置，只有20个不同网表字节哈希。累计阶段墙钟1,959.74秒（各调用时间相加，不是任务总耗时或端到端加速指标）。36种初始电路综合配置形式等价通过；divider一个配置30秒超时、其余5种未做形式证明。

默认剪枝0次；窄阈值后验探针2次，其被剪父后来均有子配置胜过当时baseline。未观察严格综合→放置QoR排名反转，未观察下游合法域改变。AST检索给divider的warmstart还劣于默认值，见`results/transfer_audit.json`。这些边界与七阶段价值见 `CROSS_STAGE_AUDIT.md`。

最终可重算表写入 `results/comparison.csv`、`results/ledger.json` 和 `results/summary.md`。阅读边界与预先写定的行为契约见 `CONTRACT.md`；来源、访问失败与许可见 `evidence/SOURCE_LEDGER.md`、`evidence/BLOCKERS.md`。

## GP修订验证（当前推荐）

```bash
cd /workspace/PaperReproduction/papers/02_astrotune
/workspace/scratch/astrotune/venv/bin/python tests/test_gp_geometry.py
/workspace/scratch/astrotune/venv/bin/python src/gp_fix_pilot.py
/workspace/scratch/astrotune/venv/bin/python src/summarize_gp_fix.py
/workspace/scratch/astrotune/venv/bin/python src/summarize.py
```

v2pilot前缀记录独立于原结果；已有summary会跳过。需要完全重跑时仅移走`results/v2pilot_*`和对应`work/v2pilot_*`，保留原v1及冻结donor库。回放GP acquisition只用于验证实际选择，0次EDA；不当成新的搜索试验。原v1精确复演需checkout `163c5fd`；以下旧命令描述其管线，当前源码GP已修正，不能覆盖原数据后声称同版本。

## 原管线重跑

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

BO v1（已发现无信息退化，结果归档）：sklearn固定Matérn+白噪声核GP，整配置ID one-hot，EI acquisition；v2改为真实参数几何，见GP_CORRECTION.md。Optuna TPE每线程2个startup trial，固定种子。未采用作者未公开的超参数。单父路径先搜索综合空间，再调一个父网表的放置；多父调度在连续2次保持最佳时传播，继续上游搜索，有限空间终止时补至最多3父。线程顺序执行，未复现并行异步调度。子线程从检索的放置参数开始，首次QoR比当前最佳差5%则剪枝。长停滞 early-stop 未实现；全局18次阶段调用预算与有限空间终止替代。每次放置读取精确父网表并记录SHA256。

Eq8–10实现见 `src/qor.py`。本地常数：αA=αP=.5，λ1=.05，λ2=.1，λ3=.1，λ4=1，β=1，κ=100，αW=1。参考值统一取该设计默认完整流程，避免不同warmstart自归一导致不可比；这是公平比较选择，与论文按initial solution归一存在解释差异。最终QoR若slack<0为100+|slack|，否则为面积/功耗归一均值；对所有方法一致。

源码、模型与算法的完整差异应与 `EVIDENCE_AUDIT.md` 一起阅读。四个目标实际映射单元范围分别为adder32 182–496、multi_pipe8 441–658、barrel28–43、divider1320–7136；原三个目标较小且只有72种全配置，零收益不能外推到原文20个更大设计。divider作为后续独立压力层，原三目标结果全部保留。

原始数值复现独立判为 Not Replicated，不从上述替代数值推导论文的14%/2×结论。

## 审阅包

四份请求报告齐全，另有跨阶段专项审计。`logs/raw_eda_and_validation.tar.gz`含6,907个原始日志/命令/验证输入文件；`artifacts/netlists/`保留全部20个不同映射网表并按SHA寻址，每个placement的输入均已与这些字节核对。另保留一个真实placed DEF/ODB示例。没有PDK、模型权重、编译缓存或大数据库混入仓库。审阅ZIP另包含完整独立分支git bundle、文件哈希清单；原始CSV/JSON可仅用Python标准库重算，无需EDA或网络。

**GP修订完成结果**：新24组408次真实调用全部成功（20×8次且每组≤3/6综合候选，4×62次历史成本匹配随机），0 EDA缓存命中；28条acquisition回放匹配，40次ID重排回归通过。累计3092次尝试/3088成功/4旧失败；v1/v2不混合。divider中部分修正GP arm胜过8次随机，但62次随机达到同样最佳值，n=2不足以归因或推广；multi_pipe8未见稳定优势。完整表及限制见`GP_CORRECTION.md`、`results/gp_fix_summary.md`。

## v3真实布线机制复核

已完成global-route→detailed-route→OpenRCX→显式SPEF回读STA，详见`ROUTING_MECHANISM.md`及`routing_v3/summary.json`。临时反转判断因缺少read_spef被撤回；核验后p9早期/最终均占优，single-parent与top-2同最佳PPA，观察regret0。15次实际工具调用（13成功/2失败，含3次明确额外时序修复校验），约37.74秒；累计3107次EDA尝试。无LLM API，未扩展divider/七阶段或donor泛化，已按负结果停止。

## v4原任务续作结果

修正链路的4点面板已完成：8次新工具调用/4次detailed+RCX+显式SPEF回读评估全部成功，约168秒。divider观察到1次placement→final严格QoR反转，early选择p0的观察regret约16.917ps；adder另一综合实现未见反转。divider的功耗与slack最优属于不同实现，不可拼成虚构PPA。每候选相同2调用/180秒额度；single/top-2仅作成本透明的机制回放，不宣称在线策略同总成本优势。累计3115尝试/3109成功/6旧失败；无LLM API，已停止。详见`ROUTING_PANEL_V4.md`。此前v3无反转结论只对应其adder s0面板，未被改写或混合。

## 独立预注册的证据限定

范围说明与结果共同进入同一个提交（本轮为a6c43ae及随后限定说明提交）；仓库没有独立、先于结果公开且不可变的时间戳预注册记录。因此“执行前冻结”是本任务执行记录/作者陈述，**独立的时间顺序预注册未获证明**。不据此把有界面板提升为确认性或盲测实验。divider的16.917ps是此面板观察到的排名反转/早剪枝机会损失，不是最终Pareto支配，也不是同总成本策略收益。
