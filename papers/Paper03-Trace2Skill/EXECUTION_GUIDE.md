# 最终执行入口：Chat → skill / rollout → 真实隔离verifier

**普通接线已完成。** 当前默认不启动网络，不读取真实凭证。本轮真实模型API请求 **0**；累计真实RTL仿真 **14**。原CVDP数据403不变；下面入口只运行合法公开的adder基础设施fixture，不能用于宣称Trace2Skill科学复现或方法优势。

## 父线程确认接入后的一条启动命令

工作目录为 `papers/Paper03-Trace2Skill`：

```bash
python3 pilot/run_canary.py --live --approval /workspace/private/nr-canary-approval.json --out runs/nr-fixture-canary
```

无需改代码开关或再补Chat/agent接线。父线程先从 `pilot/parent_approval.example.json` 准备私有的非秘密授权JSON，确认实际NR_KEY注入、目标域名权限并明确激活后，将 `parent_approved` 与 `secret_injection_confirmed` 设true。模板默认false，已实际测试会在任何secret读取或网络前返回 `BLOCKED_BEFORE_SECRET_OR_NETWORK`。授权必须接受fixture-only、保守token估计、全实验100k及共享4并发范围。此文件不存key。

程序用原子 `.started` 标记保证同一授权只启用一次；输出目录拒绝覆盖，不能用重启重置100k。若环境/接入失败，保留账本，由父线程核对网络尝试与不确定结果后再决定新授权，不自动重跑。NR_KEY是唯一变量名；不读旧变量、不回退、不改Vault/网络/安全设置。

本轮**没有**执行上述live命令。已经执行的是默认plan、false授权的fail-closed检查、Mock Chat加真实verifier接线检查。默认 `python3 pilot/run_canary.py` 仅输出计划。

## 具体闭环与保真边界

新入口是自包含stdlib Chat orchestrator，不要求安装NeMo/OpenAI SDK或Ray。`live_transport.py` 实现唯一远端 `/v1/chat/completions`；不调用Responses、models listing、health探测，不跟随重定向，不做SDK隐式重试。真实key只在通过授权/期限校验、已有预算reservation的实际transport调用中惰性取得，作为HTTPS头发给固定域名，不传给任何子进程。响应若回显同一key，拒绝在artifact/hash中保留它。测试用的是synthetic supplier＋Mock opener，不曾读取真实key或连服务。

`run_canary.py` 将Chat内容依次用于：

1. 生成初始skill候选。
2. 在fresh rollout中注入skill，生成一个RTL候选。
3. 拒绝超长/敏感内容、系统任务和include等不适于此小fixture的代码；将候选作为数据放入只读volume。
4. 真正Docker/Icarus compile＋256组输入仿真，返回terminal pass/compile fail/functional fail/timeout。
5. 基于两候选全部成功/失败记录反思，更新skill；按真实pass选择survivor、tie取最低index。
6. 第二代fresh调用重评parent并评估child，不复用旧fitness。

`--repair-attempts 1` 可启用每rollout最多一次显式修复，作为独立purpose/attempt计费与记账，绝不隐形重生成；默认0便于完整名义预算canary。修复路径已经用Mock错误RTL→真实失败→Mock修复→真实通过的两次隔离仿真验证。

这保留task-local技能复用、实测候选选择、失败反馈与parent重评；**不是完整论文框架**：每个rollout是单次RTL生成加可选一次修复，没有长上下文仓库工具探索、官方多层oracle、SkillQ/语义floor、累计lesson bank或runtime dense feedback。两代仅一轮反思更新。称为简化机制canary，不冒充原实现、GEPA或ACE baseline。

## 固定skill对照与匹配方式

一个public fixture，两代×两候选×一repeat，每arm4次rollout，共8次真实verifier。在fixed arm，skill一直是相同seed；evolution采用测得survivor和新child。为了匹配额外角色调用，fixed也执行相同的初始mutation、reflection和mutation **shadow slots，但丢弃更新**。正常完整路径每arm7次Chat调用：4生成＋2mutation＋1reflection，总14。两arm每次最大输出1024，按代交错，每代最多4并发，全实验只有一个共享Ledger。

这是“更新是否被应用”的机制控制，**不是**实用的固定skill best-of-N成本最优基线；无用shadow调用会浪费固定控制预算，文档与账本明确标注，不把它伪装成论文baseline。两arm各50k reservation上限、总100k、相同名义角色slots，但真实usage、失败/重试或repair可不同，必须报告实际成本，不能称精确实现成本相等。任何token/request预算耗尽都保留未跑/停止，不借额度补齐。

