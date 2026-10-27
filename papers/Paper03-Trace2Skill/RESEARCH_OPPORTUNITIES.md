# 后续EDA研究：优先回答什么，而不是先造新方法

当前最有价值的问题是：收益来自新测试反馈、更多独立尝试、角色模型反思，还是稳定可复用的skill内容？以下是实施方案，尚未运行，不能当实验结果。

## 1. 最小的归因实验

先选一个免费可执行任务，以同一个已确认免费模型完成 g2/p2/r1 的控制路径检查；再至少两种任务家族、多个独立search seed。model revision、采样seed、tool image digest和可见测试信息固定。新模型结果标portability，不称重现历史数值。没有免费endpoint时继续离线，不花API/cloud费、不填凭证。

核心矩阵：固定skill / 普通trace总结 / 单谱系update skill / 完整EA × runtime verifier开/关。全部共享任务、初始skill、模型、turn上限、外部测试机会与评估方式。优先固定skill best-of-N：给它与EA相同总rollout、总token、模型角色调用或等值计算额度，并分别报告“相同rollout”“相同tokens”“相同verifier秒数”的Pareto曲线；单一预算口径不足。不给摘要baseline故意缩短上下文或只看成功例。

真正no-verifier evolution应只看可见trace和自检，不能把C3（仍有终验标签选择）当它；终验反馈是否用于学习是单独因子。auto-compact只改变rollout内状态表示，固定其触发阈值、长度和模型调用成本，再测外层演化的边际作用。

## 2. 先锁定适配集，再冻结skill评估

把任务内adaptation表现、同任务fresh rollout、同家族新任务、跨家族新任务四层分开。适配只能访问预算内training-verifier；最终holdout用未反馈的新tests、变换规格或独立任务。训练/测试按repo与family分组，禁止仅按JSONL行随机split。发布测试独立性说明，但不泄露restricted harness。

Primary endpoints：固定预算下真实终验通过率、首次成功耗token/工具秒、冻结skill相对seed在fresh seeds的收益。Secondary：编译/仿真进展、无效候选比例、反馈拒绝率。每个search lineage才是统计重复单位；不能把同一skill的4个rollout或80次自适应尝试全当独立实验。

## 3. 对“skill”的内容做可证伪干预

冻结同一批真实lesson，比较原skill、长度匹配普通总结、打乱/去掉任务特定教训、只保留工具约束、只保留path grounding、随机同长度无关教训。干预后真正执行新的rollout，记录skill是否被读取、关键操作是否发生。对NoobsCPU路径/include经验与PCIe退化案例分别分析，避免只选择成功故事。

当前公开数据只能重排，不能恢复完整evolved skill，故不得伪造原始skill消融。若作者提供经许可的skill快照与独立seed轨迹，可先补所有lineage而非再挑一个最好例子。

## 4. 检验信用分配而非重复验证相关性

建立完全不消费最终reward/hidden stderr的progress函数，预注册后用独立数据校准，再比较sparse-only、该strict proxy与历史outcome-aware proxy。需要证明它能在**最终都失败**的人口中选择更有希望的策略，并在后续fresh rollout上兑现，不能仅用总体AUC。

语义floor/retention gate的false rejection也要测：它可能防止遗忘，也可能挡住必要的策略改写。本轮已有11/80个人口在去gate重排时变更赢家，值得作为候选分析集合，但没有后续执行不能称成功机会损失。Adherence必须真正instrument，不要把默认1.0当机制证据。

## 5. 与既有方法公平接轨

GEPA应使用其真实反思、候选选择/组合逻辑；ACE应保留bullet ID、增量delta与确定性合并；ACE-RTL模型专门训练部分独立标注。先将它们适配到同一个task/tool/verifier接口，再共享evaluation wrapper。若实现删减，名称写“简化的X启发方法”，不得冒充原baseline。报告所有oracle/mutator/repair/compression调用、重试与container计算。

## 建议的继续/停止门槛

完成一个免费live任务的真实tool/验证闭环后再扩展；若fixed-skill搜索在等token+等验证预算下已解释收益，停止“新演化机制”的强novelty表述，转向开放可复用EDA工具接口或成本控制研究。若冻结skill在独立任务上保持收益，再研究可迁移技能结构。即使没有正结果，发布可执行协议、失败记录和预算曲线也比不受控的640次重复更有价值。
