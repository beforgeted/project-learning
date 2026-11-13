# project-learning

为 AI 协作项目记录方案、实验、问题和经验，并逐步形成可复用的 SOP，为后续模型评测中台积累有依据的项目知识。

当前版本：**v0.6.3**。适用于机标、审核、质检、合成数据等项目，实施方式可以是代码、已提供的 Agent 链路、平台工作流或人工协作。核心指令见 [SKILL.md](SKILL.md)，版本变更见 [更新记录](CHANGELOG.md)。

## 定位

员工与 AI 讨论需求、选择方案、试跑和处理问题时，project-learning 帮助留下后续能用的记录：为什么选这个方案、实际试过什么、结果在哪、哪些经验适用、哪些配置需要重验。

它为未来中台的“根据需求召回资源和经验 → 生成方案 → 试跑 → 查找类似问题的解法 → 给出初步评价”提供知识基础。现阶段交付的是记录约定、工作指引和离线辅助、校验脚本；中台索引、模型调用、调度及 Agent 部署需要另外接入。

```text
需求讨论 → 检索历史 → 方案取舍 → 实际试跑 → 问题与评价
                ↑                              ↓
                └──── 有条件的经验 ← SOP 与证据留档
```

可以只记录一次尝试、检索一条经验或更新一个 SOP，无需每次执行完整流程。普通聊天不会自动归档，Skill 也不会后台监听员工对话。

## 安装

需要支持本地 Skill 的 Codex 环境。手动克隆需要 Git；运行可选辅助脚本需要 Python 3.9+，只使用标准库。当前 GitHub 仓库为私有仓库，需要拥有仓库访问权限并完成 GitHub 认证。

### 方式一：使用 Skill Installer

在 Codex 中发送：

```text
$skill-installer
请从 https://github.com/beforgeted/project-learning 安装 project-learning。
SKILL.md 位于仓库根目录，技能名称使用 project-learning。
如果已经安装，请先检查现有路径与本地修改，不重复安装同名副本。
```

### 方式二：手动安装到当前项目

在目标业务项目根目录执行：

```sh
git clone https://github.com/beforgeted/project-learning.git .agents/skills/project-learning
```

目录应为 `.agents/skills/project-learning/SKILL.md`，同时包含 `references/`、`scripts/`、`assets/` 和 `agents/`。

当前官方文档列出的项目级发现路径为 `.agents/skills/`，个人级为 `~/.agents/skills/`。本项目开发时的宿主环境也提供了 `~/.codex/skills/` 安装位置；已有安装应以宿主实际识别的路径为准，不再复制一份同名 Skill。安装后可在技能选择器检查；未出现时重启 Codex。参见 [官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)。

对于通过 Git 克隆的安装，先检查修改，再快进更新：

```sh
git -C .agents/skills/project-learning status --short
git -C .agents/skills/project-learning pull --ff-only
```

有本地修改时先保存或合并；不要强制覆盖。下载或安装器复制的目录未必是 Git 仓库，需要通过原安装方式更新。业务记录应放在业务工作区，避免写进技能安装目录。

## 使用方式

### 1. 从需求讨论开始

在 Codex 中显式调用 `$project-learning`，并提供 AI 可以访问的项目资料。以下为可复制的**提示词示例**，不是已经执行的任务：

```text
$project-learning
我们要做一个中文内容机标项目。请根据当前需求讨论和我提供的规则文档，
记录需求、可用资源、候选方案与取舍。先检索工作区已有经验，注明适用条件。
暂未提供的 Agent 链路、质量门槛和样本不要补造；方案先保留待验证状态。
记录保存到当前工作区的 project-learning/content-labeling/。
```

最低限度说明项目目标、当前阶段，以及可访问的材料位置。已有链路请提供真实入口、版本与输入输出约定；无法访问的材料会记为缺口。

### 2. 把执行结果补进记录

```text
$project-learning
请读取本次试跑输出、配置和逐样本评估结果，记录实际执行范围与失败样本。
区分自动检查、人工复核和未执行项；质量指标必须注明分子、分母和规则版本。
根据证据判断哪些经验可限定范围复用，哪些只是候选修复。
```

平台导出、人工评估表、工作流运行记录同样可作为证据，不要求所有项目都有代码。只提供口头结果时，会注明“用户报告、产物未核验”。

### 3. 跨项目复用并形成 SOP

