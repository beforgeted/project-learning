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
