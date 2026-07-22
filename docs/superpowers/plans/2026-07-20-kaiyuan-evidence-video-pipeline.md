# B9 契约先行与证据型天象垂直样片实施计划

> **For agentic workers:** 实现必须使用规划 PR 合并后的新 `stable/kaiyuan-v2` HEAD 和独立 feature branch。开始代码前重新读取远端 HEAD、开放 PR、`PROJECT_MEMORY.md`、任务台账、决策、设计与本计划。本文件当前仅是规划，不授权开始实现。

**Goal:** 冻结 `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1` 三个长期契约，并完成一条 2026-07-21 可复验研究包、Stellarium 脚本、字幕和本地竖屏预览。

**Architecture:** B9 是单条垂直切片，不是通用视频平台。现代星历、传统星官、古籍证据、规则评估、声明级口播和渲染互相隔离，通过版本化契约与 claim lineage 连接。B10/B11 可以改变内部规则实现，但不得迫使视频层依赖内部对象。

**Tech Stack:** Python 3.12、Pydantic 2、Skyfield、现有 KB Search/证据解析/规则引擎、pytest、Hypothesis、Stellarium `.ssc`、FFmpeg 最小预览。

## Global Constraints

- 规划 PR #30 只修改文档；实现必须从规划 PR 合并后的新 stable HEAD 建立新分支。
- 不合入 `main`；不写、删、重建或迁移 `local_kb_default`。
- `apps/star-omen` 不执行正式 ingest 或正式 Qdrant mutation。
- B9 不实现全书规则结构化、自动配音、批量天象扫描、通用剪辑或自动发布。
- 候选、歧义、缺失或不可引用证据不得进入 `classical_quote`。
- 三个 v1 契约进入实现后冻结；破坏性语义变化必须新建版本。
- 结构化黄金文件不得由普通测试自动更新。
- 普通 PR CI 不启动 Stellarium GUI 或 FFmpeg 外部进程。
- 规划分支不得复用为实现分支。

## 实施 PR 拆分

B9 禁止以一个大型 PR 一次完成。顺序如下：

```text
B9-PR-A  Contract registry and compatibility
→ B9-PR-B Scientific provider and asterism catalog
→ B9-PR-C RuleAssessment and evidence lineage
→ B9-PR-D Editorial package and Stellarium script
→ B9-PR-E Atomic package, review gate, preview and E2E
```

每个 PR 独立从最新 stable 建分支、独立 TDD、独立 review、独立合并。后一 PR 只能从前一 PR closeout 后的新 stable HEAD 开始。不得在一个 PR 中同时冻结契约、加入星历、接检索并生成媒体。

## 变更控制

进入 B9-PR-A 实现后：

- `Critical`：会生成错误科学事实、错误古籍引用、越权写入或不可恢复产物，允许修改当前 scope；
- `Important`：破坏契约兼容、确定性、审核门禁或安全边界，允许修改当前 task；
- `Normal/Enhancement`：默认进入 B10–B12 backlog，不扩大 B9；
- 任何 v1 breaking change 使用新版本和迁移说明，不原地重解释旧字段。

---

## Task 0：规划收口与仓库治理

