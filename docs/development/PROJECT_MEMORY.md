# Chinese Star Omen Workspace 全局记忆

> 本文件是跨会话恢复入口，不替代实时 GitHub、`TASKS.md`、设计、计划、决策和阶段日志。每次恢复开发必须先重新核验远端 stable HEAD 与全部开放 PR。

## 1. 仓库事实

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD before closeout: e6cd46f87f16aef94074534aac09b03898ab9289
Verified at: 2026-07-30
Current closeout branch: codex/kaiyuan-b9-editorial-closeout-v1
Forbidden release target: main
Protected legacy collection: local_kb_default
V2 collection: local_kb_kaiyuan_v2 or random ephemeral CI collection
```

恢复时必须重新读取远端事实；本文件中的 SHA 只代表最后核验时点。

## 2. 当前阶段

```text
B4–B8: DONE
PLAN-T01 / B9-B10 planning: DONE
B9-PR-A Contract registry and compatibility: DONE
B9-PR-B Scientific provider and asterism catalog: DONE
B9-PR-C RuleAssessment and evidence lineage: DONE
B9-PR-D Editorial package and Stellarium script: MERGED, closeout in progress
B9-PR-E Atomic package, review, preview and E2E: READY after closeout
```

### B9 implementation chain

```text
B9-PR-A #32 squash: 26b4ce14afbc0010357c0fd9bc21bc69aa025f70
B9-PR-A closeout #33: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
B9-PR-B #34 squash: c72aa7630f58c5828b8343bcdd39c369efe1df76
B9-PR-B closeout #35: 48180f6239187b491e41d9f68be0a9aab8dde95d
B9-PR-C #36 squash: 38042b995e885101999c93c6698a9544f22a948b
B9-PR-C closeout #37: 523c724add978bc4bb51fc07a716c6a852c95447
B9-PR-D #38 final head: 2e0b4713c158a321de645d74808316852fc20177
B9-PR-D #38 squash: e6cd46f87f16aef94074534aac09b03898ab9289
```

### B9-PR-D final evidence

```text
Focused editorial/Stellarium: 41 passed in 1.55s
Full downstream: 395 passed in 4.29s
Development Governance: 30488433312 — success
B9 Editorial Stellarium: 30488434202 — success
Kaiyuan Stable Core: 30488433382 — success
Kaiyuan Upstream Runtime: 30488433542 — success
Changed files: 17 expected
Review threads: 0
Submitted reviews: 0
```

Detailed evidence:

```text
docs/development/B9_PR_D_DECISION.md
docs/development/B9_PR_D_CLOSEOUT.md
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

## 4. 已冻结公共契约

```text
AstronomyEvent/v1
RuleAssessment/v1
VideoPackage/v1
```

破坏性语义变化必须新建版本，不得原地重解释 v1。

## 5. B9 已固化边界

### Contract and science

- public time 为显式 UTC；Skyfield 内部 TT/TDB 不得冒充 UTC；
- ICRS/J2000 identity、date-dependent apparent/GCRS、ecliptic-of-date 与 WGS84 topocentric 分离；
- runtime ephemeris download 禁止；星历加载前后验证 hash 和文件身份；
- toolchain provenance 不保存机器绝对路径；
- 星官映射只接受 exact identity/membership/region records，不做 nearest-star 推断。

### RuleAssessment and evidence

- existing matcher/resolver 被复用，不复制规则语义；
- 只有 `candidate_only` 候选可做外部 evidence hydration；
- overlay、structured fallback、non-exact、multi-exact、candidate-only 或 resolver mismatch 不能升级为 citable；
- formal recommendation 只允许 selected + matched + unsuppressed + citable；
- `EvidenceBundle/v1` 不含原文、excerpt 或绝对路径；
- July 21 无正式规则时保持 blocked classical narration。

### Editorial and Stellarium

- B9-D 只支持一套固定 `zh-CN`、80 秒、9:16 模板；
- 每个 claim 有唯一 class、稳定 ID、同包 typed source refs 和 pending review；
- `VideoPackage.package_id` 绑定实际 claim class/text/source refs；
- classical quote asset ID 集合必须与 narration-allowed lineage ID 集合完全一致；额外或未授权 quote 明确失败；
- `开口破局` 只能属于带 `现代文化转译` 披露的 modern interpretation；
- 宿命承诺、恐吓和强迫性天象措辞 fail-closed；
- shot list 与 claims 一一对应、连续覆盖 0..80,000 ms；
- Stellarium 只是 renderer；`.ssc` 使用固定命令白名单并绑定 UTC、地点、对象和时长；
- B9-D 不启动 GUI、不截图、不生成 SRT/音视频。

## 6. B9 双轨验收

- 2026-07-21 公开样片若没有 citable 古籍规则，只生成 astronomy/history/modern-interpretation 版本并省略古籍占断；
- 独立 evidence-rich CI fixture 只验证 classical quote 正向路径，不冒充真实当日内容。

## 7. B10 完成分母

```text
100% primary passages 进入 inventory
每个 passage 有 eligibility 状态
每个 eligible passage 有 candidate 或 no-candidate reason
每个 candidate 有 approved/rejected/deferred_with_reason 终态
approved rules 全部通过 citable、去重/冲突和 source-change validation
ambiguous/deferred 始终保留在统计分母
```

单批发布不能冒充全书完成；模型辅助默认 disabled，可跳过。

## 8. 永久边界

- v2 只合入 `stable/kaiyuan-v2`，不进入 `main`；
- `apps/local-kb-unified` 是正式 KB 唯一写入者；
- `apps/star-omen` 不执行正式 ingest，不直接修改正式 Qdrant；
- `local_kb_default` 不得写、删、重建或迁移；
- raw corpus、`<pb:...>`、原字形和 `&KRxxxx;` 不静默改写；
- CText 仅做人工或定点比对；
- candidate、ambiguous、stale、missing 或 unverified 内容不是正式证据；
- transport/auth/timeout/contract/collection 错误不得变成健康空结果；
- 模型只能生成候选；
- Stellarium 只是渲染器；
- “开口破局”属于现代文化转译，不是古籍原文；
- 自动发布需要独立安全决策。

## 9. 强制恢复顺序

1. `AGENTS.md`；
2. 本文件；
3. 实时 stable HEAD 与全部开放 PR；
4. `DEVELOPMENT_MANUAL.md`；
5. `TASKS.md`；
6. 当前阶段决策与 closeout；
7. 当前设计与实施计划；
8. 只有任务在 `TASKS.md` 标记 `IN_PROGRESS` 后才允许写代码。

## 10. 下一动作

```text
完成 B9-PR-D docs-only closeout
→ 重新核验 stable HEAD 与开放 PR
→ 从新 stable 建 B9-PR-E 独立分支
→ 将 B9-PR-E 标记 IN_PROGRESS
→ tests-first RED
→ 实现 atomic package、review、SRT、bounded preview argv 和 hermetic E2E
```

禁止在 closeout 分支加入 B9-PR-E 功能代码。
