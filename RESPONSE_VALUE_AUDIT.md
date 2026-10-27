# 最小判别：response信息是否优于开放环结构扰动？

**结论：在预先固定的三个7-call对照中，没有观察到response信息的增益。** 先前的动态cost-arm对静态cost-arm结果不能单独归因于真实response价值。行为闭环仍部分复现，但LLM能力、分区归因、显式cost下降均未实现。

## 预先固定、执行与评估分离

预注册提交 `297cfc80f338e4d79ebecf40889fbab3a68da22f` 在新EDA前固定了 `configs/openloop_preregistered.json` 与策略源码。开放环只接收graph、当前cost、selected-structure；沿用反馈策略的最大系数MUL优先/否则ADD节点规则，永远+3，静态full规则选择、不读取response、不rollback，外循环按原协议重置cost=1。没有从已有反馈动作日志事后抄录动作。真实response仅保留日志和统一外部评估。

按MCM-expanded、FIR-initial、x×11-initial顺序运行，各7次真实综合（reference1+2×3）和7次生成RTL-to-reference SAT，共新增21+21。反馈比较对象复用原 `factorial_<name>_<pool>_static_feedback_s0` 记录，未重复跑control。起始构造程序hash、规则池、工具、宽度、抽取器和实际EDA调用预算匹配；没有声称unique设计机会匹配。

**策略输出是最后candidate。** 表中best-so-far由会话结束后的外部评估器对两种控制器的全部7条记录作同一评估，包括reference。开放环未用response选动作或输出best RTL。反馈控制器内部读取门数标量选择回退/+6，但也未显式返回incumbent RTL。`best_gates`与`best_depth`是独立描述统计，不能拼成实现；配对候选和point IDs单独保存。

| 条件 | 控制器 | 7次门数轨迹 | 最后candidate (门数,depth) | 外部best gates（对应depth） | unique RTL | 重复query率 |
|---|---|---|---|---|---:|---:|
| MCM expanded | feedback / openloop相同 |146,146,146,130,146,146,130|(130,11)|130 (11)|3/7|57.14%|
| FIR-style initial | feedback / openloop相同 |162,162,162,158,162,162,158|(158,18)|158 (18)|4/7|42.86%|
| x×11 initial | feedback / openloop相同 |59,59,59,61,59,59,61|(61,10)|59 (11)|3/7|57.14%|

三组不仅门数/深度轨迹相同，逐步RTL byte hashes也相同。MCM和FIR改善前response持平，+3结构扰动已足以产生改善；没有证据支持response语义归因是其原因。x×11反馈在query4和query7后rollback/+6，cost-map与开放环产生分歧，但query4为外循环末尾，query5重新初始化；query7后结束。因此本预算没有后续候选使用这些分歧cost，不能声称rollback带来候选质量收益。结果只否定本次三个fixture/策略/预算中的正面证据，不证明一般反馈无用。

机器原始对照：`results/behavior/openloop_comparison.json`，逐query原始记录与gzip日志仍在runs/和logs/behavior。策略响应盲性由不带metric/history参数的 `update_costs_openloop` 与完整源码可审查；18个新更新可独立重放。没有新增预训练、模型API或付费。

## 重复查询与机会口径修正

原346次综合只有14份byte-level unique emitted RTL，重复率95.95%；原48会话中16个只有1份unique RTL。新增开放环后367次综合仍只有14份，重复率96.19%。这些是实际工具调用成本，不是346/367个独立候选、独立设计或统计样本。`unique RTL`仅按源字节hash去重，交换乘数/源表示也可能算不同，独立硬件结构数可能更少。

所有reference和重复调用都收费于实验预算；“equal true-call budget”不等于“equal informative exploration”。原因子均值可描述动态策略配置，不能作为分离出的response信息效应或LLM因果效应。开放环对照的外部best与最后输出都无优势差异；static uniform输出重复度高的限制已明确保留。

## 可独立核验的网表与证明边界

`results/behavior/unique_netlists/` 纳入全部14份unique RTL的原始代表JSON网表（约1.1 MiB），`unique_netlist_inventory.json`记录RTL hash、代表query、原始网表hash、367次调用映射及预期门数/depth。同RTL的不同调用源路径元数据不同，故原始netlist byte hash可能不同；代表文件不冒充全部调用字节相同。`python scripts/verify_unique_netlists.py` 只依赖标准库，可独立重算14份门数/拓扑depth和hash。

**所有已报告SAT仅比较生成的Verilog RTL与独立reference RTL，不验证综合后JSON网表等价。** 本次没有post-synthesis netlist equivalence，也没有物理area/timing；网表验证只是结构指标重算。51个proposal检查是手写语义公式/实例的Z3义务，未自动解析或证明`.egg`文件中的全部规则。Algorithm1的K-way partition/归因、critical-node cost下降和在线LLM均未实现；回退恢复旧cost不等于实现了其显式下降分支。

## 重建与计数

先按BEHAVIOR_CONTRACT.md完成pilot/full，再在同一新运行目录执行：

```bash
.venv/bin/python scripts/behavior_loop.py --openloop
```

控制器对照与网表导出：`.venv/bin/python scripts/analyze_openloop.py`（遵循同一个ASPEN_BEHAVIOR_RUN_ROOT；未设置时核查审阅目录）；标准库网表核验与现有online核验不调用EDA。当前online/controlled阶段累计367 synthesis+367 RTL SAT，ledger734条；第一阶段207条EDA另计，总941。实验pipeline模型调用0，新增付费费用0。
