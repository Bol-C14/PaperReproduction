# 证据审计与批判审评

> **GP审计修订 v2（原v1结果未删除）**：旧整配置ID one-hot + 固定各向同性Matérn使所有未见候选的后验均值/方差/EI相同，索引argmax退化；其GP arm是**无信息GP**，不得据此评价BO收益。原单父穷举6/6综合候选，终态也不能检验综合GP选择价值。v1报告/CSV/ledger原文保存在`evidence/v1_163c5fd/`，原2684次记录及git历史保留。修正使用fast二值+标准化log(delay)，放置util+density标准化；非对称EI及各20次ID重排回归通过。新证据在`GP_CORRECTION.md`与`results/gp_fix_summary.md`，只跑非穷举小预算pilot，不与v1合并。无在线LLM、七阶段未测；No-Go边界不变。


**判定基准是行为契约，不是输出相似的表格。** 已读事实、独立实现选择、工具替换和缺失证据分别记录。官方九页全文没有附录；另读官方26页演讲稿。作者源码、可下载实验artifact及源码许可未找到；ACM页面403，因此不能宣称彻底排除那里存在补充资料。详细来源见 `evidence/SOURCE_LEDGER.md`。

| 主张/模块 | 本次判定 | 独立证据及限制 |
|---|---|---|
| AST意为abstract syntax tree | Replicated（定义核验） | 原文明确；Pyverilog实际解析公开RTL，无猜测 |
| SimHash/MinHash/HASTE公式行为 | Partially Replicated | BLAKE2频率投票、seeded minima、signed hashing/L2/cosine实际执行；维数、权重、token规则由本地声明，原设置未知 |
| 改名/移除注释的结构稳定性 | Partially Replicated | `retrieval_audit.json`，精确AST同一的alpha-renaming；不是原文多LLM重新生成的功能等价RTL |
| LLM分层模块/设计摘要、候选筛选、直接语义分数 | Not Replicated | 免费模型与后端403，0次推理。TF-IDF及fusion_control只作非LLM控制 |
| 历史参数warmstart | Partially Replicated | 三个独立donor经真实搜索后冻结；所有目标运行接收其完整(s,p)向量，无目标结果进入检索接口；原数据库未知 |
| GP综合/TPE物理阶段与真实反馈 | v1 GP Not Replicated；v2 Partially Replicated | v1 GP后验对未见配置无区分力，撤回其BO效用解释。v2真实参数几何及非穷举pilot验证选择机制；OptunaTPE/真实PPA反馈保留。不是论文模型配置重演 |
| 跨阶段信息流正确 | Replicated（本地流程） | 每个placement有parent_run/id/s和网表SHA；`summarize.py`逐条核验；物理工具接收真实父网表，无离线目标oracle |
| 多候选传播/动态baseline/首次子线程剪枝 | Partially Replicated | 真实scheduler事件、baseline、prune日志；顺序事件执行，最多三父；稳定2轮及5%为本地假设；长停滞early-stop未实现 |
| 七阶段商业流程的协同与签核 | Not Replicated | 只有综合→放置，无CTS/布线/签核，不映射成七阶段成功 |
| 库随新设计更新 | Partially Replicated | 结果写入非serving archive，实验期间serving DB冻结；没有证明长期自改进或跨时段泛化 |
| AST相似/功能近似可预测配置可迁移性 | Partially Replicated（直接检验，不预设成立） | 事后把每个donor选中配置实际运行在每个目标上，见transfer_matrix；这些观测不回流优化器。样本很小，无家族外泛化结论 |
| LLM在AST+BO以上的独立价值 | Not Replicated | 无LLM；文本控制的好坏都不能回答这一因果问题 |
| 约14% PPA收益、>2×运行加速 | Not Replicated | 工具/电路/阶段/约束/历史库/模型不同；没有精确全流程墙钟匹配，不将替代结果当原表复现 |
| 原表格绝对area/power/WS/runtime | Not Replicated | Table5–8无原始数值重演；原文数值与本次本地指标严格分开 |

## 输入输出与正确性

`benchmarks/manifest.json`固定源commit、RTL/spec路径、top、split及SHA；原RTL未为提高PPA修改。donor/target源文件不重叠，但adder与multiplier有刻意保留的家族关联，**不是家族独立验证**。barrel shifter与serial right_shifter并非相同功能；没有强行指定它们为“正确检索命中”。压力测试divider在主实验两例目标较平坦后加入，单独成层，不删除零收益结果。