默认每attempt最低预留6144，正常每arm7×6144=43008（两arm86016）。若真实payload估计更大，按更大值预留；每arm至多约8个最低reservation，总请求还有40attempt上限。额外429或repair可能使后续步骤受预算拒绝，这是预期有界停止，不自动扩大预算或sweep。

## Token计数与结算

优先尝试了官方 `Qwen/Qwen3.5-397B-A17B-FP8` 的 tokenizer_config 下载，curl exit22（HTTP错误，具体status未保留），未取得字节，未换镜像/绕过。没有下载权重。已读[官方model card](https://huggingface.co/Qwen/Qwen3.5-397B-A17B-FP8)，采用其 `chat_template_kwargs.enable_thinking=false` 请求非thinking模式；此服务是否接受仍只能在被授权的首次live调用中确认，不自动切换参数重试。

当前计数为**保守估计**：整个canonical JSON的UTF8字节数＋2048模板余量，再加最大输出；每attempt至少6144。它不是官方tokenizer精确计数，也不能证明provider隐藏模板、reasoning或max_tokens语义下的实际硬token上限。不能用本地reservation账本声称provider实际必低于100k。

每attempt发出前先持久化reservation；失败、429、反思、mutation、repair都入同一账。合法response usage会结算实际charged tokens；缺失/不一致usage或不确定transport扣满reservation。admission累计reservation不退款，避免重用预留形成额外搜索预算；known usage只用于真实charged统计。若usage超过reservation，结算实际值并halt后续请求，记录估计失效，不能追回已发生超额。

全局并发4、60RPM、500kTPM、40attempt、900秒wall、socket timeout30秒；429只容许一次且尊重Retry-After，超过30秒/到期余量/预算即停止。401/403及其他HTTP不兼容错误停止新调用；已在途请求不能保证远端撤回。timeout不盲重试，费用按未知保守处理。到期 `2026-11-03 23:38:17 UTC` 不变，每次预留90秒请求/安全余量，并重新校验授权有效期。

## 实测证据，不能混算

| 检查 | Chat来源 | 真实RTL验证次数 | 意义 |
|---|---|---:|---|
| host正/负控制 | 无 | 2 | Icarus能区分正确/错误RTL |
| Docker正/负控制 | 无 | 2 | 编译仿真及隔离配置实测 |
| 完整两arm两代接线 | 14次Mock Chat | 8 | 6 pass/2 functional fail，证明响应→skill/RTL→真实verifier路径；无模型表现结论 |
| 单rollout显式repair接线 | 2次Mock Chat | 2 | functional fail→pass，证明修复记账与重新验证 |
| 69项unit tests | 全部离线、禁止真实socket | 0 | 协议、预算结算、到期、重试、重定向、脱敏、共享并发和子进程环境 |

累计真实fixture仿真14，真实CVDP hidden verifier0，真实模型请求0。Mock usage120等是接口测试数据，不是实际消耗或成本。证据见 `metrics/end_to_end_fixture.json`、`metrics/end_to_end_repair.json`、`metrics/token_accounting_audit.json`、`logs/pilot_adapter_tests.txt`。

实际隔离仍使用已验证镜像ID、user65534、network none、只读root/source、cap-drop ALL、no-new-privileges、CPU/memory/PID和tmpfs限额。模型key与proxy都不传worker，不挂Docker socket、凭证或账号目录；所有Docker子进程env白名单。生成代码只进容器，不在host执行。没有证明内核无漏洞；此小组合RTL另有限制system tasks/directives的静态gate，不能当通用不可信EDA代码沙箱的完备证明。

## 可复验命令与原数据边界

```bash
cd pilot
python3 -m unittest -v test_chat_adapter test_protocol_bridge test_runtime_accounting
cd ..
# 这条会新增8次真实仿真；Chat全为Mock。必须选新目录，不覆盖既有记录。
python3 pilot/run_canary.py --offline-integration --out runs/offline-wiring-check-new
```

当前原环境工具与镜像已存在；迁移方法见READINESS_UPDATE。新增脚本不需要额外Python依赖。`runs/`被gitignore，包中保留已脱敏机器摘要，不提交未来真实prompt、provider reasoning或受限材料。

**剩余是接入/授权与真实研究数据，不再是普通Chat接线。** 父线程确认NR_KEY实际注入和域名许可，准备单次授权后即可运行fixture live canary。若要回到原科学目标，schoolMIPS_0012仍须取得合法固定CVDP task/bundle/harness；原403未被绕过。这个接口入口不把adder替代原task、不把其通过率当论文结果。原框架的仓库级工具、指标与长轨迹需要在真实材料可用后作为独立实验接入，保真边界必须继续报告。
