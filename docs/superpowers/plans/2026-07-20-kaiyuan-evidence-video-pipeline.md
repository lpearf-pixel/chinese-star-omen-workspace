# B9 契约先行与证据型天象垂直样片实施计划

> **For agentic workers:** 实现时必须使用独立 feature branch；在开始任何代码前重新读取 stable HEAD、全局记忆、任务台账、决策、设计与本计划。本文件当前仅是规划，不授权开始实现。

**Goal:** 冻结 `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1` 三个长期契约，并完成一条 2026-07-21 可复验研究包、Stellarium 脚本、字幕和本地竖屏预览。

**Architecture:** B9 是单条垂直切片，不是通用视频平台。现代星历、传统星官、古籍证据、规则评估、现代转译和渲染互相隔离，通过版本化契约连接。B10/B11 可以改变内部规则实现，但不得迫使视频层依赖内部对象。

**Tech Stack:** Python 3.12、Pydantic 2、Skyfield、现有 KB Search/证据解析/规则引擎、pytest、Hypothesis、Stellarium `.ssc`、FFmpeg 最小预览。

## Global Constraints

- 规划 PR #30 只修改文档；实现必须从规划 PR 合并后的新 `stable/kaiyuan-v2` HEAD 建立新分支。
- 不合入 `main`；不写、删、重建或迁移 `local_kb_default`。
- `apps/star-omen` 不执行正式 ingest 或正式 Qdrant mutation。
- B9 不实现全书规则结构化、自动配音、批量天象扫描、通用剪辑、自动发布。
- 候选、歧义、缺失或不可引用证据不得进入 `classical_quote`。
- 三个 v1 契约进入实现后冻结；语义变化必须新建版本。
- 结构化黄金文件不得由普通测试自动更新。

---

## Task 0：规划收口与仓库治理

**Files:**
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/DECISIONS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `AGENTS.md`
- Modify: `docs/development/DEVELOPMENT_MANUAL.md`

**Outcome:** 规划 PR 合并前，仓库事实源能准确恢复 B8 完成状态、B9–B12 路线、开放 PR 和测试策略。

- [ ] 核验 `stable/kaiyuan-v2` 当前远端 HEAD，不使用聊天中的旧 SHA。
- [ ] 核验开放 PR；将 #1、#7 记录为 legacy/superseded 待处置，不能再声明“无开放 PR”。
- [ ] 将 B9 标记为“规划已批准，尚未实现”，B10–B12 标记为路线任务。
- [ ] 记录方案 C：B9 契约与垂直样片 → B10 全书规则结构化 → B11 规则执行器 2.0 → B12 批量视频生产。
- [ ] 将 `PROJECT_MEMORY.md` 加入每次恢复开发的强制阅读顺序。
- [ ] 规划 PR 只运行 docs/governance 门禁，不声称功能测试已完成。
- [ ] 规划 PR 合并后关闭规划分支，不直接继续写实现代码。

## Task 1：冻结三个 v1 Schema 与兼容政策

**Files:**
- Create: `apps/star-omen/src/video_pipeline/contracts/astronomy_event_v1.py`
- Create: `apps/star-omen/src/video_pipeline/contracts/rule_assessment_v1.py`
- Create: `apps/star-omen/src/video_pipeline/contracts/video_package_v1.py`
- Create: `apps/star-omen/tests/video_pipeline/contracts/`
- Create: `tests/fixtures/video-package/v1/manifest.json`

**Interfaces:**
- `AstronomyEventV1`
- `RuleAssessmentV1`
- `VideoPackageV1`
- `validate_contract_compatibility(old_schema, new_schema)`

**Tests before implementation:**

- [ ] RED：模块不存在。
- [ ] RED：未知字段、重复 ID、非有限数、无时区时刻、负时长被接受。
- [ ] RED：`classical_quote` 在没有 citable evidence 时被接受。
- [ ] RED：candidate-only assessment 被标记为可口播。
- [ ] RED：同一 v1 schema 的字段语义被静默改变。

**Implementation acceptance:**