RTL→AST输入不经过LLM；结构排名输出带分项分数，检索接口只接受目标RTL/spec与donorRTL/spec，不接受目标PPA。warmstart配置来自冻结legacy_db。GP/TPE只读已执行的本线程/阶段观测；每个子线程直接读取真实综合父网表。所有真实阶段执行，包括默认参考、warmstart、首次子线程、被剪枝线程，均占预算；不以缓存命中当成EDA执行。多个placement可复用同一已计费综合产物，随机对照也有同样权限。

原RTLLM测试台需要将期望DUT名字改为`verified_*`实际top，其余原测试逻辑保留。六个初始电路中5个原测试通过；4-bit流水乘法器原测试失败8/100，因为它会把首拍结果偶然等于本次乘积计作错误，并非可靠的流水线正确性判据。`tests/pipe4_semantics.v`独立枚举256组输入，在两个采样沿后检查乘积，全部通过。divider原100组测试也通过。有限仿真不构成完整spec证明；Verilator的两态语义会掩盖X/初始化问题，例如8-bit流水乘法器重复复位a_reg而未直接复位b_reg，原源码如实保留。

`check_equivalence.py`对初始六个电路出现过的每个综合配置做RTL→门级等价检查；读取Liberty逻辑模型，忽略未使用clock-gating cell缺失function，并将两侧async2sync后证明。最终36个初始电路配置证明通过。divider首配置30秒超时未证明，其余5个配置因验证预算未做形式证明，见`equivalence.json`；未证明不等同于发现功能不等价。证明对象是共同同步抽象下的逻辑等价，不能推出任意异步复位波形的时序等价或电路满足全部自然语言spec。放置合法化与parent哈希验证也不能替代布线DRC/LVS。

## 对原文结论的校准

1. 原文Table6和官方演讲稿给altered HR@1=95.8%=23/24、HR@3=100%，正文“全部top1”的措辞过强。高HR证明检索标识/功能匹配，不自动证明warmstart配置迁移收益；应直接测候选donor的transfer regret。
2. 官方演讲稿明确声称database与testing designs分开。我们尊重该声明；没有公开成员名单/哈希，故无法核查家族、近重复、LLM生成prompt与配置历史的重叠。不能把“无法独立验证”写成“已发现泄漏”。
3. 多父传播会给下游更多起点，同时剪枝改变每阶段调用分配。没有真实阶段计数、总CPU、并行度、history准备及LLM费用，就不能把性能归因于tournament本身。本次同时保留多父无剪枝控制、固定阶段调用预算和包含全额history准备成本的随机对照。
4. Eq5的HASTE是signed feature hashing。不同token映射到不同桶时本身不会产生语义距离；相同桶的相关性可能只是碰撞。结构token的选取/频率/位宽/连接编码及融合权重比“HASTE名义上含embedding”更关键。本地常数掩码反例仅检验**本地tokenizer**丢失常数信息，不能据此指控作者tokenizer相同。
5. 原文warmstart图是6例初始化比较，不能单独证明随数据库增长而长期自改进。应在冻结/逐时更新两种协议、同等累计准备预算、前瞻目标上比较。
6. 本地GP/TPE/结构控制的零收益不能反证作者在更大七阶段流程的收益；同样，真实EDA pilot成功也不能认证论文的核心LLM因果主张。

## Go / No-Go

**No-Go：** 将当前证据当作AstroTune完整算法、独立LLM效用、七阶段收益或原论文14%/2×结论已复现。

**Go：** 将本分支作为可审查的真实EDA行为实验框架与零收益/压力结果，进一步做家族隔离的迁移研究。是否存在可推广增益，应由更大设计、可访问免费模型、严格总成本匹配和预先确定的策略再验证。当前没有需要用户批准才能完成的剩余写入动作；所有未做能力已按Not/Partially标记。

**GP修订完成结果**：新24组408次真实调用全部成功（20×8次且每组≤3/6综合候选，4×62次历史成本匹配随机），0 EDA缓存命中；28条acquisition回放匹配，40次ID重排回归通过。累计3092次尝试/3088成功/4旧失败；v1/v2不混合。divider中部分修正GP arm胜过8次随机，但62次随机达到同样最佳值，n=2不足以归因或推广；multi_pipe8未见稳定优势。完整表及限制见`GP_CORRECTION.md`、`results/gp_fix_summary.md`。
