# 项目绑定、实验节点与只读画布

## 项目启用

配置位于业务工作区 `project-learning/project-binding.json`，格式 project-learning/binding/1。包括 schema_version、business_project_id、mode（enabled/manual/paused）、codex_project_id、workspace_root、record_roots（工作区内相对路径列表）、consent（启用依据）。Codex ID 是宿主关联，不替代稳定业务 ID；名称仅展示，不用于身份匹配。

enabled：在当前可见且属于所列业务范围的协作中记录有价值增量。manual：仅明确要求时记录。paused：暂停持续记录；当次明确要求单次记录不更改模式。没有绑定按 manual 处理，不扫描所有用户项目来推断意图。项目列表可访问时核对 ID；工具不可用时只依据已保存配置和实际路径，不虚构宿主识别结果。

一个 Codex 项目可有多个业务子项目，record_roots 指定边界，记录 ID 含子项目命名空间。无法判断归属时先问，不跨目录混写。改名保留业务 ID；迁移目录或 worktree 需登记经核验的新绑定，不能只凭同名或相同 remote 自动认领。跨机器的 Codex ID 可以不同。暂停不删除历史。

在主工作目录的 AGENTS.md 放置读取配置的简短入口；不覆盖已有指令。此机制依赖会话加载指令，不提供后台监听、完整聊天自动读取或必然触发保证。项目启用不等于允许额外模型费用或发布数据。

可运行 `python scripts/validate_binding.py --binding <配置> --workspace <实际目录> --codex-project-id <实际ID>` 核验配置与宿主上下文；未提供 ID 时只做路径核验，报告身份未确认。返回 0 仅代表校验通过，不执行记录或修改配置。

## 实验节点

格式 project-learning/graph/1：project_id、nodes、edges。每个 node 包含 id、title、question、change、execution_status、acceptance_status、evidence、runs。执行状态为 planned/running/completed/failed/aborted/not_run；验收为 pass/fail/incomplete/unknown/provisional_pass/not_assessed。二者独立，执行完成不等于质量通过。

每个 evidence 包含 locator（原证据定位）与可选 sha256。每个 run 包含 run_id、attempt_id、origin（fresh/cache/replay/unknown）。没有运行则 runs 为空；禁止给未执行节点编造运行号。问题、配置、输入和评价口径的实质变化建新节点；同一设计重跑新增 run，不累计成独立方法验证。原历史实验包含多个配置时，可先保留批次节点，不倒造原本不存在的实验记录。

edges 包含 source、target、relation：derived_from/retests/combines 表示来源到新实验的演进方向，必须无环；compares 表示对照，references 表示知识参考，不暗示数据流或因果。多个来源用多条边，不限制为树。跨项目参考可以作为有命名空间的节点引用，不把机标实验当作合成任务上游执行步骤。

## 生成与核验

`python scripts/render_canvas.py --graph <graph.json> --output <新canvas.html>`

只读 HTML 使用内嵌 SVG 和节点详情，不访问网络，不调用模型，不提供执行、拖拽编辑或回写。JSON 为权威输入，画布可重建；输出必须为新文件。输入校验包括唯一 ID、状态、边端点和演进环路。证据定位和哈希展示不等于自动核验业务真实性；调用方需检查原文件。

运行历史源文件及项目记录不因生成图而改变。计划节点与已执行节点明确标示，未执行生成、人工和训练不得被画成已完成。节点过多时建议按项目/阶段拆图，当前布局仅适合小型审查图。

案例见 examples/，是已执行案例的摘要映射，不是新一轮业务执行。原始数据与日志不在 Skill 仓库中。
