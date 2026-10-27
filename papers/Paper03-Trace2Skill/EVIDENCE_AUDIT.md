# Evidence audit

证据优先级：本地可解析公开记录 > 冻结说明 > 当前 README/网页 > 论文数字。公开记录是作者从私有原始 archive 允许字段提取的二级证据；hash commitment 不等于已拿到私有原件。所有结论仅限公开资料。

## 可追溯的重大差异

| 项目 | 论文 v1 / 宣称 | 冻结证据与本轮核验 | 审评影响 |
|---|---|---|---|
| C1 / C2 | 表3 列 0/32 与 4/32 | docs/RESULTS、expected_results、validator 明确占位值撤回 | 不支持 evolution-only 或 dense-only 的干净归因 |
| SelectQ | U=.60 LCB+.20 mean+.20 SkillQ | validator/run_optimizer 与 lineage 决策为 .55/.15/.20/.10 adherence | 199/320 数值不符；80 人口内赢家一致，不代表其他搜索等价 |
| adherence | 作为质量字段 | 320/320 默认 1，未有 monitor observation | 常数只给所有有效候选同一偏置，没有遵守度测量 |
| 高 AgentQ 相关 | r≈.90、AUC≈.982 | agentq96 README 指出 F_progress 用最终 reward/隐藏 verifier 输出 | outcome-conditioned 描述不能独立证明失败间 credit signal 有效 |
| strict progress | — | 独立 pairwise AUC=0.6779956427；未用于原优化 | 有较弱相关但不是已验证的替代优化收益 |
| 初始硬任务 | seed 筛选失败 | 后续独立 seed 审计八任务 5/32：async-fifo 4/4、fpga_nes 1/4 | 筛选噪声/回归均值；不能替代 C1 或称“任务必定失败” |
| quality 曲线 | valid-candidate 均值 | C3 eligible 32→26→24→17→14，C4 32→27→14→17→15 | 人口构成变化，均值升高不证明所有策略进步 |
| 历史源码 | paper implementation | 原 launch 均 dirty；C3 非 skill 改动不完整，C4 恢复14文件 patch | 发布源码是可携带重建，不是历史位级快照 |
| 历史 prompt | 可访问当前 prompt | 22条路径，21条 exact hash match；analyzer 历史文本缺失 | 不能完整重现历史 analyzer 行为 |
| baseline Codex | 12/24 | provenance 是 retrospective reconstruction，mutable image latest、CLI build 无法恢复 | 上下文对照，不是 matched architecture/预算实验 |

来源均在原样保存的上游 `docs/`、`artifacts/paper-results/evidence/` 和 `historical_prompts/`；对应文件 hash 在 `metrics/source_hashes.json`。论文的不同公式见 [§2.2.5 与 Algorithm 1](https://arxiv.org/html/2605.21810v1)。

## 分组、失败与成功样本偏差

完整 rollout key 是 (task_id,generation,individual_index,repeat_index)，quality key 少 repeat。独立脚本验证完整 8×5×4×4 网格与 quality/pass fraction 的一对多连接。`repeat_index` 是归档行序；官方 action example 的 scheduler repeat=2 与 storage ordinal 分开保留；没有 seed-level pairing。

已保留结果只有 pass/fail 且 reward 对应 1/0。C3 失败分类：411 simulation/assertion，27 exploration-only，24 compile_error，4 no_simulation_after_compile，1 hidden_verifier_or_semantic；C4 为 388、8、21、8、0。mode 是作者派生分类，本轮不能重看 raw stderr 验证分类准确性。

官方两条 action trace 被挑选为 C3 failure 与 C4 pass，同任务、gen1、ind0、scheduler repeat2、同 seed-skill hash。它们独立采样，不能称 matched counterfactual。内容只剩工具名、顺序、尺寸/hash 和 allow-listed scalars；不能恢复 RTL/命令/语义正确性。它们可展示内层修复，无法证明外层演化，因为都在 gen1 的 seed 个体。单个 NoobsCPU gen4→gen5 lineage 也有成功选择偏差；未公开所有完整 evolved skill 文本。

## 重试与隐含预算

`runtime/llm_calls.csv`：C3 762 optimizer wrapper attempt（全部 success），C4 755（753 success、2 errors）。C3 mutation120、repair32、compression27、oracle583；C4 mutation119、repair31、compression16、oracle589。两次 C4 错误之一 auth-class 不重试，另一次 internal-server 在 attempt2 成功。wrapper 最多3总尝试；oracle SDK 可另加一次，Sonnet SDK不重试。公开表不能判定 wire-level 次数。

`rollout_retries.csv` 公开4次 collection retry：C3 NoobsCPU g1i1/g1i2/g5i1，C4 NoobsCPU g1i1，每项5个无效文件被归档且 replacement 存在。存在不代表本轮验证过 replacement 原始内容。collection 配置 initial+3；bridge 内/外总尝试1/3；模型请求层初始5、最高12。这些是错误恢复 policy，不等于额外成功采样次数；也不能用640声称总请求恰为640。失败替换的精确所有 token/容器开销不可辨识。

从16项 run_metadata launch/completion 独立算得 summed task-hours：C3 **42.106503**，C4 **48.034694**（+14.08%）。这不是并行 job 的单一墙钟延迟。optimizer call CSV 可算 token：**7,841,652 / 8,168,008**；只是已记录 optimizer 子集，不是所有 rollout token。官方 README 报约 **374M / 520M** 总记录 token（+39.04%），公开 rollout 表没有 token 字段，因此本轮只做来源归属，不冒充独立重算。monetary API cost 未记录，不能折算美元。C4 至少额外1052次 runtime verifier 执行；终验每条件640次，feedback private copy/仿真与通信开销应独立记账。

## 访问与执行记录

- Zenodo tar.gz 下载：HTTP403；未执行成功，未重试，也没下载 checksum；未走镜像绕过限制。
- arXiv PDF 下载：HTTP403；使用原站公开 HTML 阅读，不声称 PDF 字节已核验。
- 官方 GitHub codeload commit 下载成功；annotated v1.0.0 peeled commit 经 git ls-remote 验证。未取得 Zenodo 字节，两个归档不能比较。
- 仓库 fetch HEAD 报 remote ref HEAD 不存在；只读 ls-remote 两次成功且无refs。不是鉴权/审批拒绝，没覆写现存 branch。
- 首次自编 replay 因 coordinate key 用 repeat_index 抛 KeyError；读 schema 后改为保留完整 coordinate，19/19检查与两条metadata回放通过。该失败未产生在线调用。
- 首次作图 matplotlib home cache 只读，自动用/tmp成功；修正推荐命令指定 MPLCONFIGDIR，图已目视核对。
- 上游未改动；运行 Python 产生的 __pycache__ 不入包。未运行 setup、pip install、Docker build/pull、benchmark downloader、live optimizer。

本轮没有自动 approval denial、没有待授权动作或不确定远端写入。最终边界：公开冻结数据可审计；私有原始日志真实性、完整 hidden harness、历史部署/seed、在线因果关系仍不可独立验证。

提交前的全树 cached whitespace 检查发现上游原有 CRLF/行尾空格和 matplotlib SVG 空格；保留上游字节，清理本轮 SVG 空格。最终仅对本轮 authored 文件做 whitespace 检查，另以180文件逐字节比对证明上游未改。此格式诊断不影响数值/机制验证。
