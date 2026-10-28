# v3：真实布线与跨阶段机制——有界负结果

**完成真实global routing、detailed routing、OpenRCX提取和显式SPEF回读STA；未发现可靠排名反转或top-2收益，按停止规则结束。** 无任何LLM API调用，不恢复七阶段，不扩展小空间搜索。沿用分支与已有免费环境，OpenROAD0a6d0fd469bc674417036342994520ee2e0a2727。

## 范围、偏差与计费

开跑前冻结`routing_v3/SCOPE.md`：adder32/div16候选s0/s3×p0/p9，先pilot，12次routing相关工具调用、每次≤180秒、累计≤1200秒，失败计费。环境与原工具已恢复，约23GiB可用。实际详细布线遇到常量地网不能布线：用官方`insert_tiecells`实现常量，重新合法放置；目标/约束不变，但不能再把原先未修复布局的PPA当成同一实现的早期指标。后续早期PPA在修复后的同一实例/布局上重新评估。

详细布线初次报告0DRC并写出SPEF后，配对复测暴露第二个接口错误：`extract_parasitics`产出SPEF不保证STA使用它。**撤回临时的“排名反转”判断**，旧日志与错误指标全部保留并标不能作为最终提取时序。预算显式修订为15次：原12次全部计费，另3次只回读已选择路由的SPEF，0新增候选/布线搜索；没有删失败后重置预算。源码已补`read_spef`。路由SPEF来源、DB SHA、原始命令/日志可逐条核查。

最终仅测adder32的s0/p0与s0/p9；divider、s3被取消以容纳修复与校验。15次实际OpenROAD评估调用，13次执行成功、2次失败，累计工具墙钟37.7414秒；其中含2次嵌套global-placement修复操作、3次成功global-route、5次成功detailed-route，不能把这些嵌套工作当作零成本。另3次version/help控制调用不属EDA评估，单列。累计本分支EDA尝试3107/成功3101/失败6；原3092次不改写。

## 同一实现的早期→最终PPA

固定2ns虚拟时钟、输入/输出延迟0.2ns、输入转换0.05ns、输出负载0.005pF；固定Nangate45 corner及RCX规则，metal2–metal6、routing adjustment0.30。功耗仍为默认活动率估计，无工作负载VCD。表中每行是同一候选的完整面积/功耗/slack tuple，不拼接来自不同实现的独立最优值。

| 候选 | 早期area μm² | 早期power μW | 早期WS ns | 最终area μm² | 最终power μW | 最终WS ns |
|---|---:|---:|---:|---:|---:|---:|
| s0,p0 |215.992|87.2|0.761166818|215.992|87.6|0.751589257|
| s0,p9 |215.992|84.9|0.777915199|215.992|84.9|0.773735320|

早期使用修复后placement RC；最终使用实际detailed wires→OpenRCX→SPEF→显式read_spef。两个候选详细布线末轮报告0个DRC violation，保留DEF/ODB、DRC报告、SPEF、RCX/STA日志；不是电源网/LVS/天线/工艺签核。RCX取自同一官方ORFS pinned commit，hash见`routing_v3/rcx_provenance.json`，不分发原规则文件。

p9在早期和最终都支配p0；两阶段观察Pareto frontier均为{p9}，严格rank reversal=0。因为本例同一实现p9恰好同时取得最小功耗/面积和最佳slack，独立各指标最优与可实现tuple不冲突；**这不意味着一般可以把不同候选的P/A/T极值合成一个不存在的实现。** 原暂时反转是STA接口错误，不是跨阶段发现。

## 配对single-parent / top-2

在pilot之后固定这个机制复核，非盲测/泛化实验：single-parent按早期指标保留p9，在p9试route seeds0/1；top-2在p0/p9各试seed0。3次真实route/extract与3次真实SPEF校验产生两臂数据，其中p9/seed0共用一次物理观测，在各自预算各计一次，不伪造额外执行。

每臂2次route/extract+2次SPEF校验=4次新工具调用，工具时间额度同为24秒；实际single14.0323秒、top-2 14.5280秒，**不是相同已消耗秒数**。两臂均全额计入相同prepared history：原1次综合+2次placement产物及本轮2次合法global-route，共5次准备调用、2.6951秒历史生产墙钟。每臂一次使用总计9次已计费机会。失败/诊断启动调用另列入整个项目15次总账；不隐藏为免费，不据此宣称cold-start加速。若single冷启动自行省去不用的p0准备，成本将不同，此处不宣称该场景预算匹配。

两臂最佳结果相同，均为p9：215.992μm²、84.9μW、0.773735320ns；观察early-pruning regret=0。seed0/1在此得到相同路由DB哈希，故single的两次实际执行只有一个独立几何实现；top-2有两个父/两个路由实现，却未改善最终最佳PPA。单个小电路不足以验证所有反转是否不存在，只能给这组冻结约束/候选的负结果。

## 交付与复算

`routing_v3/attempts.jsonl`保留15次真实记录和失败；`metrics.csv`、`summary.json`及`src/summarize_routing.py`可不依赖EDA/网络用标准库重算，并逐一核验输入/输出DB SHA、SPEF回读链及0DRC日志。原始Tcl是每个实际版本的精确命令；修改后的runner不会追溯改变旧命令。`routing_v3/inputs/`保留两份源布局，目录中保留真实路由与SPEF用于审阅。

```bash
cd /workspace/PaperReproduction/papers/02_astrotune
python3 src/summarize_routing.py
```

新运行应单独移动原`routing_v3`为归档、重新冻结scope，不能在已耗尽15次预算的目录无界追加。当前阶段已停止，不提出额外sweep。**Go**仅针对真实布线/提取/回读接口已跑通；**No-Go**针对已证明跨阶段反转/剪枝收益、模型泛化、七阶段协同或论文完整复现。现有donor分析保持描述性，没有因routing pilot升级为家族泛化证据。

## v4原任务续作结果

修正链路的4点面板已完成：8次新工具调用/4次detailed+RCX+显式SPEF回读评估全部成功，约168秒。divider观察到1次placement→final严格QoR反转，early选择p0的观察regret约16.917ps；adder另一综合实现未见反转。divider的功耗与slack最优属于不同实现，不可拼成虚构PPA。每候选相同2调用/180秒额度；single/top-2仅作成本透明的机制回放，不宣称在线策略同总成本优势。累计3115尝试/3109成功/6旧失败；无LLM API，已停止。详见`ROUTING_PANEL_V4.md`。此前v3无反转结论只对应其adder s0面板，未被改写或混合。
