# v4：修正链路的小候选组，观察到一次真实排名反转

**原环境/分支续作完成；不含任何LLM、认证或模型API调用。** 保留v1/v2/v3及失败。按开跑前`routing_v4/SCOPE.md`执行4个候选，每点1次global-route/修复后early PPA、1次detailed-route→OpenRCX→write_spef→**read_spef**→STA。8次新真实工具调用全部成功，其中4次详细评估，低于授权的最多8次；累计167.998秒，停止，不扩展。

固定候选：divider s0的p0/p9，adder32 s3的p0/p9。adder s3与v3 s0的网表SHA确实不同，但这次每设计仅比较相同综合网表下两种placement，不能宣称识别了综合选择的因果作用。所有约束、PDK/RCX、路由层/调整系数、seed0与单线程保持v3设置。每候选相同2次调用、180秒总时间额度（global60+detail120）；记录实际墙钟，不声称相同已消耗秒数。0新综合、0单独placement调用，但global-route流程内有4次已计费的重新放置/常量tie修复操作。

## 同实现PPA与Pareto边界

| 设计/综合 | placement | area μm² | early power W | early WS ns | final power W | final WS ns |
|---|---|---:|---:|---:|---:|---:|
| divider s0 |p0|1454.488|0.0668|-4.498839650|0.0672|-4.582927945|
| divider s0 |p9|1454.488|0.0671|-4.503332945|0.0673|-4.566010810|
| adder32 s3 |p0|509.922|0.000196|0.997508993|0.000197|0.991248001|
| adder32 s3 |p9|509.922|0.000196|0.995500821|0.000197|0.986034393|

每行是同一候选的完整tuple，early来自tie修复后的placement RC估计，final来自真实详细布线与显式SPEF回读。功耗仍为默认活动率估计、报告有效位数有限，不是工作负载功耗或签核。全部detailed末轮DRC=0，四份SPEF的多端网络电阻图（1344、1344、560、560网）均连通；不是独立LVS/电源网/天线验证。

**divider出现一次严格的硬时序QoR排名反转**：early p0更好，final p9更好。沿用原layout QoR=100+|WS|的时序违例分支，early选择若只保留p0，其观察终态regret为0.0169171348385 QoR单位，即约16.917ps更差的最坏slack。两解仍严重违反2ns目标，不能称作timing closure。这里的regret是独立完成两个后代后的描述性审计，不是向优化器提供oracle。

这里的Pareto frontier仅指已测两点、报告精度下的观察前沿，不是全空间Pareto最优。divider early Pareto frontier为{p0}，final为{p0,p9}：p0最终功耗低，p9最终slack好。独立极值组合(area1454.488,power0.0672,WS−4.566010810)没有任何一个候选同时实现；不得把它当成真实实现PPA。adder s3无严格QoR反转/后悔值；P/A报告打平，p0时序较好。

## 比较预算与不能作出的结论

这里完成的是**每候选相同调用数/时间额度/约束的真实配对测量**。single-parent/top-2策略只在已测固定候选上作离线机制审计，回放0次新EDA，不能冒充一次新的在线优化器实验：B=1时二者都选early-best；B=2时top-2可多查一个父，固定父在本面板只有一个路由设置，不能强做重复确定性执行来假造实际机会预算匹配。因此不宣称“同真实总成本下top-2更优”。

准备成本没有藏起：两候选组每设计的原1次综合+2次placement以及本轮2次global-route，共5次prepared-history调用；完整计入两种策略的一次使用成本，原始生产墙钟分别divider7.4184秒、adder2.7667秒。若冷启动single只准备一个父，其成本更低，必须另行匹配，不能用这里的反转结果宣称速度/效率优势。旧v3的matched配对负结果保持独立，不与v4不同设计/综合/预算混合。

## 中间告警与完整性

divider p9在detailed完成后、最终RCX之前，旧的`estimate_parasitics -global_routing`发出了Missing route to pin告警。告警针对过期的全局导引估计；最终指标在之后由OpenRCX写SPEF并显式回读获得。没有静默删除告警或把它当作最终图已连通的证明：`audit_spef_connectivity.py`对提取电阻图的全部端点作了独立离线连通性检查，未见断开，DRC末轮也为0。审阅包保留完整告警和执行次序；该检查仍不替代LVS。

## 复算、判定与停止

```bash
cd /workspace/PaperReproduction/papers/02_astrotune
python3 src/audit_spef_connectivity.py
python3 src/summarize_routing_panel.py
```

两脚本仅标准库，不运行EDA/网络，校验全部源/目标DB SHA、路由后代链、read_spef命令、DRC与SPEF电阻图。`routing_v4/metrics.csv`、`summary.json`保留全部结果；源布局副本、路由ODB/DEF/SPEF、精确Tcl和日志齐全。原8次预算已耗尽，不再增加点/重试/模型。累计本分支3115次EDA尝试、3109执行成功、6旧失败。

**Go：** 已在免费真实流程中展示一个placement→最终布线排名反转与潜在早剪枝机会损失，且能区分可实现PPA tuple与独立极值。**No-Go：** 同总机会/实际时间的在线策略收益、稳定总体效果、家族/模型泛化、七阶段交互或论文完整复现。只有两个旧设计、四点、单seed，不能外推反转频率；divider尚未满足时序，结果到此为止。

## 独立预注册的证据限定

范围说明与结果共同进入同一个提交（本轮为a6c43ae及随后限定说明提交）；仓库没有独立、先于结果公开且不可变的时间戳预注册记录。因此“执行前冻结”是本任务执行记录/作者陈述，**独立的时间顺序预注册未获证明**。不据此把有界面板提升为确认性或盲测实验。divider的16.917ps是此面板观察到的排名反转/早剪枝机会损失，不是最终Pareto支配，也不是同总成本策略收益。
