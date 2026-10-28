# 最新就绪状态：免费真实模拟器与隔离（2026-10-28）

**完成：真实Icarus工具链、host与Docker正负控、隔离实测、45项离线客户端测试。没有任何真实API请求。** 先前PILOT_PREPARATION的缺模拟器/无镜像段落属于历史状态；原CVDP数据403、模型注入/授权/计数/整栈接线仍是独立问题。

## 实际执行与成本边界

- Debian13 amd64官方iverilog **12.0-2+b1**，先验证InRelease的Debian归档签名（系统受信keyring、禁自动取key），再验证签名覆盖的软件索引与包SHA-256；包hash为 `febe027d2d3f5a7e570844d55758339ab5490acc09f404f214a8719d89d07056`。
- `dpkg-deb -x`只解包到 `/workspace/free-tools/iverilog/root`，不运行maintainer脚本、不系统安装。`/workspace/free-tools/bin`含明确prefix的iverilog/vvp wrappers。二进制依赖由当前Debian已装共享库满足，无API/cloud费用。
- **host真实仿真2次：**官方CC0 adder正控 exit0；人工OR错误负控 exit1。不是模型生成的代码。
- **Docker真实仿真2次：**同样正控通过256组穷举，负控因adder mismatch失败。共**4次实际RTL仿真**。编译次数各对应一次，不与模型rollout数混算。
- Docker镜像从scratch在本地构建：官方已校验Icarus＋当前系统shell/必要动态库，无网络build步骤、未pull未知镜像。固定本次image ID：`sha256:5ca5a8b42e0bd12da72852a33d5d50ef45de6e0e8949edcae6cd288d7608b509`。
- model/API请求 **0**，LLM生成/反思/更新skill **0**，mock测试不计live，实际CVDP hidden verifier **0**。

证据：`metrics/pilot_isolated_verifier.json`保留每控耗时/退出码/源码hash/实际检查，`metrics/verified_toolchain.json`与`pilot/toolchain_provenance/`保留签名、索引hash、包stanza、库hash和Dockerfile。ZIP不打包系统二进制或镜像；有可核验重建脚本。

## 真实隔离保证与剩余缺口

实际容器user65534:65534、network none、rootfs只读、源码volume只读、cap-drop ALL、no-new-privileges、1 CPU、256MiB、pids64、/tmp仅64MiB且noexec/nosuid，外层30秒timeout。启动前inspect验证有效配置；容器里NR_KEY不存在、Docker socket不存在；尝试写root及源码均被拒绝。只挂两个专门的公开fixture文件，未挂账号目录、凭证文件或宿主源码树。测试与所有外部执行命令均通过显式env白名单，不记录全环境。

这些是已有Docker隔离路径的实测结果，不是修改宿主security设置。没有证明内核/容器运行时绝无漏洞，没有测复杂恶意HDL/VPI攻击；仍需保持无特权、禁止任意插件/自选编译参数。Docker daemon控制权仅由可信控制器持有，不能暴露给模型生成代码。尚未建立完整LLM broker服务或agent工具路由，不能称完整运行系统隔离全部达标。

`bwrap --unshare-net`失败：uid map只读，未重试修改设置。Docker第一次非root启动exit126、未执行RTL：本地镜像/bin与/lib64因安全umask成为0700。只修正工作区构建目录为0755、tmp为01777，no-cache重建后正负控通过；未提权、未改变宿主权限/网络设置。失败启动不计作verifier样本。

依赖下载最初在无proxy的env白名单中无法DNS解析；后续只向**可信下载器**传现有HTTPS_PROXY等明确网络变量，未读取NR_KEY或其他凭证、未输出proxy值。模型/RTL worker环境不传这些proxy变量。原CVDP403没有重试、换header、镜像或绕过。

## 当前可直接运行

在仓库 `papers/Paper03-Trace2Skill` 下：

