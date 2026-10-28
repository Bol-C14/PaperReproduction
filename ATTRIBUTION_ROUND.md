# 有界归因、双向cost与实际rollback机制实验

**本轮终点已完成：机制作用可观察，数值策略未显示稳定质量优势。** 沿原分支、保留全部旧结果；没有LLM API、付费、推送、PR或凭证/网络配置修改。原环境恢复后egglog/Z3可直接导入，5 CPUs、约17GiB RAM可用，不需要换机器。

## 合约、先行门槛与方法替代

配置 `configs/attribution_round.json` 最初在新EDA前提交（f0fbc56，完整历史可查）；先做纯e-graph候选多样性检查，再检查归因覆盖，再做提取干预。输入为原MCM/FIR-style构造的12位版本，以及预先列出的MCM(5,93)16位备用构造，不是官方benchmark字节。共用已冻结native egglog图：expanded算术constants+既有Appendix replay、5轮、3000节点上限，禁代数重排规则以避免无界增长。两个最终对照的图分别54和45个节点；每条件四种策略使用同一图字节hash、宽度、综合工具和正确性门槛。

最初的cell `src`属性归因实测覆盖率0：技术映射只剩Yosys techmap位置，路线已裁剪。一次类型错误发生在已完成pilot后的门槛比较（配置说明字符串误当阈值）；兼容性修复未重跑该点。复用原网表改用保留的逐运算命名wire作为边界，对门级fan-in锥分组，共享cell按owner数均分。这是**确定性启发式归因**，不是因果边际面积、不是LLM归因或原论文K-way partition的精确实现。

门槛预先为cell覆盖≥60%、选中运算命名边界覆盖≥80%。FIR-style基线能映射，但固定策略第5个候选只保留4/7运算边界（57.14%），虽然门数分摊覆盖仍为100%，已不可靠，因此停止整个FIR完整对照，不拿其余未执行策略作比较。这个失败表明“分完全部门”不等于“节点归因正确”。保留失败候选346门/depth24、原始RTL/SAT/netlist和失败恢复记录。随后以前瞻提交3a5a66c将备用MCM16位纳入剩余额度；没有根据其结果选取新策略。FIR耗费的5次综合和5次SAT不删除、不隐匿。备用原触发条件因此有明确、留痕的有界修订；不称盲法预注册研究。

## 机制实现与小测试

每个e-node使用稳定命名wire，所有中间值统一W位模运算。node cost目标为 `max(0.25, fractional_attributed_gates/W)`，对已选节点可以上调或下调。数值策略保存生成已接受候选时的cost快照；当新候选门数变差时恢复快照，**不再在外循环末尾立刻重置掉rollback**。后继提取立即读取恢复的状态。

纯抽取干预测试 `scripts/test_attribution_mechanisms.py`：

- 使用已测MCM分摊，增加MUL costs使实际后继从307门变为217门（这两次pilot真实综合/RTL SAT均已记录）。
- 保持总分摊不变、置换归因，后继表达式不同；这是依赖性测试，不证明归因准确或收益来自信息。
- 对实测0 gate的Shl节点，从1降至0.25，在有界13次纯结构上下文检查中找到后继变化（MUL cost=2，ADD=1）。此存在性示例没有用于选择对照超参，没有新EDA或事后PPA调参。
- 恢复cost快照立即改变抽取结果；实际比较中再检查反事实“同图、同seen-set、不rollback”的下一候选。

实际数值策略有8项上调、4项下调、9次rollback，其中7次非终止；**2次改变了真正执行的下一条新候选**，并与记录预测hash吻合：MCM71931 q2、MCM593 q1。其他rollback没有改变去重后的下一候选，或发生在终止点，不夸大为9次有效改进。未执行的反事实分支只做抽取、不额外综合，因此只证明决策作用，不证明该分支PPA会更好。

## 匹配真实预算的小对照

每个完整臂6次真实综合+6次实际生成RTL-to-reference SAT，无臂内重复RTL。所有方法采用同一有界novelty约束：对已见RTL，分支禁止选中e-nodes，寻找下一个tree-cost候选；每query最多64个子问题。这个机制避免固定策略重复浪费预算，不是预测量候选PPA的oracle，也不是全局完整k-best求解保证。

