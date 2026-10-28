# 客户端审计修补：解码凭证回显与异常usage结算

**Outcome：fixed（限定以下两项已复现的问题）。本轮真实凭证读取0、网络/模型请求0、新EDA执行0。live继续禁止，等待父线程审计通过。** 原有14次真实fixture仿真是历史接线证据，没有在本轮重跑。

## 漏洞与最小修补

1. HTTP响应原字节中查不到Unicode escape编码的凭证，但json.loads后会出现原值；可经正文、嵌套metadata/reasoning、字典key到达Canary的response hash、validated_skill_state/validated_lessons或RTL保存路径。已用合成supplier与Mock opener复现，未接触真实key。
2. HTTP200 `choices=[]` 与 `usage=null` 导致usage_total调用null.get；异常发生在except Stopped里的finish，遗留active=1、in_flight。本轮复现了AttributeError和该残留状态；没有证据将此推断为实际超额消耗。

生产代码仅改两个文件：

- `pilot/live_transport.py`：保留raw字节检查；解析JSON后迭代检查所有字符串值、dict keys、list成员，涵盖未使用的reasoning/extension字段。相同检查用于HTTP错误的有界body，错误文本仍不返回；Retry-After精确值检查后仅保留合法数值/日期，无效opaque文本不向直接调用方传播。supplier、网络、JSON和错误body读取/关闭异常变为固定Stopped，且在except块外抛出，不把第三方异常文档或消息挂在cause/context上。原有成功响应tuple、合法JSON与合法Retry-After行为保留。
- `pilot/runtime_accounting.py`：新增一行非dict usage guard，将null/list/string等视为unknown，保留满reservation；不重写finish或放宽已有整数/总和校验。合法usage在malformed choices时仍结算，bool和非法usage不作为已知token数。

直接caller与sink一并检查：AccountedChat仍先经过transport，再返回content；Canary在返回后才hash/存skill/source，阻断点位于这些sink之前。错误响应不返回body/原始异常原因。没有修改模型配置、外部凭证、Vault、网络、安全设置、预算或实验框架。

## 验证

- 语法/import：变更模块与新测试py_compile通过。
- 新增 `pilot/test_client_security.py` **19项测试**：plain echo、首字符Unicode escape、嵌套/unused reasoning、dict key、400/401/429/500错误body、Retry-After、transport/supplier/解析/读取异常、artifact/hash sink、placeholder契约；null/list/string usage × malformed/truncated choices，并检查一条尝试、一回finish、active=0、terminal状态、满额未知计费、不盲重试；sleep失败不双重finish。还有有效JSON/Retry-After及null usage正常content的合法控制。
- 原有69项＋新增19项：**88/88通过**，显式安全env白名单启动；有transport的测试禁止真实socket，HTTP opener、supplier全为合成/mock，verifier替身禁止调用EDA。
- 独立只读review未发现具体残留绕过/回归；另外77例malformed choices/usage矩阵通过，均为一次transport、一次finish、active归零与terminal账本。reviewer未改文件。独立review执行时为18项新增＋69项原有；随后补充1项错误关闭异常回归，生产patch未改，最终88项由本线程全部复验。
- 原触发已不复现：合成escaped凭证被transport拒绝，未到达hash函数、skill/lesson/source artifact；固定异常str/repr/traceback/属性无该值且cause/context为空。null/list/string usage的失败响应保守结算且释放active。未保存响应原文或合成凭证派生hash作为审计输出。

命令（本目录内）：

```bash
cd pilot
python3 -m unittest -v test_client_security
python3 -m unittest -v test_chat_adapter test_protocol_bridge test_runtime_accounting test_client_security
```

机器证据：`metrics/prepatch_client_audit.json`（仅布尔/类型/状态）、`metrics/client_fix_review.json`、`logs/client_security_tests.txt`、`logs/pilot_adapter_tests.txt`。测试case内部含明确的合成fixture构造，不是实际credential。

## 保证边界与待审条件

这里阻止的是**进程持有的精确注入值**在JSON解码后的回显（包括其作为较长字符串的子串）。它不是任意base64、分片、变换、其他秘密或内存取证的完整防泄漏系统，也不支持将第三方异常frame locals整体导出。客户端仍不得记录原响应、全环境、Authorization或traceback locals。

若平台Network secret在进程里只有placeholder，实际vault值由平台在别处注入网络，则本检查只能识别placeholder，**无法据此识别进程未知的vault真值**。此次只用合成字符串测试了可见值契约，没有读取真实key、验证平台注入语义或改变外部设置；父线程必须审计这一边界及平台侧日志/回显控制，才能决定是否启用live。不能把“placeholder测试通过”说成“真实vault凭证绝不泄露”。

Token计数仍是先前明确标注的保守估计，provider实际硬token上限未被证明；本修补没有改变该结论。没有阻塞本地两项修补验证的剩余工具缺口，但实际接入与live审计仍待父线程处理。