```bash
# 全部离线客户端/预算/expiry/脱敏/并发/子进程检查；不发API请求
cd pilot
python3 -m unittest -v test_chat_adapter test_protocol_bridge
cd ..

# 当前环境已有已校验包与镜像；脚本内对外部子进程使用env白名单
python3 pilot/prepare_toolchain.py
python3 pilot/verifier_fixture/docker_smoke.py
```

不要为了重复证明基础设施而大批重跑。运行docker_smoke将新增2次真实仿真，应写入新的运行ledger，而不是覆盖累计次数。

若迁移到父线程另行配置的私有Debian13 amd64环境：

```bash
# 仅在已有普通依赖安装授权的环境，由可信控制器执行；不会调用模型或读取NR_KEY
python3 pilot/prepare_toolchain.py --acquire --build-image
# 用上一步实际输出的不可变image ID替换下行参数
python3 pilot/verifier_fixture/docker_smoke.py --image-id sha256:<inspected-image-id>
```

脚本拒绝非已审阅平台、变化的release/hash和下载失败，不自动换源或新版本。build使用当前系统库，跨机器image ID可能不同，必须记录；不要伪装历史位级镜像。迁移需gitbundle内报告/脚本及从官方源取得的依赖；当前`/workspace/free-tools`和Docker daemon镜像不随Git提交携带。工具脚本不修改Vault、model域名、安全策略或NR_KEY。

## 下一步真实任务与对照

**科学目标仍选择原论文 schoolMIPS_0012 / cid016**，固定CVDP revision、原task/harness与seed skill。当前官方JSONL403且bundle/harness未取得，不能启动它；这不是缺API key能解决的问题。需合法访问恢复或有权提供固定材料；不绕过403。若取不到，记录原task NoGo，再单独选择另一合法公开任务并明确portability，不能把adder当论文结果。

adder仅基础设施smoke，虽然使用真实编译器/仿真器、真实RTL及功能断言，复杂度很低且负例为人工注入，不能为Trace2Skill外层演化有效性提供证据。

原task准备好后：一个任务，fixed seed skill与evolution各g2/p2/r1，按代交错；同代最多4个全实验共享并发。fixed不更新；evolution保留parent＋child，来自该任务两候选全部成功/失败trace的反思，child下一代实测、parent也重新评估。初次关闭dense反馈，避免将额外verifier观测混同skill演化；每arm4rollout，turn cap4，明确偏离原30。此为有界机制canary，不是效能/泛化结论。反思/修复/生成/重试计入各arm真实token与费用；同rollout数不等于总预算匹配。

## Live前仍必须完成

1. **NR_KEY与目标域名：**上次当前task存在性false、域名许可unknown；父线程正在用户单独批准后配置。本线程未并行修改、未读取key、未探测endpoint。需父线程实际确认注入和逐域名元数据，再明确启动；All environments范围用户已接受，不要求缩小。
2. **可信token计数：**Qwen tokenizer/template及provider reasoning/max_tokens计量契约未验证。缺counter拒绝请求；不能用粗字节估计声称实际token硬界限。共享4并发、100k首轮reservation、40attempt、60RPM、500kTPM、过期停止保护保持。
3. **真实task材料：**原CVDP403仍阻塞；真实Icarus工具已补齐，不能用smoke代替原hidden harness。
4. **实际Chat broker/agent接线：**纯协议转换与mock已测，但真实HTTP transport与NeMo本地facade整栈仍未实现/运行；父线程启动前须完成，不能发送远端Responses请求。可以用已有stdlib Chat客户端减少OpenAI/Ray安装，但若改orchestrator需记录协议/调度差异，不能隐称原框架。
5. **模型生成代码仅进隔离worker：**不可因为host smoke成功而在host执行未来生成代码。将来的live broker只持NR_KEY，worker只收task文件与allowlisted参数。

以上未就绪时应停在真实模型调用前，继续可独立的准备工作；没有自动审批拒绝、付费、push/PR或新增环境。