**Files:**
- Modify: `docs/development/PROJECT_MEMORY.md`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/DECISIONS.md`
- Modify: `docs/development/WORK_LOG.md`
- Modify: `AGENTS.md`
- Modify: `docs/development/DEVELOPMENT_MANUAL.md`

**Outcome:** 规划 PR 合并前，仓库事实源能准确恢复 B8 完成状态、B9–B12 路线、开放 PR、测试策略和实施 PR 拆分。

- [ ] 核验远端 `stable/kaiyuan-v2` HEAD，不使用聊天或记忆中的旧 SHA。
- [ ] 核验全部开放 PR；#1、#7 记录为 legacy/superseded 待事实核验处置。
- [ ] 在任务台账登记 B9-PR-A 至 B9-PR-E；实现任务保持 `BACKLOG`，不得提前标记 `IN_PROGRESS`。
- [ ] 记录方案 C、变更控制和“规划分支不承载实现”。
- [ ] 规划 PR 只运行 docs/governance 门禁，不声称功能测试已完成。
- [ ] 规划 PR review/merge 后关闭规划分支，并重新读取 stable HEAD。

## Task 1 / B9-PR-A：契约注册表、Schema 和兼容政策

**Files:**
- Create: `apps/star-omen/src/video_pipeline/contracts/astronomy_event_v1.py`
- Create: `apps/star-omen/src/video_pipeline/contracts/rule_assessment_v1.py`
- Create: `apps/star-omen/src/video_pipeline/contracts/video_package_v1.py`
- Create: `apps/star-omen/schemas/video_pipeline/v1/astronomy-event.schema.json`
- Create: `apps/star-omen/schemas/video_pipeline/v1/rule-assessment.schema.json`
- Create: `apps/star-omen/schemas/video_pipeline/v1/video-package.schema.json`
- Create: `apps/star-omen/schemas/video_pipeline/schema-registry.json`
- Create: `apps/star-omen/tests/video_pipeline/contracts/`
- Create: `tests/fixtures/video-package/v1/manifest.json`

**Interfaces:**
- `AstronomyEventV1`
- `RuleAssessmentV1`
- `VideoPackageV1`
- `validate_contract_compatibility(old_schema, new_schema)`
- `canonical_contract_bytes(model) -> bytes`

**Required contract additions:**

- 每个 narration/claim 有稳定 `claim_id`、唯一 `claim_class`、`source_refs`、`review_status`；
- `source_refs` 只能引用 astronomy measurement、asterism mapping、citable passage、historical source 或明确 modern interpretation；
- schema registry 记录 schema ID、version、owner、compatibility policy 和 fixture manifest hash；
- 未知 schema、重复 ID、悬空引用和跨包引用 fail-closed。

**Tests before implementation:**

- [ ] RED：模块和 schema registry 不存在。
- [ ] RED：未知字段、重复 ID、非有限数、无时区时刻、负时长被接受。
- [ ] RED：`classical_quote` 没有 citable evidence 仍被接受。
- [ ] RED：candidate-only assessment 被标记为可口播。
- [ ] RED：claim 有悬空或错误类型 `source_refs`。
- [ ] RED：同一 v1 schema 删除 required 字段或改变 enum 含义仍通过。

**Acceptance:**

- [ ] Pydantic `extra="forbid"`，严格 UTC、有限数、稳定 ID 和交叉引用校验。
- [ ] Python model、JSON Schema、registry 和 canonical fixture 四者一致。
- [ ] v1 允许新增明确 optional 字段；禁止删除 required、改变 enum 含义或重解释字段。
- [ ] `RuleAssessment/v1` 只投影稳定字段，不暴露内部 matcher 对象。
- [ ] contract、property smoke、schema registry 和 golden compatibility tests 通过。

## Task 2 / B9-PR-B：科学约定、固定工具链和中国星官目录

**Files:**
- Create: `apps/star-omen/src/video_pipeline/astronomy/provider.py`
- Create: `apps/star-omen/src/video_pipeline/astronomy/conventions.py`
- Create: `apps/star-omen/src/video_pipeline/asterisms/catalog.py`
- Create: `apps/star-omen/data/video_pipeline/scientific_conventions_v1.yaml`
- Create: `apps/star-omen/data/video_pipeline/asterism_catalog_v1.yaml`
- Create: `apps/star-omen/data/video_pipeline/toolchain_policy_v1.yaml`
- Create: `tests/fixtures/astronomy/v1/`
- Create: `tests/fixtures/asterisms/v1/`

**Interfaces:**
- `SkyfieldEphemerisProvider.get_points(...)`
- `calculate_event_candidate(...) -> AstronomyEventV1`
- `AsterismCatalog.resolve_object(...) -> AsterismMapping`
- `build_toolchain_manifest(...) -> ToolchainManifestV1`

**Scientific and reproducibility decisions:**

- [ ] UTC/TT/TDB 转换和输出边界。
- [ ] ICRS、视位置、黄道坐标和站心坐标分离。
- [ ] 无折射几何高度与展示高度分离。
- [ ] 东经为正、北纬为正；海拔和时区策略明确。
- [ ] 星历逻辑名、版本、字节数和 SHA-256；正常运行和测试不联网下载。
- [ ] Python、Skyfield、星历、leap-second/timescale 数据、Stellarium、FFmpeg 进入 toolchain manifest。
- [ ] 科学黄金值来自独立参考源，不能由待测 provider 或 Stellarium 自身生成。
- [ ] 可见性阈值、事件容差和参考架均有版本。

**Tests:**

- [ ] 属性测试：纬度、经度、时区、闰日、极区、非有限数。
- [ ] 变形测试：同一 UTC 的不同时区表达结果一致。
- [ ] 变形测试：改变地点不改变地心身份坐标，但改变站心高度/方位。
- [ ] 科学黄金：月相、近合、恒星附近经过至少三类事件。
- [ ] 至少一类事件使用第二独立参考源做 differential check；分歧超容差必须 fail-closed。
- [ ] 星官映射：verified identity、membership、region-only、ambiguous、unresolved。
- [ ] 禁止以最近恒星作为无来源的通用映射。
- [ ] 缺少固定星历、版本/hash 不匹配或隐式下载均明确失败。

## Task 3 / B9-PR-C：证据检索、双轨回归和 `RuleAssessment/v1`

**Files:**
- Create: `apps/star-omen/src/video_pipeline/rule_assessment.py`
- Create: `apps/star-omen/src/video_pipeline/evidence_bundle.py`
- Create: `apps/star-omen/tests/video_pipeline/test_rule_assessment_v1.py`
- Create: `tests/fixtures/evidence/v1/`
- Create: `tests/fixtures/video-package/v1/evidence-rich-regression/`

**Interfaces:**
- `build_rule_assessment(event, retriever, rules) -> RuleAssessmentV1`
- `build_evidence_bundle(assessment) -> EvidenceBundleV1`

**Must reuse:**

```text
official structured_recall
→ official primary_evidence
→ filesystem fallback only after healthy empty official primary
```

**双轨样片验收:**

1. `2026-07-21` 是公开垂直样片候选。若没有 citable 古籍规则，允许产出 astronomy/history/modern-interpretation 版本，但必须省略古籍占断并保持 blocked classical status。
2. 使用仓库已有、可固定证据链的事件 fixture 建立 `evidence-rich-regression`，仅用于 CI，保证 `classical_quote` 正向路径确实被覆盖。它不是第二条公开样片，也不得冒充真实当日视频。

**Tests:**

- [ ] transport/auth/timeout/contract 错误不会转换成健康无命中。
- [ ] pending overlay 不进入 citable evidence。
- [ ] source/locator/page/paragraph/heading/anchor/hash 任一不匹配即阻止口播。
- [ ] `matched`、`candidate_only`、`insufficient_data`、`partial_match`、冲突抑制正确投影。
- [ ] 规则内部字段变化不影响冻结的 `RuleAssessment/v1` fixture。
- [ ] 负向黄金集覆盖标题命中、反向词序、全文重复、多处 anchor 和缺 hash。
- [ ] 7月21日没有正式规则时仍能生成诚实、可审核的非古籍占断包。
- [ ] evidence-rich fixture 能生成且只能生成经过 citable 校验的 classical quote。

## Task 4 / B9-PR-D：声明级编辑包与 Stellarium 脚本

**Files:**
- Create: `apps/star-omen/src/video_pipeline/editorial.py`
- Create: `apps/star-omen/src/video_pipeline/stellarium.py`
- Create: `apps/star-omen/data/examples/video/2026-07-21-input.json`
- Create: `apps/star-omen/data/examples/video/2026-07-21-modern-interpretation.json`
- Create: `apps/star-omen/data/video_pipeline/templates/zh_cn_vertical_slice_v1.yaml`
- Create: `apps/star-omen/tests/video_pipeline/test_vertical_editorial_v1.py`

**Scope:** 只支持一套约 60–90 秒模板，不建设通用模板系统。

**Tests:**

- [ ] 每段口播有且只有一个 claim class、稳定 claim ID 和非悬空 source refs。
- [ ] “开口破局”只能是 `modern_interpretation`，带现代转译披露。
- [ ] 无 citable 古籍证据时自动省略古籍占断，不生成占位式伪引文。
- [ ] 禁止确定性命运承诺和恐吓性表达。
- [ ] shot list 时间连续且与字幕总时长一致。
- [ ] `.ssc` 中 UTC、地点、对象与 `AstronomyEvent/v1` 一致。
- [ ] `.ssc` 只使用 allowlist 命令，拒绝绝对路径、路径穿越和任意脚本注入。
- [ ] 重复生成的 `.ssc`、SRT 和结构化文件字节一致。
- [ ] Stellarium 能力/版本不满足时明确 blocked，不静默降级为错误镜头。

## Task 5 / B9-PR-E：原子研究包、审核门禁、最小预览与 E2E

**Files:**
- Create: `apps/star-omen/src/video_pipeline/package.py`
- Create: `apps/star-omen/src/video_pipeline/review.py`
- Create: `apps/star-omen/src/video_pipeline/preview.py`
- Create: `apps/star-omen/tests/video_pipeline/test_package_review_preview_v1.py`
- Create: `apps/star-omen/tests/video_pipeline/test_vertical_slice_e2e_v1.py`
- Create: `docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`
- Modify: `.github/workflows/kaiyuan-stable-core.yml`
- Modify: `.gitignore`
- Modify: `docs/development/TASKS.md`
- Modify: `docs/development/WORK_LOG.md`

**Interfaces:**
- `write_package_atomic(...)`
- `evaluate_review_gate(...)`
- `build_minimal_preview_command(...)`

**Package and review acceptance:**

- [ ] staging 目录全部验证后才同文件系统原子发布；输出已存在时拒绝覆盖。
- [ ] 所有结构化资产、脚本、字幕和可选媒体进入 hash inventory。
- [ ] 审核维度独立：astronomy、classical evidence、editorial、render；每项记录 reviewer role、decision、UTC 和理由。
- [ ] `partial_metadata_only`、candidate-only、ambiguous mapping、hash 变化阻止 publishable classical status。
- [ ] B9 允许无音频 `preview.mp4`；不生成或承诺 `final.mp4`。
- [ ] FFmpeg 只构造 argv，不使用 shell；执行有 timeout、输出路径限制和退出码校验。
- [ ] 结构化包最大 10 MiB（不含 frames/media）、截图最多 30 张、单个本地预览默认 timeout 120 秒；超限明确失败。

**媒体确定性边界:**

- canonical JSON、`.ssc`、SRT、manifest 必须 bit-for-bit deterministic；
- MP4 不要求跨 OS/FFmpeg 版本字节一致；它的 hash 只绑定 exact toolchain manifest；
- 跨环境验证检查尺寸、时长、帧/音轨清单、字幕时间线和人工视觉结论，不错误要求相同 MP4 hash。

**PR gates:**

```text
G0 Governance
G1 Contract/schema registry
G2 Scientific golden + property smoke
G3 Retrieval/citation negative golden
G4 RuleAssessment projection
G5 Hermetic vertical E2E
G7 Package/review verification
```

**Nightly:** full Hypothesis、完整科学黄金、mutation testing、determinism scan。

**Local/self-hosted macOS:** Stellarium capability、实际 `.ssc`、截图清单、FFmpeg preview、人工视觉审核。

**E2E failure injection:**

- [ ] tampered astronomy provenance；
- [ ] missing angular separation；
- [ ] candidate-only quotation；
- [ ] ambiguous star mapping；
- [ ] dangling claim source reference；
- [ ] path traversal/script injection；
- [ ] changed frame/hash inventory；
- [ ] transport failure；
- [ ] noncanonical JSON；
- [ ] repeated structured generation nondeterminism；
- [ ] toolchain capability/version mismatch；
- [ ] timeout/resource limit exceeded。

## Completion Definition

B9 只有在以下全部成立时才能 `DONE`：

- B9-PR-A 至 B9-PR-E 均从各自最新 stable HEAD 实施、review 和合并；
- 三个 v1 契约、JSON Schema 和 registry 冻结并有兼容测试；
- 2026-07-21 研究包能从固定输入重复生成，即使无正式古籍规则也能诚实降为非占断版本；
- evidence-rich regression 覆盖 citable classical quote 正向路径；
- 科学事实、传统映射、古籍证据和现代转译有声明级 lineage；
- hermetic E2E 不联网、不启动 GUI、不写正式 Qdrant；
- 本地 macOS 实际生成 `.ssc` 截图和一个可查看竖屏预览；
- 结构化资产确定性，媒体确定性边界与 toolchain provenance 明确；
- 所有 required gates 和独立 review 通过；
- 最终 closeout 记录 exact-head CI、各 PR squash SHA 和剩余风险；
- 没有自动配音、批量生成、通用剪辑或自动发布。