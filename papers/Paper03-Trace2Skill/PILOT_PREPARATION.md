# 第二轮：Northern Relay 免费资源的无凭证准备

**状态：准备与离线接口测试完成；真实模型请求0，真实RTL/verifier执行0。** 本版本 `LIVE_ENABLED=False`，没有实现真实HTTP transport、没有启动server，也不提供绕过此锁的CLI。所有 mock 只验证接口与策略，不是live复现。

沿用 `reproduction/trace2skill-mlcad2026` 和原环境；未安装软件、未pull/build镜像、未配置或读取凭证值、未调用服务的任何路径（包括models listing/health probe），未push/PR。收到的非秘密服务配置仅写入源码与计划：

- Base URL：`https://models.northern-relay.com/v1`。
- API：**Chat Completions**，远端只计划 `/chat/completions`；不用远端 Responses API。
- 完整model ID：`Qwen/Qwen3.5-397B-A17B-FP8`。
- Secret变量名：`NR_API_KEY`；最初未检查；收到用户完成vault设置的授权后，仅核验变量名存在性，结果 **NR_API_KEY_present=false**；未读取值、长度或任何变体，未索取凭证。
- 凭证到期：**2026-11-03 23:38:17 UTC**。不因系统本地时区改变含义。
- 账号共享上限：5M tokens/day、60RPM、500kTPM、并发4。不是本任务可独占预算。本任务仍等待父线程启用，当前预留额度0。

## 已实现并运行的离线内容

`pilot/chat_adapter.py` 仅接受显式offline mock transport。请求包含精确model、Chat格式messages/function tools、`stream=false`、`n=1`、`parallel_tool_calls=false`，最多一个tool call。解析JSON arguments、usage与finish reason，拒绝未知工具/多tool/格式错误，不自动执行返回内容。`send_live()`无条件在任何凭证访问或网络行为前失败。程序不访问环境secret。

`pilot/protocol_bridge.py` 是未来**本地**NeMo Responses facade 的纯转换层：developer显式映射system，input/output text映射Chat，function_call/call_id/function_call_output与Chat tool_call_id双向保持；远端仍是Chat。未知item、orphan tool result、multimodal、reasoning item和未支持state字段失败即停。该转换没有接入FastAPI/NeMo服务器，返回的Python字典尚未通过真实NeMo/Pydantic整栈验证；它不是完整可启动的模型服务。Qwen的实际tool-call格式、reasoning replay需求与provider参数兼容性尚未live验证。

`pilot/preflight.py` 无网络、仅检查变量名存在性布尔，不读取凭证值；另做本地资源检查；Docker只查询版本/本地镜像。`pilot/prepare_plan.py` 生成8条**未执行**rollout计划，不调用模型或verifier。

执行命令（在本目录）：

```bash
cd pilot
python3 -m unittest -v test_chat_adapter test_protocol_bridge
python3 preflight.py
python3 prepare_plan.py
```

**44/44 unittest 通过。** 36项client/预算/隔离测试＋8项protocol conversion测试。主要覆盖精确model与endpoint、文本/工具call roundtrip、usage校验、token/request/RPM/TPM/单并发gate、超额配置拒绝、UTC到期与安全余量、401/403全run停止、429数字/HTTP-date Retry-After与有限重试、timeout不盲重试、截断不隐形修复、unknown tool/arguments拒绝、脱敏日志、实际子进程环境不继承synthetic secret。adapter测试在patch socket禁止网络的条件下运行；转换测试完全不含网络调用。日志见 `logs/pilot_adapter_tests.txt`，机器资源/计划见 `metrics/pilot_preflight.json` 与 `metrics/pilot_plan.json`。

## 硬预算与失败语义

**提议而未启用**的本任务局部天花板：100,000 token reservation、40次请求attempt（含重试）、**全实验共享最多4并发**、60RPM、500kTPM、900秒wall、每请求30秒timeout、每生成最多1,024输出tokens。不会把每日5M额度分配给每个任务；父线程还须在账号级协调其他任务。

输入需要可信的Qwen tokenizer/chat-template计数，输入+最大输出在发出前预占，**不退还**错误/不确定请求reservation。当前没有经过核验的tokenizer/template和provider隐藏reasoning计费契约，缺counter直接拒绝调用；测试中的counter只是mock。局部 admission 硬上限不等于已证明provider实际token上限：必须先验证计数/`max_tokens`语义，不能以字节数估计假装精确硬预算。已知usage超reservation立即halt；缺失/不一致usage也halt。请求数与已声明reservation可确定限制，实际未计数的远端token不可追溯保证。

401/403立刻停止整个run。只有429允许至多一次重试，要求有效Retry-After；大于30秒、跨到期安全线、超过attempt或总预算时直接停止，绝不提前重试。timeout/连接异常视为可能已计费，保留reservation、halt、无盲重试；其他HTTP错误不自动重试。输出length截断不自动重生成或修复。任何后续显式repair/reflection都必须独立记purpose和费用。

到期前预留60秒安全余量＋30秒请求timeout，距离到期不足90秒时拒绝新请求。rolling rate不足直接停止，不排队消费未来额度。日志allowlist包含：UTC时间、purpose、arm/rollout、attempt、HTTP status、reservation、usage、finish reason、耗时及停止结果；不含Authorization、secret、原始error body、prompt/RTL/工具文本或模型reasoning。

