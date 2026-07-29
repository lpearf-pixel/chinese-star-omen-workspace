# B9-PR-C RuleAssessment and Evidence Lineage Start

## 2026-07-30 — task started

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Verified stable HEAD: 48180f6239187b491e41d9f68be0a9aab8dde95d
Feature branch: codex/kaiyuan-b9-rule-assessment-lineage-v1
Task: B9-PR-C RuleAssessment and evidence lineage
State: IN_PROGRESS
```

## 实时仓库核验

- stable 与 `48180f6239187b491e41d9f68be0a9aab8dde95d` identical；
- 开放 PR 只有旧路线 #1、#7；
- B9-PR-A 与 B9-PR-B 已实现并完成 docs-only closeout；
- B9-PR-D 及以后保持 `BACKLOG`。

## Existing boundaries reused

```text
AstronomyEvent/v1
→ existing rule_engine.minimal_matcher
→ existing citable-evidence/v2 resolver
→ RuleAssessment/v1
→ EvidenceBundle/v1
```

现有 matcher 已提供三值条件、`matched|candidate_only|insufficient_data|partial_match|not_matched`、冲突选择/抑制、正式/临时推荐和证据摘要。本 PR 只做稳定投影与证据 lineage，不复制规则语义。

现有 two-stage retriever 顺序保持不变：

```text
official structured_recall
→ official primary_evidence
→ filesystem fallback only after healthy empty official primary
```

transport/auth/timeout/contract/collection 错误不得捕获为无命中。

## Fixed scope

1. `AstronomyEventV1` 到 matcher event mapping，显式投影 body/event/target、测量和可见性；
2. `build_rule_assessment(...)` 与完整 build result；
3. formal/provisional recommendation projection；
4. evidence status projection and stable evidence IDs；
5. unresolved embedded evidence 的可选 two-stage hydration；
6. unique exact primary candidate only，resolver 全字段通过后才可 citable；
7. content-free `EvidenceBundle/v1`，绑定 assessment、rule、evidence、claim class 和 blocking reasons；
8. evidence-rich CI fixture 与 2026-07-21 blocked-classical regression；
9. focused diagnostic workflow and full regression gates。

## Explicit exclusions

- 不生成编辑文案或 claim text；
- 不生成 Stellarium `.ssc`、SRT、音频或视频；
- 不执行全书规则抽取；
- 不修改 corpus、candidate、ingest、Qdrant、collection 或 `local_kb_default`；
- 不把 overlay、structured fallback、多命中或 mismatch 证据升级为 citable。

## TDD order

```text
commit missing-module and fail-closed tests
→ observe RED on exact branch head
→ implement pure event/matcher projection
→ implement evidence status/lineage bundle
→ implement optional two-stage hydration
→ focused GREEN
→ review regressions and full downstream
→ exact-head workflows / independent review
```

## Environment

当前执行环境通过 GitHub contents API 操作远端分支。focused RED/GREEN 以专用 GitHub Actions 为权威；完整 downstream、retrieval error semantics 和 existing matcher regressions 由 Stable Core/Upstream Runtime 门禁覆盖。不得因本地环境限制跳过断言。
