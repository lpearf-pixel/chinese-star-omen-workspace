# B10 《唐开元占经》全书规则结构化实施计划

> **For agentic workers:** 本计划在 B9 完成并形成稳定 `RuleAssessment/v1` 后实施。开始前必须重新读取 stable HEAD、`PROJECT_MEMORY.md`、任务台账、决策、B10 设计和本计划。本文件当前仅作规划。

**Goal:** 将全书 primary passage 转换为可审核、可回链、可统计、可版本发布的 `OmenRule/v2` 规则资产，并形成 B11 的真实执行器需求清单。

**Architecture:** B10 分为本体与标注规范、稳定 passage、黄金集、候选抽取、人工审核、去重冲突、覆盖率评测和规则发布包八个阶段。候选生成与正式批准彻底分离，模型只允许生成候选。

**Tech Stack:** Python 3.12、Pydantic 2、现有 `kb-text-core`、现有证据 resolver、pytest、Hypothesis、可选模型适配器、JSONL/YAML、离线发布包验证。

## Global Constraints

- B10 必须从 B9 closeout 后的新 `stable/kaiyuan-v2` 建立独立 feature branch。
- 不写、删、重建或迁移 `local_kb_default`。
- raw corpus 不可变；所有校订、解释和规则存在派生层。
- 模型只生成候选，不能批准、promote 或写正式知识库。
- `OmenRule/v2` 破坏性变化必须新建版本。
- sealed holdout 不参与日常 prompt、pattern 或阈值调整。
- 正式规则必须通过完整 citable evidence 校验和人工复核。

---

## Task 1：冻结 `OmenRule/v2` 与标注手册

**Files:**
- Create: `packages/kb-contracts/python/kb_contracts/omen_rule_v2.py`
- Create: `packages/kb-contracts/tests/test_omen_rule_v2.py`
- Create: `docs/research/KAIYUAN_RULE_ANNOTATION_GUIDE_V1.md`
- Create: `tests/fixtures/rules/v2/annotation-cases/`

**Acceptance:**

- [ ] 规则本体覆盖 trigger、actors、relation、conditions、effect、severity、time window、exceptions、conflict、computability、evidence、review 和 provenance。
- [ ] 明确一段拆多规则、多段合一规则、枚举、省略主语、引用异文和不可计算语义。
- [ ] v1 兼容读取和显式迁移报告。
- [ ] 严格 JSON、重复 ID、非法状态、未知字段、非有限数 fail-closed。
- [ ] 标注案例由人工审阅后固定为 contract fixtures。

## Task 2：稳定 passage 清单与 source-change 失效

**Files:**
- Create: `packages/kb-text-core/python/kb_text_core/rule_passages.py`
- Create: `packages/kb-text-core/tests/test_rule_passages.py`
- Create: `apps/star-omen/src/rule_structuring/passage_inventory.py`
- Create: `tests/fixtures/evidence/rule-passages-v1/`

**Interfaces:**
- `build_rule_passage_inventory(kb_root) -> PassageInventory`
- `compare_source_fingerprint(previous, current) -> SourceChangeReport`

**Acceptance:**

- [ ] 每个 passage 使用现有 book/locator/page/heading/paragraph/raw hash 语义。
- [ ] 全文/分卷重复保留 provenance，分卷优先。
- [ ] source hash 变化将相关规则标记 `source_changed`，不得继续 citable。
- [ ] 多处相同 anchor 不得自动绑定唯一 passage。
- [ ] inventory bytes 确定性，输入顺序不影响输出。

## Task 3：development/validation/sealed holdout 黄金集

**Files:**
- Create: `eval/rules/v2/development/`
- Create: `eval/rules/v2/validation/`
- Create: `eval/rules/v2/holdout/`
- Create: `eval/rules/v2/manifests/`
- Create: `docs/research/KAIYUAN_RULE_GOLDEN_SET_POLICY.md`

**Acceptance:**

- [ ] 覆盖日、月、五星、二十八宿、客星、彗星、流星、日月食、云气等类别。
- [ ] 覆盖合、犯、入、守、掩、离、留、逆等关系。
- [ ] 包含可计算、部分可计算、不可计算、歧义、重复和冲突案例。
- [ ] 每个 fixture 记录 passage ID、source hash、人工标签、审核人、版本和 split。
- [ ] holdout manifest 有 hash，普通命令不得读取其 expected labels 用于调参。
- [ ] 黄金更新只能通过显式批准命令，普通测试不得重写。

## Task 4：确定性候选抽取器

**Files:**
- Create: `apps/star-omen/src/rule_structuring/pattern_extractor.py`
- Create: `apps/star-omen/data/rule_structuring/patterns_v1.yaml`
- Create: `apps/star-omen/tests/rule_structuring/test_pattern_extractor_v1.py`

**Interfaces:**
- `extract_rule_candidates(passages, pattern_set) -> CandidateBatch`