```text
$project-learning
为新的合成数据项目检索已有机标经验。
保存原业务问法、术语改写和实际候选结果，检查是否因阅读窗口而遗漏方法。
按方法、配置、效果分别判断：借鉴什么、适配什么、重验什么。
生成新方案和 SOP，关联来源版本与目标步骤；未执行的生成、质检和训练明确标注。
```

### 记录保存在哪里

有明确工作区且没有既有约定时，默认使用 `project-learning/<项目短名>/`，按需要创建：

```text
project-learning/<项目短名>/
├── index.md          项目导航与未决事项
├── requirements.md   需求、规则与验收口径
├── resources.md      实际可用资源及依赖缺口
├── approaches.md     方案选择和历史参考
├── experiments.md    实际尝试、结果与证据定位
├── issues.md         问题、解法和修复验证
├── lessons.md        有边界的经验及入库判定
├── evaluations.md    初步评价与未覆盖范围
└── sops/             SOP、成熟度与验收步骤
```

也可以沿用已有目录、拆成独立条目或映射到已有知识平台。条目保留项目命名空间 ID、修订、来源、适用范围及关联；文件名和数量不要求固定。保存、索引就绪、业务召回验证分别报告，本地保存不代表已进入团队中台。

## 实际案例：公开评论机标

以下为本项目开发期间的**真实本地演练摘要**。机标演练最初使用 v0.3；以下指标来自原始演练，后续文档更新不代表重新执行。

需求是对公开 YouTube 评论进行 SPAM/HAM 机标，并允许转复核。比较过关键词基线、带弃权的规则方案，以及朴素贝叶斯分类方案。

原始 1,956 条，去重后保留 1,741 条：训练 1,030、开发 400、留出 311。选定方案的留出结果为：

| 指标 | 实际结果 | 含义 |
|---|---|---|
| 自动部分与参考标签一致 | 274 / 294，93.20% | 仅自动输出子集，不是全量质量 |
| 自动覆盖 | 294 / 311，94.53% | 剩余进入待复核分支 |
| 待复核 | 17 条 | 人工处理未执行 |

留出结果没有达到演练提出的 95% 门槛；该门槛是 AI 提议，不是团队已批准标准。业务未达标仍然可以留下有用经验：

- `youtube-spam-pilot/L-001`：未命中垃圾信号不能直接证明正常，应保留未知或待复核分支。
- `youtube-spam-pilot/L-002`：开发结果不能代替新范围验收，模型高分不能代替独立参考质量。
- `youtube-spam-pilot/L-003`：同时报告自动质量、覆盖与待复核量，避免只展示好看的子集指标。
- `youtube-spam-pilot/L-004`：新联系方式规则只是候选修复，未实施就不能写成已验证解法。

实际形成了需求、资源、方案、开发与留出实验、问题卡、经验、试行 SOP 和本地目录等 15 条主记录，并保存逐样本证据。这个案例展示的是“失败结果如何成为可追溯经验”，不是承诺某个分类模型适用于其他项目。

## 实际案例：Self-Instruct 跨项目复用

