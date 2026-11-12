# 经验入库、召回验证、有效期和交付状态

本文件定义决策和记录规则，适用于本地文件及已有知识平台。缺少索引或查询接口时记录真实能力边界，不自动建设服务。简单记录只使用相关部分。

## 1. 留档与经验入库

| 层次 | 进入条件 | 复用方式 |
|---|---|---|
| 原始证据 | 可定位的讨论、执行记录、产物或转述 | 支持追溯；不直接作为已验证操作规则 |
| 候选经验 | 有明确问题、假设或发现，但支持证据、边界或复现信息不足 | 可作为探索线索，标明缺口 |
| 限定范围可复用经验 | 下列门槛均有依据支持 | 可供中台召回，附条件、证据和反例 |
| SOP | 可复用做法已形成执行、验收、异常处理步骤 | 按 [sop.md](sop.md) 的成熟度使用 |

复用经验的判定门槛：

1. **可追溯**：结论链接到执行、评估或失败证据，明确直接核验与用户报告；仅有转述时保留为候选，直到必要证据得到核验。
2. **可触发与操作**：说明遇到什么条件采用什么做法，或在什么条件下应避开什么做法。失败结果也可以成为可复用的避坑经验。
3. **边界明确**：记录已覆盖场景、数据/规则/资源版本，以及反例、未测部分和原因推测。
4. **具有复用价值**：会改变后续方案选择、避免有意义的重复试错，或补足通用文档中没有的业务知识。没有新结论时只保留实验。
5. **有唯一归属**：先检索已有经验；选择新建、补充、修订、关联或保留冲突，避免相同结论重复累积。

判定记录包含 `decision`（candidate / reusable / merge / evidence_only）、`reason`、支持/反驳证据、缺失项、目标条目 ID/版本和判定时间。`merge` 是对已有条目的更新动作，不自动提高其证据等级。证据状态与 SOP 成熟度分别记录。

单次实验可以支持窄范围经验，不支持未经验证的跨场景结论。重复引用同一次试跑算一个证据来源；不按聊天提及次数累计“成功次数”。跨项目提升需核对规则、数据和实施条件，未知部分仍为候选。已有用户要求的记录照常保存，不因不满足门槛丢弃失败或未决信息。

### 证据范围与复用范围

`evidence_scope` 保存实际观察发生的版本、数据和条件；`applicability` 保存新任务必须满足的条件，二者不要机械复制。例如“拒判流程同时报告自动质量与覆盖率”是一种方法，其观察证据来自特定项目，但采用这种报告方法不要求使用原项目的数据哈希。原规则配置和数值效果则不能随方法一起继承。

正文、元数据和检索过滤应表达同一范围。有依据的必要约束必须保留，业务域不同可只返回方法参考并标明具体实现待适配。无法判断时列出差异，不能静默放宽条件。

跨项目出现混合主张或旧元数据冲突时，使用 [cross-project-reuse.md](cross-project-reuse.md) 的逐主张审查：条件按访问边界、方法前提、实现约束或证据背景解释；在新项目保存派生审查，不将原记录整体改成适用。

已核验失败现象可以形成可复用的边界或避坑结论；它提出的新修复动作仍可能未执行。需要结构化时分别记录 `observation_status`、`action_validation` 和各自证据，不使用一个 `evidence_verified=true` 推断解法已验证。

## 2. 召回验证

对新建或实质修改的复用经验/SOP，在现有可用检索路径上做小规模验证。普通事实补记不必反复执行。这里的检查证明可发现性，不证明实际效果，也不等同于中台完整检索评测。

1. 根据原始需求或问题写一个自然业务问法；不使用目标 ID、文件名或完整标题作为唯一查询。边界重要时再用一个不适用条件的问法做反例检查。
2. 记录检查的库/索引/版本、权限范围、过滤条件和时间。只有本地搜索时标为 `local_search`，不能写中台语义召回通过。
3. 实际执行查询，保留必要的返回 ID/版本和可观察的排序。结果有截断或只读部分候选时，记录返回上限和实际阅读窗口；候选命中不等于窗口内可见，也不等于采用。确认目标的适用范围、状态与证据可读取；相似但过期或不兼容的条目不作为可直接复用结果。
4. 缺失或结果过宽、无法支持方案决策时，检查索引是否更新、业务术语、字段、过滤条件与窗口；按 [cross-project-reuse.md](cross-project-reuse.md) 保留原问法并作有依据的补查。沿用查询预算；无既定预算时本次最多做初查加两轮有明确变化的补查，仍有缺口就记录并停止。
5. 有代表性相关条目集合时再计算命中指标；一个查询找到一个目标不能证明整体召回率高。不得添加纯粹为测试命中的关键词、修改原业务问题或放宽权限来掩盖失败。

```yaml
retrieval_check:
  target_id: null
  target_revision: null
  query: null
  query_origin: null
  query_transform: null
  check_kind: "smoke"
  expected_behavior: null
  backend: null
  index_revision: null
  scope_and_filters: null
  corpus_ref: null
  checked_at: null
  observed_results: null
  retrieval_outcome: "not_run"
  applicability_review: null
  outcome: "not_run"
  limitations: null
```

`expected_behavior` 可以是“命中并附条件”或“排除/标为不适用”。`outcome` 为 pass / fail / blocked / not_run / stale；只有观察结果满足预期行为才为 pass。没有检索工具标 blocked；没有执行标 not_run；以前通过但条目/范围/索引变化标 stale。负例出现目标并不总是失败：明确标示其不适用且未推荐复用时，可以符合预期。