**Acceptance:**

- [ ] pattern version、raw offsets、match terms 和 source passage 全部进入 provenance。
- [ ] 高精度优先，标题-only 和 loose 匹配不能自动产生高置信候选。
- [ ] 同一 passage 多候选稳定排序、稳定 ID。
- [ ] validation 报告 precision、recall、F1 和按类别指标。
- [ ] false positive 高风险类别有独立阈值和负向黄金集。

## Task 5：可选模型辅助候选抽取

**Files:**
- Create: `apps/star-omen/src/rule_structuring/model_extractor.py`
- Create: `apps/star-omen/src/rule_structuring/model_contract.py`
- Create: `apps/star-omen/tests/rule_structuring/test_model_extractor_contract_v1.py`
- Create: `docs/research/KAIYUAN_MODEL_EXTRACTION_POLICY.md`

**Interfaces:**
- `ModelRuleExtractor.extract(passages, prompt_asset) -> CandidateBatch`

**Acceptance:**

- [ ] 适配器与供应商解耦；离线测试使用 fake provider。
- [ ] 记录 provider、model、version、prompt hash、input hash、raw output 和 parsed result。
- [ ] 非确定输出、invalid JSON、missing fields、timeout 和拒答均明确失败或候选缺失，不产生正式规则。
- [ ] 模型无法 approve、promote、ingest 或写正式 Qdrant。
- [ ] 模型变化必须重跑 validation，报告与确定性抽取器分开。

## Task 6：双阶段人工审核、去重和冲突组

**Files:**
- Create: `apps/star-omen/src/rule_structuring/review.py`
- Create: `apps/star-omen/src/rule_structuring/dedup.py`
- Create: `apps/star-omen/src/rule_structuring/conflicts.py`
- Create: `apps/star-omen/tests/rule_structuring/test_review_dedup_conflict_v1.py`

**Acceptance:**

- [ ] 状态机覆盖 initial review、independent recheck、adjudication、approved、rejected、needs_revision。
- [ ] 审核历史 append-only，修改字段和理由可追踪。
- [ ] 同一审核者复核时要求时间隔离字段。
- [ ] 多审核者统计一致率，关键字段 κ 目标 ≥ 0.80。
- [ ] 同源重复、语义重复、上位/特例、不同传统冲突分别处理。
- [ ] suppressed rule 不删除，所有决定有 provenance。

## Task 7：覆盖率和质量评测

**Files:**
- Create: `apps/star-omen/src/rule_structuring/coverage.py`
- Create: `apps/star-omen/src/rule_structuring/evaluation.py`
- Create: `apps/star-omen/tests/rule_structuring/test_coverage_evaluation_v1.py`
- Create: `docs/research/KAIYUAN_RULE_COVERAGE_METRICS.md`

**Interfaces:**
- `build_coverage_report(inventory, candidates, reviews) -> CoverageReport`
- `run_rule_eval(split, extractor, rule_set) -> EvaluationReport`

**Acceptance:**

- [ ] 明确所有指标分母，不静默排除未识别 passage。
- [ ] 输出卷、天体、事件、关系词、effect domain 等维度覆盖率。
- [ ] 输出 candidate/reviewed/approved/citable/computable/not-computable/ambiguous/missing/conflict 数量。
- [ ] development/validation/holdout 结果分开。
- [ ] sealed holdout 只在发布 gate 开启。
- [ ] 报告严格 JSON、确定性排序和版本 provenance。

## Task 8：规则发布包和离线验证

**Files:**
- Create: `apps/star-omen/src/rule_structuring/release.py`
- Create: `apps/star-omen/tests/rule_structuring/test_rule_release_v1.py`
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
```

**Acceptance:**

- [ ] fixed inventory、bytes、size、hash 和 schema version。
- [ ] atomic caller-selected no-overwrite 发布。
- [ ] offline verifier 重跑 schema、引用、coverage 和 evaluation consistency。
- [ ] 不含 secret、绝对路径或未批准原始模型数据。
- [ ] mutation testing 覆盖 approval、evidence、source invalidation、conflict 和 release verifier，关键模块目标 ≥ 80%。
- [ ] PR gates、nightly gates、holdout release gate 和独立 review 全部通过。

## Completion Definition

B10 只有在以下全部成立时才能 `DONE`：

- `OmenRule/v2` 和标注手册冻结；
- 稳定 passage inventory 与 source-change invalidation 生效；
- development/validation/holdout 黄金集建立；
- 确定性抽取和可选模型辅助抽取均有独立质量报告；
- 双阶段审核、去重、冲突和一致率完成；
- 覆盖率以自动指标报告，不再使用主观百分比；
- 至少一批跨类别 approved/citable 规则进入确定性发布包；
- 发布包可离线复验；
- B11 获得按真实频次、重要性和缺口排序的执行器需求清单。