使用 v0.4，以 [Self-Instruct](https://github.com/yizhongw/self-instruct) 的固定提交 `0b26ccaa415992100fa32df62d41b994cf928e23` 为参考。实际执行了旧机标库检索与公开合成实例的离线检查，没有重新执行上游生成与训练流程。

原问题：“合成数据生成后，如何记录可用量、淘汰量和待审量，避免只报生成数量？”

原关键词零命中；改写为“覆盖率、待复核、分母”后返回 9 条候选，其中 L-003 排第 8。词语之间是帮助搜索的相关线索，不代表合成可用量与机标覆盖率有相同定义。依据完整日志推演，仅取前五条会看不到 L-003；这不是线上中台事故，也没有证明前五条完全没有相关知识。

采用到新方案中的内容分别处理：

| 来源 | 可借鉴的方法 | 不能直接迁移或仍需重验 |
|---|---|---|
| L-001、L-003 | 待审分流、分母和处理量记账 | 新筛选是否误删、语义合格量与人工成本 |
| L-002 | 独立评价、按范围验收 | 新模型/评分器、质量门槛和下游效果 |
| I-004 | 去重及评测隔离的流程 | 合成样本的去重键、近重复与语义污染检测 |
| L-004 | 区分观察、建议动作与修复验证 | 尚未实施的规则不升级为已验证 SOP |

原机标的 HAM/SPAM 标签、分类器、0.90/0.99 阈值、95% 门槛和质量数字均未直接沿用。

本次对全部 **82,439 条**公开合成实例执行离线检查，得到互斥路由：

| 路由 | 数量 |
|---|---:|
| 待语义质检 | 74,764 |
| 同题多答案待复核 | 7,631 |
| 规范化重复剔除 | 42 |
| 与评测指令精确重合，进入隔离 | 2 |
| 结构拒收 | 0 |
| 合计 | 82,439 |

同题多答案不等于错误，指令重合也不等于已证明答案泄漏。74,764 条只是待语义质检，不能称为合格训练数据。产物包括实际检索记录、适用性审查、新方案、全量单样本路由和 SOP。

**新生成、独立语义质检、人工质检、训练与下游评价均未执行；整体业务验收未完成，完整 SOP 为草稿。** 离线审计子流程已有执行证据，可作为试行参考。

两个案例的完整工作区、数据集、运行日志和专用适配脚本未随本仓库发布；上述 ID 是本地演练标识，不是仓库文件链接。仅安装此 Skill 无法一键重跑两个案例，需要另行提供案例资料与运行条件。本 README 的结果是维护者根据本地证据整理的摘要，仓库读者不能仅凭这些摘要独立复核全部明细。

## 当前能力与边界

| 能力 | 明确边界 |
|---|---|
| 有依据地补查业务术语，保留原问题与改写 | 没有内置向量库、语义搜索或自动同义词服务 |
| 分别记录候选命中、阅读窗口与最终采用 | 没有更换排序算法；尚未证明召回率提升 |
| 按方法、实现配置、效果逐主张审查 | 方法可借鉴不代表配置兼容，更不保证数值效果 |
| 处理旧元数据与正文范围冲突 | 在新项目保存派生判断，不静默放宽原条件或批量重写旧库 |
| 区分证据、候选经验、限定范围经验与 SOP | 单次观察只支持覆盖范围；未执行步骤不能升级成熟度 |
| 保存单样本证据、有效性及交付回执 | 依赖实际可访问材料，不读取不可见对话，也不自动完成平台入库 |
| 提供离线格式检查、验收汇总和时间评估 | 不执行模型生成、人工质检或训练，不判断答案的语义正确性 |
| 项目启用、业务目录绑定与写入目标校验 | 配置有效不等于允许持续归档；不提供后台监听 |
| 实验节点、关系和只读画布 | 由既有记录生成视图，不调度实验或回写业务状态 |
| SOP 提炼、交接及独立复验约定 | 局部通过不代表整体业务完成；没有内置代理调度，也不保证相对旧版更好 |

采集格式为 `project-learning/0.5`；旧 0.2/0.3/0.4 记录继续可读，按实际维护需要补充字段。项目绑定使用 `binding/2`，实验图使用 `graph/2`；各辅助脚本的数据约定见对应参考文档。

## 项目绑定与只读实验画布

在指定 Codex 项目中明确启用后，记录范围与模式保存在业务工作区的 `project-learning/project-binding.json`。支持 enabled/manual/paused；默认未绑定时仅显式调用。一个 Codex 项目可以包含多个业务子项目，binding/2 用 projects 分别绑定业务 ID 和记录目录。写入前核对宿主项目、当前业务 ID 和实际目标路径；配置 valid 不等于允许持续归档。迁移或 worktree 需要明确登记。此机制不提供后台监听。

实验节点保存问题、改动、执行状态、验收状态与范围、标准来源、待完成项、证据和运行列表。派生、复验、组合关系支持多个来源且禁止演进环路；对照和参考关系不代表执行依赖。graph/2 将未执行的方案阶段标为 planned_stage，以 planned_next 表示计划顺序。重跑增加运行，配置或验证问题实质变化才产生新实验。历史批次保留原粒度，不能从汇总反向编造独立实验。

[配置与数据约定](references/project-graph.md) · [机标摘要记录](examples/youtube.json) · [Self-Instruct 摘要记录](examples/self-instruct.json)

在仓库根目录执行（输出必须不存在）：

```sh
python scripts/render_canvas.py --graph examples/youtube.json --output youtube-canvas.html
python scripts/render_canvas.py --graph examples/self-instruct.json --output self-instruct-canvas.html
```

生成离线只读 HTML，可点击节点定位详情；包含图级来源、关系类型与依据、执行与验收状态、验收范围、未完成项、原证据定位及哈希。案例 JSON 是本地实际记录的摘要映射，原始日志仍未发布；unknown attempt_id 表示未从汇总恢复，不能当成真实尝试编号。Self-Instruct 审计运行的 origin=fresh，input_origin=replay：本次新执行审计，输入来自历史公开生成。

案例摘要保留机标留出失败、人工未完成，以及 Self-Instruct 生成、语义/人工质检、训练未执行。画布不调用模型、不自动执行、不支持编辑回写；只生成可审查的小型图，结构检查不替代证据真实性或业务验收。

持续归档前运行（路径替换为实际值）：

```text
python scripts/validate_binding.py --binding <binding.json> --workspace <工作区> --codex-project-id <宿主ID> --business-project-id <当前业务ID> --target <拟写入文件>
```

退出码 0 表示持续归档条件匹配，1 表示配置有效但条件不足，2 表示输入/配置错误；工具本身不写业务记录。调用方仍需判断讨论内容属于哪个业务，不能从目标路径反向伪造身份。旧 binding/1 仅提供诊断，不会自动推断多个子项目的归属；需明确映射后迁移。旧 graph/1 可读，缺失信息在页面中显示未知，新案例使用 graph/2。

## 可选离线辅助脚本

这部分供需要机器可读结果的操作者使用，日常讨论与复盘无需运行脚本。

| 脚本 | 用途 | 不能证明什么 |
|---|---|---|
| [evaluate_checks.py](scripts/evaluate_checks.py) | 根据检查 JSON 对样本 JSONL 执行确定性输出检查 | 格式通过不等于业务质量达标；human/model 检查为 not_run |
| [summarize_acceptance.py](scripts/summarize_acceptance.py) | 核验报告哈希并汇总必需检查、未完成项及标准来源 | 不核验声明的验收对象与证据在语义上是否匹配，不授权发布 |
| [assess_validity.py](scripts/assess_validity.py) | 按查询时间核对有效期及已声明状态 | 不判断业务兼容性；无到期时间不代表永久有效 |
| [validate_binding.py](scripts/validate_binding.py) | 核对项目、业务 ID 和实际写入目标 | 不自动判断讨论内容属于哪个业务，也不写业务记录 |
| [render_canvas.py](scripts/render_canvas.py) | 校验实验图并生成只读 HTML | 图结构通过不证明来源真实或业务验收通过 |

在 Skill 根目录执行以下命令。尖括号内容必须替换为真实文件；先创建输出父目录，输出文件必须尚不存在：

```text
python scripts/evaluate_checks.py --checks <checks.json> --samples <samples.jsonl> --output <new-report.json>
python scripts/summarize_acceptance.py --plan <plan.json> --output <new-summary.json>
python scripts/assess_validity.py --record <record.json> --as-of <带时区的ISO时间> --output <new-validity.json>
```

`record.json` 是含 ID、修订和 validity 的结构化记录，不是 Markdown 原文。数据结构、退出码与结果解释见 [评价与验收](references/evaluation.md) 和 [知识生命周期](references/knowledge-lifecycle.md)。[检查示例](assets/acceptance-example.json) 与 [汇总计划示例](assets/acceptance-plan-example.json) 是虚构模板，需按真实业务修改，不能当成批准的质量标准。

## 仓库检查

仓库内回归检查：

```sh
python -B -m unittest discover -s tests -v
```

检查覆盖两个案例结构、跨项目目标混用、缺少身份、暂停/手动模式、目录越界、未执行却通过、待办与通过冲突、重复节点/运行、关系环路、来源显示和输出防覆盖。哈希及状态由维护者另与本地案例证据核对；这些检查不证明模型会在所有会话中准确判断归属。

## 进一步阅读

- [版本更新记录](CHANGELOG.md)
- [核心工作指令](SKILL.md)
- [跨项目检索与逐主张复用审查](references/cross-project-reuse.md)
- [经验入库、召回、有效期与交付回执](references/knowledge-lifecycle.md)
- [中台知识采集与交接字段](references/platform-handoff.md)
- [方案、实验和经验模板](references/records.md)
- [SOP 成熟度与维护](references/sop.md)
- [SOP 交接与对照验证](references/sop-validation.md)
- [设计来源及适配说明](references/design-sources.md)