## 极小真实任务的计划

任务拟选官方 `cvdp_agentic_heavy_schoolMIPS_0012`（cid016），因为其公开repo bundle约9.8KB，是八个原任务里小的真实仓库；实际材料未取得，无法保证task context或harness也小。数据版本固定 `5b807d945f6a99aa645f7e43a64a2115e281b4bf`。若材料/验证器不合条件，停止并重新定范围，不替换成toy通过样例冒充CVDP。

同任务运行 fixed seed skill 与 evolution，各g2/p2/r1，即每arm4次真实rollout，共8次；max agent model turns暂定4以限成本（原论文30，因此只是canary，不可作论文数值对比）。先做人工或已审阅reference的verifier正/负smoke，确认工具链不会把所有答案都判同一值；不让agent看到reference或hidden harness。然后按generation交错fixed/evolution，最多4个共享并发（同一generation最多fixed/evolution各2条，四角色共享一个controller），每次终验用同一已固定digest的真实harness。runtime dense feedback先关闭，避免内层新观测掩盖外层skill变化；后续dense是另一个实验，未授权自动扩展。

Evolution gen1包括seed和一个初始化mutant；基于两候选实测结果选择survivor，再反思两者成功/失败并生成一个child；gen2重新评估parent与child。fixed每轮保持同一seed。rollout生成最多32次请求，初始化mutation1＋reflection1＋后续mutation1＋最多两次显式repair，共名义37，**所有重试合计仍不能超过40**。预算不足时记未跑，不补齐或借用别的任务额度。工具/verifier各记exit、pass/fail、wall/CPU或container秒数、调用次数、失败/超时；模型账分别记每次生成、修复、反思、压缩与重试。最终报告fixed/evolution两arm全部token/请求/终验开销，不能只对齐rollout数就称匹配总预算。

此小试只是接口/闭环 canary，不能估计外层机制因果优势。真正budget-matched efficacy实验仍应按 `RESEARCH_OPPORTUNITIES.md` 设计，不启动sweep。

## 凭证隔离设计与实测边界

模型client将来只在单独的受控broker进程安全取得NR_API_KEY；本轮没有此读取路径。worker通过正面allowlist重建环境（PATH、HOME、TMPDIR、LANG、LC_ALL），不使用`os.environ.copy()`；已实际执行Python子进程验证synthetic父进程secret及NR_API_KEY均未继承。没有在测试中设置NR_API_KEY。

真实生成/编译执行器尚未实现：未来必须让broker与worker分开用户/容器空间，worker无secret文件/父进程可读接口，禁止挂载凭证、Docker socket和账号目录；任务volume限特定工作目录，network none、read-only根、cap-drop、no-new-privileges及CPU/memory/pid/wall limits。这里只记录设计，**未改变安全设置或声称容器隔离已实测**。命令参数应严格按工具schema与目标文件allowlist执行，禁止任意shell。隐藏harness只在private verifier，reference不可进入agent sandbox。

## 精确阻碍与后续启用顺序

| Action / target | 原因 | Status / 已完成 |
|---|---|---|
| 下载固定revision官方CVDP JSONL | Hugging Face原URL返回HTTP403 | **denied by remote HTTP；明确未取得，停止且未重试/绕过**。预期SHA已取自官方下载器 |
| 真实schoolMIPS verifier smoke | 任务材料缺失，iverilog/vvp/verilator/yosys均缺，本地Docker镜像0 | **未尝试**；Docker daemon 28.4.0本地查询成功 |
| 接入完整NeMo执行 | openai/ray/pytest未安装；本地model facade尚未接线、整栈schema尚未测试 | **未尝试live**；纯转换与客户端44项测试完成 |
| 确保token硬界限 | 缺已核验Qwen tokenizer/template及provider计数语义 | **pending**；缺counter拒绝请求测试通过 |
| 真实服务请求 | 本轮禁止真实请求；父线程未启用执行，当前旧任务NR_API_KEY_present=false，逐域名授权unknown | **未尝试**；无凭证读取或网络probe |

下一步必须先处理可合法取得的真实任务与verifier环境，再完成本地facade和已核验token计数，父线程明确启用账户局部预算并安全提供secret后，才考虑一个任务的首个live请求。当前没有自动审批拒绝、没有不确定的模型调用或远端写入。数据403不通过改header/镜像/代理或换设备绕过。


### 最后一次即时就绪核验

在用户报告完成Personal vault设置之后，本任务实际只检查环境变量名存在性，得到 **NR_API_KEY_present=false**。目标 `models.northern-relay.com` 的逐域名授权状态为 **unknown**：本环境只显示general network enabled，没有域名清单或可用的vault/network授权元数据工具；未用请求/health probe“验证”。环境工作正常，不新建替代线程、不切换Mac、不改权限。需平台将secret与目标域名授权实际投递到本任务；用户已设置的证据不等于此旧任务已收到。

共享并发新增四项mock测试：所有role/arm client引用同一个ExperimentController/Budget；4个lease允许、第5个拒绝；4个真实Python线程持有共享lease（没有API）并释放；429重试只释放自己的一份lease而不影响其他正在运行的请求。实现是**单broker进程内**共享，不是跨进程分布式limiter；未来不能每个worker独立建立controller。
