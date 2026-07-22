# B10 《唐开元占经》全书规则结构化实施计划

> **For agentic workers:** 本计划在 B9 完成并形成稳定 `RuleAssessment/v1` 后实施。开始前必须重新读取远端 stable HEAD、开放 PR、`PROJECT_MEMORY.md`、任务台账、决策、B10 设计和本计划。本文件当前仅作规划。

**Goal:** 将全书 primary passage 转换为可审核、可回链、可统计、可恢复执行、可版本发布的 `OmenRule/v2` 规则资产，并形成 B11 的真实执行器需求清单。

**Architecture:** B10 分为基础设施、校准试点、全书抽取、全书审核波次和规则发布五个阶段。候选身份与正式规则身份分离；确定性抽取是基线，模型辅助是显式可选能力；所有长任务按稳定 batch ID 可恢复执行。

**Tech Stack:** Python 3.12、Pydantic 2、现有 `kb-text-core`、现有证据 resolver、pytest、Hypothesis、可选模型适配器、JSONL/YAML、append-only review log、离线发布包验证。

## Global Constraints

- B10 从 B9 closeout 后的新 `stable/kaiyuan-v2` 建立独立 feature branch。
- 不写、删、重建或迁移 `local_kb_default`。
- raw corpus 不可变；所有校订、解释和规则存在派生层。
- 模型只生成候选，不能批准、promote、ingest 或写正式知识库。
- `OmenRule/v2` 破坏性变化必须新建版本。
- sealed holdout 不参与日常 prompt、pattern 或阈值调整。
- 正式规则必须通过完整 citable evidence 校验和人工复核。
- B10 不以单个巨型 PR 实施；每个阶段独立 PR/closeout。
- 长任务必须 checkpoint/resume、幂等、no-overwrite，不允许因中断从头静默重跑并覆盖历史。

## 完成分母

“全书规则结构化”使用以下明确分母，不再以“至少一批规则发布”代替全书完成：

1. `100%` primary passages 进入稳定 inventory；
2. 每个 passage 获得 `eligible | ineligible | ambiguous | needs_review` 的 eligibility 状态；
3. 每个 eligible passage 至少产生候选规则，或记录 `no_candidate_reason`；
4. 每个候选进入 `approved | rejected | deferred_with_reason` 终态；
5. 每个 approved rule 通过 citable evidence、去重/冲突和 release validation；
6. unresolved/ambiguous 内容保留在分母和报告中，不通过排除提高覆盖率。

B10 基础设施可以提前发布，但只有以上全书分母满足时，B10 项目状态才能 `DONE`。

## 实施阶段与 PR 拆分

```text
B10-PR-A  OmenRule/v2, identity and annotation contract
→ B10-PR-B Passage inventory, source invalidation and resumable batch framework
→ B10-PR-C Golden sets and calibration pilot
→ B10-PR-D Full-book deterministic extraction
→ B10-PR-E Optional model candidate adapter
→ B10-PR-F Review queue, deduplication and conflict workflow
→ B10-PR-G Full-book review waves and coverage
→ B10-PR-H Rule release, offline verification and engine-gap report
```

模型辅助未启用时可以跳过 B10-PR-E，但 release manifest 必须明确 `model_extraction=disabled`；B10 完成定义不能反过来强制使用模型。

---

## Task 0：规划、治理和阈值冻结流程

