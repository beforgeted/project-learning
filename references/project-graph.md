# 项目绑定、实验节点与只读画布

## 项目启用

配置位于业务工作区 `project-learning/project-binding.json`，新格式为 project-learning/binding/2。包括 schema_version、business_project_id（绑定组身份）、mode（enabled/manual/paused）、codex_project_id、workspace_root、projects（每项为 project_id 与 record_root）、consent（启用依据）。Codex ID 是宿主关联，不替代稳定业务 ID；名称仅展示，不用于身份匹配。

例如 projects 为 `[{"project_id":"youtube-spam-pilot","record_root":"project-learning/youtube-spam-pilot"},{"project_id":"self-instruct-transfer","record_root":"project-learning/self-instruct-transfer"}]`。目录是工作区内相对路径，必须明确到子目录；重复 ID 或重叠目录会被拒绝。工作区绝对路径与宿主 ID 留在本机配置，不随通用 Skill 分发。

enabled：在当前可见且属于所列业务范围的协作中记录有价值增量。manual：仅明确要求时记录。paused：暂停持续记录；当次明确要求单次记录不更改模式。没有绑定按 manual 处理，不扫描所有用户项目来推断意图。项目列表可访问时核对 ID；工具不可用时只依据已保存配置和实际路径，不虚构宿主识别结果。

一个 Codex 项目可有多个业务子项目，projects 将每个业务 ID 映射到唯一记录目录，记录 ID 含子项目命名空间。写入前明确本次内容的业务归属，再核对实际目标路径；不能为了校验通过反向从目标目录猜测业务身份。路径匹配不证明讨论内容相关，用户意图仍需由当前上下文判断。无法判断归属时先问，不跨目录混写。改名保留业务 ID；迁移目录或 worktree 需登记经核验的新绑定，不能只凭同名或相同 remote 自动认领。跨机器的 Codex ID 可以不同。暂停不删除历史。

在主工作目录的 AGENTS.md 放置读取配置的简短入口；不覆盖已有指令。此机制依赖会话加载指令，不提供后台监听、完整聊天自动读取或必然触发保证。项目启用不等于允许额外模型费用或发布数据。

运行 `python scripts/validate_binding.py --binding <配置> --workspace <实际目录> --codex-project-id <实际ID> --business-project-id <本次业务ID> --target <拟写入的文件>`。target 相对 workspace 解析或使用绝对路径；校验真实解析路径、目录边界、业务 ID、宿主身份及模式。

`valid=true` 仅代表配置可解析；持续归档需要 `auto_archive_allowed=true`。缺少目标、业务 ID 或宿主身份，目标越界、项目不匹配、manual/paused 均不允许持续归档。退出码 0 为满足持续归档条件，1 为配置有效但未获持续归档条件，2 为配置/输入错误。工具不写记录，也不验证 consent 文本是否真的来自用户。

旧 binding/1 可读取诊断，但缺少子项目映射，auto_archive_allowed 恒为 false；只有在有既有授权和明确归属依据时迁移到 binding/2，不自动扩展范围。用户明确要求的单次记录另按请求范围办理，不为了临时写入修改模式或扩大配置范围。

## 实验节点

新格式 project-learning/graph/2：project_id、provenance、nodes、edges。每个 node 包含 id、kind（experiment/planned_stage）、title、question、change、execution_status、acceptance_status、acceptance_scope、criteria_authority、pending_checks、evidence、runs。执行状态为 planned/running/completed/failed/aborted/not_run；验收为 pass/fail/incomplete/unknown/provisional_pass/not_assessed。二者独立，执行完成不等于质量通过。

acceptance_scope 明确验收对象，criteria_authority 为 agreed/proposed/unknown，pending_checks 保存必需未完成项。未执行不能标 pass/fail；未完成执行不能标 pass/provisional_pass；有待完成项不能通过。正式 pass 还需 agreed 标准。批次有多个方案时说明验收状态究竟指哪个方案及范围，不把其中一个方案的通过贴给整个批次。

每个 evidence 包含 locator（原证据定位）与可选 sha256。每个 run 包含 run_id、attempt_id、phase、origin 和 input_origin；后两者为 fresh/cache/replay/unknown，分别表示本阶段执行来源和输入来源。例如历史合成数据的本地新审计是 origin=fresh、input_origin=replay，不能将审计说成重新生成。attempt_id 未恢复时写 unknown，不制造真实编号。没有运行则 runs 为空；禁止给未执行节点编造运行号。问题、配置、输入和评价口径的实质变化建新节点；同一设计重跑新增 run，不累计成独立方法验证。原历史实验包含多个配置时，可先保留批次节点，不倒造原本不存在的实验记录。

edges 包含 source、target、relation、basis（关系依据）：derived_from/retests/combines 表示来源到新实验的演进方向，必须无环且连接 experiment；compares 表示对照，references 表示知识参考，不暗示数据流或因果。planned_next 只连接 planned_stage，表示尚未执行的方案阶段顺序，并检测环路。多个来源用多条边，不限制为树。跨项目参考可以作为有命名空间的节点引用，不把机标实验当作合成任务上游执行步骤。关系无依据时不补边，仅按节点展示。

## 生成与核验

`python scripts/render_canvas.py --graph <graph.json> --output <新canvas.html>`

只读 HTML 使用内嵌 SVG 和节点详情，不访问网络，不调用模型，不提供执行、拖拽编辑或回写。JSON 为权威输入，画布可重建；输出必须为新文件。输入校验包括唯一 ID、状态一致性、重复运行/边、边端点和演进/计划环路。图级来源、验收范围、标准来源及未完成项均显示；参考/计划边为虚线，并附关系类型与依据。证据定位和哈希展示不等于自动核验业务真实性；调用方需检查原文件。

graph/1 可继续读取，缺少 kind、验收范围或标准时在页面显式显示未知，不反推默认完成；新生成图使用 graph/2。数据约定的版本提升独立于 Skill 补丁版本，不更改原历史记录及旧画布。

运行历史源文件及项目记录不因生成图而改变。计划节点与已执行节点明确标示，未执行生成、人工和训练不得被画成已完成。节点过多时建议按项目/阶段拆图，当前布局仅适合小型审查图。

案例见 examples/，是已执行案例的摘要映射，不是新一轮业务执行。原始数据与日志不在 Skill 仓库中。