- [ ] Pydantic `extra="forbid"`，严格 UTC、有限数、稳定 ID 和交叉引用校验。
- [ ] JSON Schema 快照和 canonical JSON fixtures。
- [ ] v1 兼容政策：可新增明确 optional 字段，不得删除 required 字段或改变 enum 含义。
- [ ] `RuleAssessment/v1` 只投影稳定字段，不暴露内部 matcher 对象。
- [ ] focused tests、property smoke、contract golden tests 通过。

## Task 2：科学约定、固定星历和中国星官目录

**Files:**
- Create: `apps/star-omen/src/video_pipeline/astronomy/provider.py`
- Create: `apps/star-omen/src/video_pipeline/astronomy/conventions.py`
- Create: `apps/star-omen/src/video_pipeline/asterisms/catalog.py`
- Create: `apps/star-omen/data/video_pipeline/scientific_conventions_v1.yaml`
- Create: `apps/star-omen/data/video_pipeline/asterism_catalog_v1.yaml`
- Create: `tests/fixtures/astronomy/v1/`
- Create: `tests/fixtures/asterisms/v1/`

**Interfaces:**
- `SkyfieldEphemerisProvider.get_points(...)`
- `calculate_event_candidate(...) -> AstronomyEventV1`
- `AsterismCatalog.resolve_object(...) -> AsterismMapping`

**Required planning decisions encoded in fixtures:**

- [ ] UTC/TT/TDB 转换和输出边界。
- [ ] ICRS、视位置、黄道坐标和站心坐标分离。
- [ ] 无折射几何高度与展示高度分离。
- [ ] 东经为正、北纬为正；海拔和时区必填策略。
- [ ] 星历逻辑名、版本、字节数和 SHA-256；正常运行不联网下载。
- [ ] 可见性阈值版本。
- [ ] 每类科学 fixture 的独立来源、参考架和容差。

**Tests:**

- [ ] 属性测试：纬度、经度、时区、闰日、极区、非有限数。
- [ ] 变形测试：同一 UTC 的不同时区表达结果一致。
- [ ] 变形测试：改变地点不改变地心身份坐标，但改变站心高度/方位。
- [ ] 科学黄金测试：月相、近合、恒星附近经过等至少三类事件。
- [ ] 星官映射测试：verified identity、membership、region-only、ambiguous、unresolved。
- [ ] 禁止以最近恒星作为无来源的通用映射。

## Task 3：证据检索与 `RuleAssessment/v1` 适配器

**Files:**
- Create: `apps/star-omen/src/video_pipeline/rule_assessment.py`
- Create: `apps/star-omen/src/video_pipeline/evidence_bundle.py`
- Create: `apps/star-omen/tests/video_pipeline/test_rule_assessment_v1.py`
- Create: `tests/fixtures/evidence/v1/`

**Interfaces:**
- `build_rule_assessment(event, retriever, rules) -> RuleAssessmentV1`
- `build_evidence_bundle(assessment) -> EvidenceBundleV1`

**Must reuse:**

```text
official structured_recall
→ official primary_evidence
→ filesystem fallback only after healthy empty official primary
```

**Tests:**

- [ ] transport/auth/timeout/contract 错误不会转换成健康无命中。
- [ ] pending overlay 不进入 citable evidence。
- [ ] source/locator/page/paragraph/heading/anchor/hash 任一不匹配即阻止口播。
- [ ] `matched`、`candidate_only`、`insufficient_data`、`partial_match`、冲突抑制正确投影。
- [ ] 规则内部字段变化不影响冻结的 `RuleAssessment/v1` fixture。
- [ ] 负向黄金集覆盖标题命中、反向词序、全文重复、多处 anchor 和缺 hash。

## Task 4：2026-07-21 受限编辑包与 Stellarium 脚本

**Files:**
- Create: `apps/star-omen/src/video_pipeline/editorial.py`
- Create: `apps/star-omen/src/video_pipeline/stellarium.py`
- Create: `apps/star-omen/data/examples/video/2026-07-21-input.json`
- Create: `apps/star-omen/data/examples/video/2026-07-21-modern-interpretation.json`
- Create: `apps/star-omen/data/video_pipeline/templates/zh_cn_vertical_slice_v1.yaml`
- Create: `apps/star-omen/tests/video_pipeline/test_vertical_editorial_v1.py`