**Files:**
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/DECISIONS.md`
- Modify: `docs/development/WORK_LOG.md`
- Create: `docs/research/KAIYUAN_RULE_PROGRAM_CHARTER.md`

**Acceptance:**

- [ ] 记录全书完成分母、PR 拆分和批次恢复政策。
- [ ] 明确 pilot 之前的指标是候选目标，不是可随意移动的 release threshold。
- [ ] 校准试点完成后生成 `threshold-freeze.json`，固定 extractor/review/release 阈值；后续修改必须独立决策和 before/after 报告。
- [ ] citable evidence false positive 门禁固定为 `0`，不能通过调阈值放宽。
- [ ] B11 只消费正式 `engine-gap-report`，不得根据未审核候选提前实现复杂执行器。

## Task 1 / B10-PR-A：`OmenRule/v2`、候选身份和标注手册

**Files:**
- Create: `packages/kb-contracts/python/kb_contracts/omen_rule_v2.py`
- Create: `packages/kb-contracts/python/kb_contracts/rule_candidate_v2.py`
- Create: `packages/kb-contracts/tests/test_omen_rule_v2.py`
- Create: `docs/research/KAIYUAN_RULE_ANNOTATION_GUIDE_V1.md`
- Create: `tests/fixtures/rules/v2/annotation-cases/`

**Identity lifecycle:**

- `candidate_id` 基于 extractor identity、source passage IDs、raw spans 和 candidate payload hash；
- `rule_id` 只在批准时分配，不能由模型直接指定；
- approved rule 后续修改生成新 `rule_version`，历史版本不可覆盖；
- candidate 合并、拆分或拒绝保留来源 candidate IDs 和审核链。

**Acceptance:**

- [ ] 本体覆盖 trigger、actors、relation、conditions、effect、severity、time window、exceptions、conflict、computability、evidence、review、provenance。
- [ ] 明确一段拆多规则、多段合一规则、枚举、省略主语、引用异文和不可计算语义。
- [ ] v1 兼容读取和显式迁移报告。
- [ ] 严格 JSON、重复 ID、非法状态、未知字段、非有限数 fail-closed。
- [ ] candidate/rule identity、版本和 append-only history 有 contract fixtures。
- [ ] 标注案例人工审阅并冻结；普通测试不得自动改写。

## Task 2 / B10-PR-B：稳定 passage inventory、source-change 失效和 batch 框架

**Files:**
- Create: `packages/kb-text-core/python/kb_text_core/rule_passages.py`
- Create: `packages/kb-text-core/tests/test_rule_passages.py`
- Create: `apps/star-omen/src/rule_structuring/passage_inventory.py`
- Create: `apps/star-omen/src/rule_structuring/batches.py`
- Create: `apps/star-omen/tests/rule_structuring/test_batches_v1.py`
- Create: `tests/fixtures/evidence/rule-passages-v1/`

**Interfaces:**
- `build_rule_passage_inventory(kb_root) -> PassageInventory`
- `compare_source_fingerprint(previous, current) -> SourceChangeReport`
- `plan_batches(inventory, batch_size=200) -> BatchPlan`
- `resume_batch(batch_id, checkpoint) -> BatchState`

**Acceptance:**

- [ ] passage 使用现有 book/locator/page/heading/paragraph/raw hash 语义。
- [ ] 全文/分卷重复保留 provenance，分卷优先。
- [ ] source hash 变化将相关 candidate/rule 标记 `source_changed`，不得继续 citable。
- [ ] 多处相同 anchor 不得自动绑定唯一 passage。
- [ ] inventory 和 batch plan 字节确定性，输入顺序不影响输出。
- [ ] 默认 batch 为 200 passages，可配置在 `100–500`；batch ID 与输入集合稳定绑定。
- [ ] 中断恢复、重复执行、并发同 batch、checkpoint 篡改和 no-overwrite 有测试。

## Task 3 / B10-PR-C：黄金集、审核校准和阈值冻结

**Files:**
- Create: `eval/rules/v2/development/`
- Create: `eval/rules/v2/validation/`
- Create: `eval/rules/v2/holdout/`
- Create: `eval/rules/v2/manifests/`
- Create: `docs/research/KAIYUAN_RULE_GOLDEN_SET_POLICY.md`
- Create: `docs/research/KAIYUAN_REVIEW_CALIBRATION.md`

**Pilot:**

- 按卷、天体、关系词、句式复杂度、可计算性和证据风险进行分层抽样；
- pilot 不以连续前几卷代替代表性抽样；
- pilot 输出标注分歧、吞吐量、每类错误、阈值建议和 full-book 工作量估算。

**Acceptance:**

- [ ] 覆盖日、月、五星、二十八宿、客星、彗星、流星、日月食、云气等类别。
- [ ] 覆盖合、犯、入、守、掩、离、留、逆等关系。
- [ ] 包含可计算、部分可计算、不可计算、歧义、重复和冲突案例。
- [ ] fixture 记录 passage ID、source hash、人工标签、审核人、版本和 split。
- [ ] holdout manifest 有 hash，普通命令不得读取 expected labels 用于调参。
- [ ] 黄金更新只能显式批准，普通测试不得重写。
- [ ] pilot 后冻结 precision/recall/review thresholds；确定性抽取正式候选目标 precision 不低于 `0.90`，未达标时只保留 research-only 状态。
- [ ] citation eligibility false positive 固定为 `0`。

## Task 4 / B10-PR-D：全书确定性候选抽取

**Files:**
- Create: `apps/star-omen/src/rule_structuring/pattern_extractor.py`
- Create: `apps/star-omen/data/rule_structuring/patterns_v1.yaml`
- Create: `apps/star-omen/tests/rule_structuring/test_pattern_extractor_v1.py`
- Create: `apps/star-omen/src/rule_structuring/run_batches.py`

**Interfaces:**
- `extract_rule_candidates(passages, pattern_set) -> CandidateBatch`
- `run_extraction_batch(batch, checkpoint_dir) -> BatchResult`

**Acceptance:**

- [ ] pattern version、raw offsets、match terms 和 source passages 全部进入 provenance。
- [ ] 高精度优先；heading-only 和 loose 匹配不能自动产生正式候选。
- [ ] 同一 passage 多候选稳定排序、稳定 candidate ID。
- [ ] validation 报告 precision、recall、F1 和按类别指标。
- [ ] false positive 高风险类别使用独立阈值和负向黄金集。
- [ ] 全书所有 inventory batches 完成或有明确 failed/deferred 记录，不允许漏 batch 后声称完成。
- [ ] batch 可恢复、重复运行不产生重复 candidate。

## Task 5 / B10-PR-E：可选模型辅助候选抽取与数据治理

**Files:**
- Create: `apps/star-omen/src/rule_structuring/model_extractor.py`
- Create: `apps/star-omen/src/rule_structuring/model_contract.py`
- Create: `apps/star-omen/tests/rule_structuring/test_model_extractor_contract_v1.py`
- Create: `docs/research/KAIYUAN_MODEL_EXTRACTION_POLICY.md`

**Interfaces:**
- `ModelRuleExtractor.extract(passages, prompt_asset) -> CandidateBatch`

**Governance:**

- 默认 `disabled`；启用外部 provider 需要显式配置和决策记录；
- 记录 provider 的数据保留/训练政策、发送字段 allowlist 和本地缓存政策；
- 不发送 secret、机器路径、未授权私有注释或审核身份；
- 原始模型输出是否进入发布包由 policy 决定，默认不进入正式 release。

**Acceptance:**

- [ ] 适配器与供应商解耦；离线测试使用 fake provider。
- [ ] 记录 provider、model、version、prompt hash、input hash、raw output 和 parsed result。
- [ ] invalid JSON、missing fields、timeout、拒答和非确定差异明确失败或候选缺失。
- [ ] 模型无法 approve、promote、ingest、分配 rule ID 或写正式 Qdrant。
- [ ] 模型变化必须重跑 validation，并与确定性抽取器报告分开。
- [ ] 禁用模型时 B10 仍可完成，manifest 明确记录 disabled。

## Task 6 / B10-PR-F：审核队列、双阶段复核、去重和冲突

**Files:**
- Create: `apps/star-omen/src/rule_structuring/review_queue.py`
- Create: `apps/star-omen/src/rule_structuring/review.py`
- Create: `apps/star-omen/src/rule_structuring/dedup.py`
- Create: `apps/star-omen/src/rule_structuring/conflicts.py`
- Create: `apps/star-omen/tests/rule_structuring/test_review_queue_v1.py`
- Create: `apps/star-omen/tests/rule_structuring/test_review_dedup_conflict_v1.py`

**Interfaces:**
- `build_review_queue(candidates, batch_policy) -> ReviewQueue`
- `append_review_decision(queue, decision) -> QueueState`
- `resume_review_queue(queue_id, log) -> QueueState`

**Acceptance:**

- [ ] 状态机覆盖 initial review、independent recheck、adjudication、approved、rejected、deferred_with_reason。
- [ ] 审核历史 append-only，修改字段和理由可追踪。
- [ ] 同一审核者复核时要求时间隔离字段。
- [ ] 多审核者统计一致率，关键字段 κ 目标 ≥ 0.80。
- [ ] 同源重复、语义重复、上位/特例、不同传统冲突分别处理。
- [ ] suppressed rule 不删除，所有决定有 provenance。
- [ ] review queue 支持 claim/lease、超时归还、断点恢复、并发冲突和重复 decision 去重。
- [ ] 批次不能因为跳过困难项而提前完成；deferred 必须有结构化理由。

## Task 7 / B10-PR-G：全书审核波次、覆盖率和质量评测

**Files:**
- Create: `apps/star-omen/src/rule_structuring/coverage.py`
- Create: `apps/star-omen/src/rule_structuring/evaluation.py`
- Create: `apps/star-omen/src/rule_structuring/waves.py`
- Create: `apps/star-omen/tests/rule_structuring/test_coverage_evaluation_v1.py`
- Create: `docs/research/KAIYUAN_RULE_COVERAGE_METRICS.md`

**Interfaces:**
- `build_coverage_report(inventory, candidates, reviews) -> CoverageReport`
- `run_rule_eval(split, extractor, rule_set) -> EvaluationReport`
- `plan_review_waves(coverage, capacity) -> ReviewWavePlan`

**Acceptance:**

- [ ] 明确所有指标分母，不静默排除未识别或 deferred passage。
- [ ] 输出卷、天体、事件、关系词、effect domain 等维度覆盖率。
- [ ] 输出 candidate/reviewed/approved/citable/computable/not-computable/ambiguous/missing/conflict 数量。
- [ ] development/validation/holdout 结果分开。
- [ ] sealed holdout 只在发布 gate 开启。
- [ ] 报告严格 JSON、确定性排序和版本 provenance。
- [ ] 每一 review wave 有固定输入 hash、容量估算、开始/结束 checkpoint、remaining backlog。
- [ ] 全书分母六项全部满足后才允许 B10 completion；单批发布不能冒充全书完成。

## Task 8 / B10-PR-H：规则发布、差异报告、离线验证和 B11 gap report

**Files:**
- Create: `apps/star-omen/src/rule_structuring/release.py`
- Create: `apps/star-omen/src/rule_structuring/engine_gap.py`
- Create: `apps/star-omen/tests/rule_structuring/test_rule_release_v1.py`
- Create: `apps/star-omen/tests/rule_structuring/test_engine_gap_v1.py`
- Create: `docs/development/B10_RULE_RELEASE_RUNBOOK.md`
- Modify: `.github/workflows/kaiyuan-stable-core.yml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `docs/development/DECISIONS.md`