`retrieval_outcome` 单独记录实际命中情况；`applicability_review` 记录另一次范围审查的判定、依据、审查者或工具和时间。附加脚本或 AI 给出“不适用”，不能归功于检索系统本身已经正确过滤。只做了命中测试，不得补写适用性通过。

声明查询来源是员工真实需求、独立维护用例还是同一作者的演练问法；保存原问法及实际执行的关键词改写。`corpus_ref` 指本次被检索集合／版本和相关过滤，不需要复制全文。有排序且声称窗口内命中或漏召回时，记录 k、目标名次和窗口是实际采用还是事后推演；无排序的文件搜索不伪造名次。不能因扩窗后找到目标就改写原窗口的失败结果。

小库中用同一作者的关键词找到目标只作为 smoke。若要主张检索质量改善，使用独立问法及相关性依据，加入有代表性的相似但不适用条目，并分别观察命中、排序和适用性；没有这些材料时明确未评估，不自行编造标准答案。负例检查也应核对错误条目是否被推荐，而非只确认某个目标出现。

## 3. 知识有效期

区分**记录时间**和**业务有效时间**，有效性必须结合适用范围判断：

```yaml
validity:
  recorded_at: null
  effective_from: null
  effective_until: null
  last_verified_at: null
  review_due_at: null
  state: "unknown"
  basis: null
  bindings: null
  superseded_by: null
```

- `bindings` 指适用的数据特征、规则、模型/资源或流程版本；引用真实版本，不能只写“最新”。
- `effective_from / effective_until` 只填有依据的业务有效界限。`null` 是未知，不表示永久有效。时间范围已知时采用起始包含、结束不包含。
- `state` 为 current_in_scope / review_required / expired / superseded / unknown；current_in_scope 只表示声明范围内有支持，不代表所有未来任务可直接采用。
- `last_verified_at` 是实际验证日期；`review_due_at` 仅在已有维护周期或明确约定时填写，不统一强加 30 天有效期。
- 规则生效、资源更换、数据分布变化、关键反例或证据失效是复核事件；时间到达复核日表示需复核，不自动证明知识错误。新结果矛盾时保留原记录，说明受影响范围及新证据。

旧条目按原范围保留；当前推荐过滤或降级过期、已替代、范围不兼容的知识，必要时提供历史参考和复核提示。复核可能只影响一个条件分支，不扩大成所有范围失效。

查询时按本次 `as_of` 核对有效时间，不能只读取以前写下的 state：已知结束边界到达即过期，尚未生效不得当作当前可用，到达复核日期需复核。未知日期不等于永久有效；曾声明 expired / superseded 的记录不能因日期缺失自动恢复。保留原状态作为历史，把当前判断另记为带时间的评估，不静默改写证据。

需要可执行的时间检查时，可将单条元数据导出为 JSON 并运行 [assess_validity.py](../scripts/assess_validity.py)：

```text
python <skill-dir>/scripts/assess_validity.py --record <record.json> --as-of <含时区的本次时间> --output <new-report.json>
```

输入含 `id`、`revision` 和 `validity`。日期时间必须带时区；仅日期字段按 `--as-of` 的时区自然日判断，报告会声明这一解释，若业务时区不同先使用正确时区。起始包含、结束不包含；边界矛盾或非法日期报错。报告只评估时间和已声明状态，不验证业务兼容性、权限、证据真伪或是否可直接复用。退出码0表示声明范围内没有发现时间阻断，1表示过期／替代／待复核／未知，2表示输入或写入错误。

## 4. 保存、索引与召回的独立回执

在条目旁或已有发布账本中保存最小回执，不强建新文件系统。回执绑定内容修订号；如使用内容哈希，哈希只针对业务正文与元数据，不包括会被回执更新的字段，避免自引用。

```yaml
delivery:
  record_id: null
  revision: null
  operation_key: null
  record_saved:
    state: "not_attempted"
    locator: null
    verified_at: null
    receipt: null
  index_ready:
    state: "not_configured"
    backend: null
    indexed_revision: null
    verified_at: null
    receipt: null
  retrieval_verified:
    state: "not_run"
    check_ref: null
```

| 状态轴 | 可用状态 | 成功证据 |
|---|---|---|
| record_saved | not_attempted / confirmed / failed / unknown | 本地回读内容吻合，或平台回执及回读能核对 ID/版本 |
| index_ready | not_configured / pending / confirmed / failed / unknown / stale | 指定索引已包含本次 ID/版本，或精确读取验证匹配 |
| retrieval_verified | not_run / pass / fail / blocked / stale | 对应的业务问法查询结果与验证记录 |

`index_ready.backend` 区分本地导航索引、文件搜索和中台检索索引。更新 `index.md` 只能确认本地导航，不能证明中台索引已更新。来源记录已保存但无中台索引时，保留 `record_saved=confirmed`、中台 `index_ready=not_configured`。

写入超时或回执不明确时标 unknown，先按目标 ID/版本查询。重试使用同一 `operation_key`（目标 ID＋修订号＋操作类型），不要因回执丢失再次新建知识；已有平台幂等键优先使用。仅靠本地字段不能保证服务端幂等，需要目标系统实际支持或先查后写。

索引失败不回滚已确认保存的知识，不重跑生成/标注业务。重试只处理失败阶段，限于已有授权和合理次数；仍失败则报告部分完成。并发修改通过版本比对识别，读取最新内容后合并，不能盲目覆盖。

内容修订、目标索引变化或验证范围变化后，旧回执不能沿用；标记相关 index/recall 为 stale，并保存此前验证对应的版本。交付用一句话分别说明已保存在哪里、哪个索引就绪、哪个检索路径经过验证。
