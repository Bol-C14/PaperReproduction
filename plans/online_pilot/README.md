# 本地冻结：未来在线cost-controller vs开放环

本目录仅准备协议和未发送的payload例子，没有网络transport。未发API请求、未读/写入任何凭证、未传输仓库数据；不修改v3 ZIP或Library身份。保留原分支/历史。

`protocol.json`冻结机械条件与上限；`payload_provenance.json`逐字段列出本地源文件/hash和公开数学/本地synthetic来源。`payloads/`只有匿名synthetic图、成本/分摊和测量，排除了路径、repository/commit、完整RTL/netlist/log、对话和秘密。**内容被判为synthetic不代表已获发送授权。** 两份q0例子字节已hash；未来响应/观察尚未发生，仅其schema/来源约束可冻结。

未来若获明确免费调用和数据发送分配：两个既有验证MCM（W12/W16），同图/规则/起始cost，各arm6真实综合+6 RTL SAT，两个arms总24+24；online最多10次cost-action调用，最后query不再请求无后继动作。open-loop沿用verified结构+3。模型只选有限JSON动作，不能写代码、提议规则或操控工具。一个seed，不扩展benchmark或sweep。原始数值结果不是新在线实验结果。

模型/endpoint/provider/free quota均为空；当前授权API次数与发送次数均为0。父任务的generic认证测试不在本协议内，不视为这里的模型调用许可。服务绑定必须在future执行前另行留痕，token/定价必须确认免费，失败停止，不自动重试补额。当前没有待运行的网络任务。

本地重建/校验：`.venv/bin/python scripts/prepare_online_pilot.py`。不要将示例作为已经获批的请求发出；此脚本没有任何发送实现。当前准备阶段0新增EDA、0API、0费用。接下来的精确阻碍见protocol.json的exact_blockers。

源hash allowlist已固定：仅两个已审查synthetic图及对应q0记录；匿名化私有图不会把它变成公开数据。改变来源即拒绝，不能只靠字段名称宣称非敏感。未来新增观察必须证明来自这些同一synthetic构造，而不是替换为私有benchmark。Provider-specific完整HTTP envelope目前无法冻结，仍是服务绑定blocker；当前冻结的是content schema、provenance边界和两个精确内容例子，而不是可直接发送的已批准请求。