**Package members:**

```text
rule-release-manifest.json
rules.jsonl
passage-bindings.jsonl
coverage-report.json
evaluation-report.json
source-fingerprint.json
migration-report.json
review-summary.json
release-diff.json
engine-gap-report.json
```

**`engine-gap-report.json` 至少包含:**

```text
unsupported_requirement
frequency_in_approved_rules
affected_event_families
severity
representative_rule_ids
required_measurements
current_engine_behavior
recommended_B11_priority
```

**Acceptance:**

- [ ] fixed inventory、bytes、size、hash 和 schema version。
- [ ] atomic caller-selected no-overwrite 发布。
- [ ] offline verifier 重跑 schema、引用、coverage、evaluation 和 diff consistency。
- [ ] release diff 明确新增、修改、弃用、source_changed 和冲突变化。
- [ ] 不含 secret、绝对路径或未批准原始模型数据。
- [ ] mutation testing 覆盖 approval、evidence、source invalidation、conflict 和 release verifier，关键模块目标 ≥ 80%。
- [ ] PR gates、nightly gates、holdout release gate 和独立 review 全部通过。
- [ ] B11 优先级只能来自 approved/citable 规则的 gap report，不统计 rejected 候选。

## Completion Definition

B10 只有在以下全部成立时才能 `DONE`：

- B10-PR-A 至 B10-PR-H 中适用 PR 均独立 review/merge/closeout；
- `OmenRule/v2`、candidate/rule identity 和标注手册冻结；
- 100% primary passages 进入稳定 inventory 并有 eligibility 状态；
- 100% eligible passages 有候选或结构化 no-candidate 原因；
- 所有候选进入 approved/rejected/deferred_with_reason 终态；
- approved rules 均通过 citable、去重/冲突和 source-change validation；
- development/validation/holdout、校准阈值和黄金更新政策生效；
- 确定性全书抽取完成；模型辅助若启用则有独立报告，未启用则明确 disabled；
- 审核队列可恢复，所有 review waves 有输入/output/checkpoint 证据；
- 覆盖率使用明确分母，不再使用主观百分比或单批冒充全书；
- 规则发布包可离线复验并有 release diff；
- `engine-gap-report.json` 按真实频次、风险和覆盖面给出 B11 需求；
- 最终 closeout 记录 exact-head CI、PR squash SHA、全书剩余 deferred 风险和人工工作量。