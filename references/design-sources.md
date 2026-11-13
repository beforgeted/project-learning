# 设计来源与适配说明

本文件供设计解释和技能维护使用。以下为 2026-11-12 阅读到的项目文档、Skill 和发布记录；链接可能随上游变化。此 Skill 的指令、模板和本地脚本独立编写，采用设计思路，不要求安装这些项目。未把仓库 Star、宣传性能或模型自报置信度当成业务验证。

| 本版机制 | 参考来源 | 借鉴内容 | 对本项目的适配 |
|---|---|---|---|
| 经验入库门槛 | [Compound Engineering：ce-compound](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/guides/ce-compound.md) | 筛选有长期价值的知识；重叠检查；保留失败路径；确保后续工作能发现记录 | 分离原始实验留档与复用经验入库；失败经验可入库；无需代码仓库、测试框架或每条人工审批 |
| 分层与项目边界 | [Hermes：技能机制](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills#agent-managed-skills-skill_manage-tool)、[ECC：continuous-learning-v2](https://github.com/affaan-m/ECC/blob/main/skills/continuous-learning-v2/SKILL.md) | 区分事实和程序性知识；从小经验形成流程；项目经验与跨项目经验分开 | 使用证据/候选/可复用经验/SOP；只按可核验依据提升，不照搬数值置信度、观察频次或后台 Hooks |
| 召回验证 | [ECC：iterative-retrieval](https://github.com/affaan-m/ECC/blob/main/skills/iterative-retrieval/SKILL.md)、上述 ce-compound | 检索后检查缺口，调整查询并有界停止；解决“记录了但没人找到” | 用真实业务问法检查 ID/版本、条件与负例；本地检索和中台检索分别出回执，不把一次命中当整体召回率 |
| 知识有效期 | [Graphiti 项目设计](https://github.com/getzep/graphiti) | 时间有效窗口、来源关系、旧事实失效后保留历史 | 分离记录时间、业务有效时间、最近验证与复核状态；按规则/资源/数据范围失效，不要求部署图数据库 |
| 单样本证据 | [Langfuse：实验数据模型](https://langfuse.com/docs/evaluation/experiments/data-model)、[数据集](https://langfuse.com/docs/evaluation/experiments/datasets) | 关联样本、实验运行、轨迹和评分；运行样本可进入评测集 | 增加样本/运行/尝试/节点定位和证据粒度；允许 CSV、平台记录、JSONL 等原有产物，不复制敏感原文 |
| 可执行验收 | [Promptfoo：Assertions & metrics](https://www.promptfoo.dev/docs/configuration/expected-outputs/)、[0.125.0 发布记录](https://github.com/promptfoo/promptfoo/releases) | 可声明的检查、不同评分器、重复试跑稳定性、缓存命中披露 | 将业务标准映射到带版本的检查；附独立的离线确定性检查器；人工/模型判断保持未执行，运行错误不能算通过 |
| 保存与索引回执 | [Mem0：Python SDK v2.2.1 发布记录](https://github.com/mem0ai/mem0/releases) | 修复底层拒绝写入却报告成功新增的问题，仅为实际插入记录返回成功并写历史 | 分离保存/索引/召回；回读核验；超时状态未知；重试复用操作标识并检查版本，不伪称服务端原子事务 |

## 对未来中台的影响

v0.4 另依据一次本地机标项目的实际试跑和隔离验证补充：带范围与标准来源的验收汇总、证据范围与复用条件分开、召回命中与适用性审查分开、查询时计算有效期，以及案例适配器的可迁移性说明。这些是本 Skill 的迭代设计，不代表上述开源项目提供了相同接口。原项目数据、失败样本和版本审查报告保留在项目工作区，不写入 Skill 安装包。

现在积累的数据能够回答：经验为何可复用、怎样找到、何时和在什么范围有效、哪个样本支持结论、用什么标准验收、结果是否真正进入可查询位置。

v0.5 依据 Self-Instruct 跨项目案例的本地查询记录，补充术语映射关系、宽泛查询的补查、候选与阅读窗口分开记账、逐主张适用性审查，以及旧元数据冲突的派生记录。观察到原业务词无命中、合理改写后目标仍靠后、状态词产生宽泛命中；据此完善决策规则，没有更换或宣称改进搜索算法。原业务记录及复盘证据保留在项目工作区，不随 Skill 安装包分发。未新增外部项目设计归因；新规则仍需独立场景验证其检索效果。

后续服务仍需实现权限过滤、真实索引与查询、幂等写入及并发控制、Agent 运行接口、模型/人工评估器和异步状态回写。本 Skill 的字段与本地检查器不代表这些服务已经存在。现有 Agent 链路仍由用户提供。

## v0.6.2：SOP 提炼及其自身验证

2026-11-13 阅读下列公开设计，按本地 Self-Instruct 离线审计适配。研究上游指令和文档不等于安装或执行上游框架。

| 来源 | 具体借鉴 | 本次适配和实际依据 |
|---|---|---|
| [Compound Engineering：保存形式选择](https://github.com/EveryInc/compound-engineering-plugin/blob/main/skills/ce-compound/references/form.md) | 选择能阻止问题重现的最小形式；检查既要正常通过也要对缺陷失败 | 允许规则、决策表、子流程；为检查器建立五个错误输出负例，另对复跑验收目标作正反例诊断。不照搬仅保存已解决问题的范围，失败证据仍保留 |
| [Hermes：技能组织](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills#agent-managed-skills-skill_manage-tool) | 将操作方法和对应步骤的陷阱组织在一起，较长参考按需读取 | 形成离线审计子流程及分支表；来源证据仍留业务项目。本次未证明这种组织方式改善执行结果 |
| [Claudeception：Skill 提取](https://github.com/blader/Claudeception/blob/62dbb91d1183a866b5cf40079265c825b2695843/SKILL.md) | 明确触发、步骤、验证和例外；检查重复后更新 | 将经验映射到触发—信号—决策—例外—验证；并非每条经验都生成新 Skill |
| [Anthropic skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)、[grader](https://github.com/anthropics/skills/blob/main/skills/skill-creator/agents/grader.md) | 基线与新版本对照、查看实际产物、检查评分条件是否有效 | 同输入、同脚本、每版两个独立会话，原产物冻结后独立核验。允许打平；缺少可比耗时和 Token 就不报告效率提升 |

本次四组对 82,439 条公开数据及 14 条构造记录的正式路由和追溯一致，两类损坏批次均保留失败范围。实际支持的是“当前检查内未观察到优劣”，不支持“新版更好”或“任意输入下等效”。两类后续改动有产物依据：原版一份交付的验收器只读旧目录；提炼版两份报告的未评审数量表达有歧义。SOP 指引据此增加成对检查运行/复核入口及区分已确认通过数和未知实际质量。

Distilly 的资料提取/个人偏好分层、Hindsight 的混合召回也在前期研究中查看，但本次试验没有检验人物资料提取或检索后端，不将它们列为本次实测改进来源。