**Scope:** 只支持一套约 60–90 秒的垂直样片模板。

**Tests:**

- [ ] 每段口播必须有且只有一个 claim class。
- [ ] “开口破局”只能是 `modern_interpretation`，且带现代转译披露。
- [ ] 无 citable 古籍证据时自动省略古籍占断，不生成占位式伪引文。
- [ ] 禁止确定性命运承诺和恐吓性表达。
- [ ] shot list 时间连续且与字幕总时长一致。
- [ ] `.ssc` 中 UTC、地点、对象与 `AstronomyEvent/v1` 一致。
- [ ] `.ssc` 只使用 allowlist 命令，拒绝绝对路径和路径穿越。
- [ ] 重复生成的脚本和结构化文件字节一致。

## Task 5：原子研究包、审核门禁和最小预览

**Files:**
- Create: `apps/star-omen/src/video_pipeline/package.py`
- Create: `apps/star-omen/src/video_pipeline/review.py`
- Create: `apps/star-omen/src/video_pipeline/preview.py`
- Create: `apps/star-omen/tests/video_pipeline/test_package_review_preview_v1.py`
- Modify: `.gitignore`

**Interfaces:**
- `write_package_atomic(...)`
- `evaluate_review_gate(...)`
- `build_minimal_preview_command(...)`

**Acceptance:**

- [ ] staging directory 全部验证成功后才同文件系统原子发布。
- [ ] 输出已存在时拒绝覆盖。
- [ ] 所有结构化资产和可选媒体资产进入 hash inventory。
- [ ] 审核维度独立：astronomy、classical evidence、editorial、render。
- [ ] `partial_metadata_only`、candidate-only、ambiguous mapping、hash 变化阻止 publishable。
- [ ] B9 允许无音频 `preview.mp4`；不生成或承诺 `final.mp4`。
- [ ] FFmpeg 只构造 argv，不通过 shell 拼接；单元测试不启动外部进程。

## Task 6：分层测试、Hermetic E2E 与本地视觉 Smoke

**Files:**
- Create: `apps/star-omen/tests/video_pipeline/test_vertical_slice_e2e_v1.py`
- Create: `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- Modify: `.github/workflows/kaiyuan-stable-core.yml`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**PR gates:**

```text
G0 Governance
G1 Contract/schema
G2 Scientific golden + property smoke
G3 Retrieval/citation negative golden
G4 RuleAssessment projection
G5 Hermetic vertical E2E
G7 Package/review verification
```

**Nightly or scheduled gates:**

```text
full Hypothesis profiles
scientific golden full set
full corpus/rule fixture scan
mutation testing for critical validators
```

**Local/self-hosted macOS gates:**

```text
Stellarium capability detection
actual .ssc execution
screenshot inventory
FFmpeg minimal preview
manual visual review record
```

**E2E failure injection:**

- [ ] tampered astronomy provenance；
- [ ] missing angular separation；
- [ ] candidate-only quotation；
- [ ] ambiguous star mapping；
- [ ] path traversal；
- [ ] changed frame/hash inventory；
- [ ] transport failure；
- [ ] noncanonical JSON；
- [ ] repeated generation nondeterminism。

## Completion Definition

B9 只有在以下全部成立时才能 `DONE`：

- 三个 v1 契约冻结并有兼容测试；
- 2026-07-21 研究包可以从固定输入重复生成；
- 科学事实、传统映射、古籍证据和现代转译严格隔离；
- hermetic E2E 不联网、不启动 GUI、不写正式 Qdrant；
- 本地 macOS 实际生成 `.ssc` 截图和一个可查看的竖屏预览；
- 所有 required gates 和独立 review 通过；
- 实现 PR 合入 `stable/kaiyuan-v2` 并记录 exact-head CI 与 squash SHA；
- 没有自动配音、批量生成或自动发布。