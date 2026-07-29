# Chinese Star Omen Workspace 全局记忆

> 本文件是跨会话恢复入口，不替代实时 GitHub、`TASKS.md`、设计、计划、决策和阶段日志。每次恢复开发必须先重新核验远端 stable HEAD 与全部开放 PR。

## 1. 仓库事实

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: c72aa7630f58c5828b8343bcdd39c369efe1df76
Verified at: 2026-07-30
Current closeout branch: codex/kaiyuan-b9-scientific-provider-closeout-v1
Forbidden release target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or random ephemeral CI collection
```

恢复时必须重新读取远端事实；本文件中的 SHA 只代表最后核验时点。

## 2. 当前阶段

```text
B4: DONE
B5: DONE
B6: DONE
B7: DONE
B8-T01: DONE
B8-T02: DONE
PLAN-T01 / B9-B10 planning: DONE
B9-PR-A Contract registry and compatibility: DONE
B9-PR-B Scientific provider and asterism catalog: MERGED, closeout in progress
B9-PR-C RuleAssessment and evidence lineage: READY after closeout
B9-PR-D Editorial package and Stellarium script: BACKLOG
B9-PR-E Atomic package, review, preview and E2E: BACKLOG
```

### B9-PR-A

```text
Implementation PR: #32
Implementation squash: 26b4ce14afbc0010357c0fd9bc21bc69aa025f70
Closeout PR: #33
Closeout squash: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
```

### B9-PR-B

```text
Implementation PR: #34
Base before merge: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
Final feature head: 3493270f65f2d177a9c755078477512fa585c0bb
Development Governance: 30476661474 — success
B9 Scientific Provider: 30476655763 — success
Kaiyuan Stable Core: 30476656261 — success
Kaiyuan Upstream Runtime: 30476655660 — success
Squash merge: c72aa7630f58c5828b8343bcdd39c369efe1df76
Focused tests: 40 passed
Full downstream: 319 passed
Review threads: 0
Submitted reviews: 0
```

Detailed evidence:

```text
docs/development/B9_PR_B_DECISION.md
docs/development/B9_PR_B_CLOSEOUT.md
```

### Other open PRs

最后核验时，旧路线 PR #1、#7 仍开放，均不以 `stable/kaiyuan-v2` 为目标。关闭前必须逐项确认已被 stable v2 取代。

## 3. 已批准路线：方案 C

```text
B9  契约先行＋2026-07-21 垂直样片
→ B10 《唐开元占经》全书规则结构化
→ B11 approved/citable gap 驱动的规则执行器 2.0
→ B12 批量天象选题、媒体生产与人工发布辅助
```

## 4. B9 顺序

```text
B9-PR-A Contract registry and compatibility              DONE
→ B9-PR-B Scientific provider and asterism catalog       DONE after closeout
→ B9-PR-C RuleAssessment and evidence lineage            next
→ B9-PR-D Editorial package and Stellarium script
→ B9-PR-E Atomic package, review, preview and E2E
```

每个 PR 必须从前一个 closeout 后的实时 stable HEAD 建立独立分支。

### 已冻结公共契约

```text
AstronomyEvent/v1
RuleAssessment/v1
VideoPackage/v1
```

### B9-PR-A 固化

- 严格 Pydantic 契约；
- Draft 2020-12 JSON Schema；
- schema registry；
- canonical fixture 与双层 SHA-256 绑定；
- UTC、有限数、正式推荐和同包引用 fail-closed；
- nested `$defs` 的 additive-optional-only 兼容门禁。

### B9-PR-B 固化

- public time 为显式 UTC；Skyfield 内部 TT/TDB 不得冒充 UTC；
- ICRS/J2000 identity、date-dependent apparent/GCRS、ecliptic-of-date 和 WGS84 topocentric 语义分离；
- 科学高度默认无折射；
- runtime ephemeris download 禁止；只接受调用方传入的本地 `.bsp` 和期望 hash/size；
- 星历文件加载前后验证 SHA-256 和文件身份；
- toolchain provenance 不保存绝对路径；
- 星官映射只接受 exact identity/membership/region records，不做 nearest-star 推断；
- ambiguous/unresolved 映射禁止正式星名口播；
- `HIP 65474 / Spica = 角宿一` 是首个双来源、可哈希身份。

## 5. B9 双轨验收

- 2026-07-21 公开样片若没有 citable 古籍规则，只生成 astronomy/history/modern-interpretation 版本，省略古籍占断；
- 独立 evidence-rich CI fixture 只验证 classical quote 正向路径，不冒充真实当日内容。

## 6. B10 完成分母

```text
100% primary passages 进入 inventory
每个 passage 有 eligibility 状态
每个 eligible passage 有 candidate 或 no-candidate reason
每个 candidate 有 approved/rejected/deferred_with_reason 终态
approved rules 全部通过 citable、去重/冲突和 source-change validation
ambiguous/deferred 始终保留在统计分母
```

单批发布不能冒充全书完成；模型辅助默认 disabled，可跳过。

## 7. 永久边界

- v2 只合入 `stable/kaiyuan-v2`，不进入 `main`；
- `apps/local-kb-unified` 是正式 KB 唯一写入者；
- `apps/star-omen` 不执行正式 ingest，不直接修改正式 Qdrant；
- `local_kb_default` 不得写、删、重建或迁移；
- raw corpus、`<pb:...>`、原字形和 `&KRxxxx;` 不静默改写；
- CText 仅做人工或定点比对；
- citable evidence 必须验证 source、book、locator、page、paragraph、heading、anchor 和 hash；
- candidate、ambiguous、stale、missing 或 unverified 内容不是正式证据；
- transport/auth/timeout/contract/collection 错误不得变成健康空结果；
- 模型只能生成候选；
- Stellarium 只是渲染器；
- “开口破局”属于现代文化转译，不是古籍原文。

## 8. 测试策略

```text
G0 Governance
G1 Contract
G2 Scientific
G3 Corpus/Retrieval
G4 Rule Quality
G5 Hermetic E2E
G6 Renderer
G7 Release
```

- 普通 PR：治理、契约、property smoke、黄金/负向、hermetic E2E、release verifier；
- Nightly：完整 property、科学黄金、全语料、mutation、长集成；
- Stellarium/FFmpeg：本地或 self-hosted macOS；
- 普通测试不得更新黄金文件；
- 长任务必须 checkpoint/resume、幂等、no-overwrite。

## 9. 强制恢复顺序

1. `AGENTS.md`；
2. 本文件；
3. 实时 stable HEAD 与全部开放 PR；
4. `DEVELOPMENT_MANUAL.md`；
5. `TASKS.md`；
6. `DECISIONS.md` 与当前阶段决策；
7. 当前设计、计划和计划审查；
8. 当前阶段 start/closeout 日志；
9. 只有任务在 `TASKS.md` 标记 `IN_PROGRESS` 后才允许写代码。

## 10. 下一动作

```text
完成 B9-PR-B docs-only closeout
→ 重新核验 stable HEAD 与开放 PR
→ 从新 stable 建 B9-PR-C 独立分支
→ 将 B9-PR-C 标记 IN_PROGRESS
→ 按 TDD 实现 RuleAssessment adapter 和 claim-level evidence lineage
```

禁止在 closeout 分支加入 B9-PR-C 功能代码。