- fixed：统一静态operator cost=1，按上述next-best结构约束探索；不是只反复抽同一个点。
- random：seed0，对节点cost抽[0.25,1,3,10]，不读response；仅一个seed，不能作统计优势结论。
- open-loop：最大系数选中MUL优先、否则ADD，永远+3；不读response，不rollback，状态跨query保持。
- numerical：使用上述实际网表锥分摊、双向目标cost和持续rollback。不是原论文精确实现。

| 条件 | fixed best / last | random best / last | numerical best / last | open-loop best / last |
|---|---:|---:|---:|---:|
| MCM(7,19,31), W12 |237 /237|266 /341|217 /355|217 /237|
| MCM(5,93), W16 |326 /355|326 /402|326 /340|326 /355|

数字为generic gates。完整配对depth与point IDs在 `comparison_summary.json`；不拼接独立最小门数和深度。best为统一外部评估器在全部6条记录中计算的best-so-far，**不是策略返回的最终RTL**；最后candidate单独报告。这里没有事后将数值策略最后一次355门改称输出217门来制造优势。

结论：轨迹已经有差异，归因、上下调、rollback能作用于后继抽取；但W12数值策略best只追平开放环、last更差，W16没有方法改善baseline的326门。故本轮不支持数值归因策略有稳定质量优势，也不支持在线LLM/原ASPEN的优势。两套小MCM构造和一个seed不构成宽泛泛化证据。

## 数据、预算与失败

完整对照48 synthesis +48 RTL SAT；起步pilot4+4；被裁剪FIR5+5；**合计57+57=114真实EDA调用，低于预设64次综合硬上限**。工具非零退出0、SAT失败/timeout0；有前述1次post-pilot配置类型错误、1次FIR覆盖失败，均保留。完整8会话wall总13.006s（含提取/控制器/综合/SAT/逐步写入），全部EDA耗时14.893s（额外包括pilot/失败分支）；不能将这两种口径相减推断训练时间。依赖安装、研究/打包时间未纳入；本轮没有新安装、模型训练、离线PPA oracle或API调用。

57次调用仅28份unique tagged RTL，跨策略/pilot重复仍计入实际预算；每个完整臂6/6唯一。唯一RTL不等于独立硬件结构，部分不同语法/命名可能综合成同类逻辑。本轮不是57个独立设计或统计样本。全部唯一RTL及28份原始代表网表、hash、归因映射、实际门数/depth和controller轨迹已保存；可由 `verify_attribution_round.py` 独立重算/重放。

SAT仍仅证明生成RTL对reference RTL；**没有综合后JSON网表等价或原商业PPA验证**。锥边界方法的FIR失败、目标cost的加性假设、共享cell均分和正成本下限都是限制；Algorithm1的LLM、K-way语义分区等仍未复现。相比上一轮，显式cost下降及具有后继作用的rollback已由本替代方法补齐，不反写为原策略已实现。

## 重跑（独立目录，不覆盖旧证据）

使用既有免费依赖锁 `configs/behavior-requirements.lock`，不调用API：

```bash
export ASPEN_ATTRIBUTION_RUN_ROOT=.runs/attribution_rebuild1
.venv/bin/python scripts/attribution_round.py --preflight
.venv/bin/python scripts/attribution_round.py --pilot-suite
.venv/bin/python scripts/test_attribution_mechanisms.py
.venv/bin/python scripts/attribution_round.py --compare-primary
.venv/bin/python scripts/attribution_round.py --preflight-reserve
.venv/bin/python scripts/attribution_round.py --compare-reserve
.venv/bin/python scripts/analyze_attribution_round.py
.venv/bin/python scripts/verify_attribution_round.py
```

主FIR分支返回明确gated-stop消息后才执行reserve；不捕获/掩盖其他工具失败。当前归档保留原始未捕获traceback与恢复记录；重建入口已修补配置类型和失败记录落盘，计算方法/预算不变。完整每调用netlist可重建（不进Git），全部28份unique代表原始JSON进包。默认目录是审阅记录；新运行必须使用未使用的run root。
