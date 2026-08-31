# Chinese Star Omen Workspace 全局记忆

> 跨会话恢复入口；不替代实时 GitHub、任务台账、设计、决策和阶段日志。恢复开发必须先重新核验远端 stable HEAD 与全部开放 PR。

## 1. 当前仓库事实

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: 99c0a85c1f944add8d013aedbae830fe022b7c3b
Verified at: 2026-08-31
Current feature branch: codex/kaiyuan-evidence-feedback-loop-skeleton-v1
Current task: VFL-T01-D1 remote-delivery reconciliation VERIFYING; VFL-T01
local S0 DONE; B10-PR-C human-review BLOCKED
Open PRs: #54 only; Draft and blocked on Reviewer B
Forbidden target: main
Protected collection: local_kb_default
```

本文件中的 SHA 只代表最后核验时点。

## 2. 当前阶段

```text
B4–B8: DONE
B9 planning: DONE
B9-PR-A contracts: DONE
B9-PR-B science/asterisms: DONE
B9-PR-C RuleAssessment/lineage: DONE
B9-PR-D editorial/Stellarium script: DONE
B9-PR-E package/review/preview machinery: DONE implementation
B9-G6-E1 preview-media evidence hardening and closeout: DONE (#42/#43)
B9-G6 first real macOS evidence: REJECTED after archive verification
B9-G6-E2 scientific hard gate: DONE (#44)
B9-G6-E3 AI visual report: DONE (#45)
B9-G6-E4 lightweight human confirmation: DONE (#46 plus accepted local evidence)
B9-G6-E5 FFmpeg runtime preflight and audience-copy follow-up: DONE (#48)
B9-G6-E6 evidence handoff integrity: DONE (#49 plus accepted corrected archive)
B9-G6 run 20260730T121805Z: ACCEPTED
B9 final closeout: DONE (#50)
B9 overall: DONE
B10-T00 program charter and threshold governance: DONE (#51)
B10-PR-A OmenRule/v2, identity and annotation contract: DONE (#52)
B10-PR-B passage inventory, source invalidation and resumable batches: DONE (#53)
B10-PR-C calibration pilot: BLOCKED on two independent human reviews (#54)
B10-R01/R02 research source audits: DONE (#56)
B10-R03 P0 related Wikisource localization: DONE (#57, squash 090f1b95d1c0b798077162408cea3d3bedd975a5)
B10-R04 reversible multi-text source model: DONE (#58; squash 1a30070d3517d07097fbffe3a8ed43a9a0144c5f)
B10-R05 bounded 15-accession source expansion: DONE (#59; squash `bcb72c9c922a8d87319cc88aec7a772016a1cf27`)
B10-R06 Core14 disputed-case second evidence review: DONE (#64 Draft evidence support; PR #54 comment 5173585995)
B10-R07 Core14 provisional usability stratification: DONE (#64 continuation; 11 provisional-use + 3 isolated evidence-supplement; PR #54 comment 5176472354)
ASTRO-R01 twenty-eight mansion and external-media audit foundation: DONE (approved phases 1–5)
B10-R08 PR #64 stable-integration reconciliation: DONE (integration commit `2384533291b1163738fb06f6984a348f78ecc558`)
PR #64 merged to stable: DONE (2026-08-14, `99c0a85c1f944add8d013aedbae830fe022b7c3b`)
B10 overall: IN_PROGRESS
VFL-T01 offline evidence-to-video feedback skeleton: DONE for local S0
implementation/review scope; feature branch delivered remotely at `f36b146`;
PR/integration/render/publication unclaimed
```

### VFL-T01 local S0 closeout

- Tasks 1–5 deliver strict lifecycle contracts, defensive local-probe
  comparison, deterministic non-applying candidates and B9 requests, atomic
  package closure, and the episode 22 offline CLI.
- Task 5 was hardened twice after the initial CLI delivery: `b190614` protects
  literal shell path bytes, while `a951680` prevents Make-function evaluation
  and internal transport-alias override.
- The first whole-branch review at `59af182` found exactly FR-01 and FR-02 as
  Important, with `0 Critical / 0 Minor`: non-authoritative modern/retrieval
  evidence could become decisive, and outcome/run metric IDs could collide.
  Contract-owned invariants in exact four-path fix `21e6904` close both gaps.
  The same reviewer approved the scoped fixes with zero remaining findings
  after exhaustive/adversarial matrices. Current code head is
  `21e69048b7277023458ee5217acec85d259eebb8`, tree
  `c869c1f3f81a5cdedf92ec026054b22e8e9bb958`.
- Fresh local evidence: final-review focused `58 passed`; feedback-loop
  `86 passed`; related regressions `112 passed`; full supported downstream
  `759 passed`; governance unit `21 passed`; compileall and development
  governance passed. The canonical eight-member no-outcome CLI run is
  `feedback-run:vfl:e2fb1a2d98be3ea09b2c885f68832530741772afc588a40c9005c3761dcef6e0`,
  with manifest SHA-256
  `00b96fd7dec1ad90da94af29bea90860b85b6712ad336c7bb7d345e412a8ebc4`.
- An occupied destination returned nonzero with the entire package unchanged
  and no staging residue. Renewed whole-branch review approved exact candidate
  `33657fae698970a9d820870ab180c3712e9f295a`, tree
  `8bcce81842e6130d0328b525168f8b46c9955d7e`, across `15 commits / 25 paths /
  15 code files` with `0 Critical / 0 Important / 0 Minor`. FR-01/FR-02 remain
  closed, recorded findings.
- Local S0 is `DONE`. At the 2026-08-30 closeout, Runner was `NOT RUN` and the
  feature branch was unpushed with no PR; no stable merge, render, upload or
  publication had occurred. This remains the accurate historical closeout
  boundary.
- On 2026-08-31 the reviewed closeout head
  `f36b146ddb08809b6b23a8db5e5fc94393165a21`, tree
  `fe4babc7c34328a4b18f22bbea998882ae38b2dc`, was non-force pushed as
  `codex/kaiyuan-evidence-feedback-loop-skeleton-v1`. Remote stable remained
  `99c0a85`; open PRs remained only human-blocked Draft #54. No VFL PR, merge,
  Runner, render, upload or publication occurred, and no later stage was
  authorized.

## 3. B9 merge chain

```text
#32  B9-PR-A implementation  26b4ce14afbc0010357c0fd9bc21bc69aa025f70
#33  B9-PR-A closeout        8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
#34  B9-PR-B implementation  c72aa7630f58c5828b8343bcdd39c369efe1df76
#35  B9-PR-B closeout        48180f6239187b491e41d9f68be0a9aab8dde95d
#36  B9-PR-C implementation  38042b995e885101999c93c6698a9544f22a948b
#37  B9-PR-C closeout        523c724add978bc4bb51fc07a716c6a852c95447
#38  B9-PR-D implementation  e6cd46f87f16aef94074534aac09b03898ab9289
#39  B9-PR-D closeout        d16e75d9eda153c13fcbcfc13449c49bb1a8af60
#40  B9-PR-E implementation  92e3c08371bb52651ea0fd5e4357fb9ce7dcd82f
#41  B9-PR-E closeout        41a613a1606cbbf8a77336fa01ea4c98236b57c7
#42  G6 preview-media fix    b0a39ff4ec243aefb324287e1ab1b1a564fc38b6
#43  G6 media closeout       28f3b2a1ce5a9e324b6fc03060423bbacf1b917a
#44  G6 scientific gate      d6f2f862d7cf45c1008925f6d4286aabb4e43077
#45  G6 AI visual review     f937c60c76f5e450279e05b3c04de67e296fa687
#46  G6 human confirmation   939c5272a84a1bf3dd2e9c72037ea180f76e8adf
#47  G6 collection readiness 23e9d0fce3c5f2609456430f9829234afe2e704b
#48  G6 FFmpeg preflight     c2be80c2adbf307178c353a6769ab98c170d1930
#49  G6 handoff integrity   e5a5315fcea72ea878bf62968170d4f262fabc5d
#50  B9 final closeout      a10e33118c2e34f947a099492bb01e13a07a98a8
```

## 4.2 Second real G6 evidence disposition

Run `20260730T121805Z` passed the canonical renderer hard gate, hash-bound AI
review, three human confirmations, final assisted review, media inspection and
all evidence byte bindings. Its first uploaded handoff archive is not accepted:

```text
Archive SHA-256: 0271e15b99151811123ff47f25e5254dec42703001e6bc8079344e6f66916918
Core review and media chain: valid
Capability Stellarium version: 26.2.0
Bound overview window title: Stellarium 26.1
Absolute inventory paths: 5
AppleDouble archive members: 16
Disposition: handoff rejected; preserve evidence bytes and rebuild capability/archive
```

The preview, screenshots and assisted-review reports do not need regeneration.
The actual application version must be read from the `.app`, capability
evidence rebuilt with that version, and the archive recreated from a fixed
member list with a relative screenshot inventory.

The corrected archive was subsequently regenerated with the merged PR #49
handoff command and independently verified:

```text
Archive: b9-local-g6-evidence-20260730T121805Z-corrected-v1.tar.gz
Archive SHA-256: 8a4af09210961fada5cb6e8ac1a3344d4055307bb7d8c48920c90f71c4020214
Archive members: 19 fixed members
Unsafe paths, links or devices: 0
Absolute machine paths: 0
AppleDouble members: 0
Screenshot inventory: 5 relative paths, all byte hashes matched
Stellarium: 26.1.0, matching the bound Stellarium 26.1 overview
FFmpeg: 8.1.2
Preview: 1080x1920, H.264, 80000 ms, 1 video, 0 audio
Renderer hard gate: passed, 0 issues
AI visual review: needs_human_review
Human confirmations: all true
Resolved assisted review: approved
Disposition: accepted for B9-G6
```

This acceptance applies only to the exact corrected archive hash above. It
does not change the rejected disposition of either earlier archive.

## 4.1 First real G6 evidence disposition

The archive `b9-local-g6-evidence-20260730T040856Z.tar.gz` passed outer SHA-256, archive safety, internal hash, media and capture-timing checks. It was rejected for content:

```text
Archive SHA-256: fc49031dc98083e46aad912b3cfaa43cea611ec80934c37352ba9691cf9eff52
Recorded fixture separation: 3.25 deg
Independent Shanghai topocentric separation: approximately 5.4 deg
Fixture ephemeris SHA-256: placeholder aaaaaaaaaa...
Disposition: rejected; never use for B9 closeout
```

The accepted remediation is a three-level gate: deterministic scientific/media/OCR hard checks, hash-bound AI visual review, then three layperson experience checks. Neither AI nor a person can override a machine rejection.

### PR #42 final evidence

```text
Final feature head: 88e66d8e5ec85db78f4fddecec2c4d7ffc6a9895
Focused: 48 passed in 1.42s
Full downstream: 443 passed in 3.98s
Development Governance: 30493748550 — success
B9 Package Review Preview: 30493748497 — success
Kaiyuan Stable Core: 30493748498 — success
Kaiyuan Upstream Runtime: 30493748522 — success
Changed files: 8 expected
Review threads: 0
Submitted reviews: 0
```

Detailed records:

```text
docs/development/B9_G6_E1_START.md
docs/development/B9_G6_E1_DECISION.md
docs/development/B9_G6_E1_CLOSEOUT.md
docs/development/B9_VERTICAL_SLICE_RUNBOOK.md
```

## 4. Legacy PR disposition

GOV-T02 的 70 行逐路径审计已由 PR #61 合并为
`08fb71ab1db7de509154214cca44693a5de4859c`。旧路线 PR #1 与 #7
均已收到哈希绑定的取代说明，并分别以 `closed / merged=false`
关闭；分支和历史保留。PR #62 final head
`82b464049f1ca39557696016dddab3cdcfc2762c` 通过三项 Actions 和终审，
随后 squash 合并为 `96b41a4524d36c7ffb2f1e2ec66ca4aed1565962`。
GOV-T02 已在 stable 生效为 `DONE`；PR #62 合并后的即时开放集仅有受两名
不同真人 Reviewer A/B 门禁阻塞的 #54。此后出现的治理 PR 不改变该历史
事实。两条旧分支不得重新合并或 cherry-pick。

## 5. 冻结公共契约

```text
AstronomyEvent/v1
RuleAssessment/v1
VideoPackage/v1
```

破坏性语义变化必须新建版本，不得原地重解释。

## 6. B9 已固化边界

### Science

- public time 为显式 UTC；Skyfield 内部 TT/TDB 不冒充 UTC；
- ICRS/J2000 identity、apparent/GCRS、ecliptic-of-date、WGS84 topocentric 分离；
- runtime 星历下载禁止；本地 `.bsp` 在加载前后校验 hash 和文件身份；
- 星官映射只接受有来源的 exact identity/membership/region，不使用 nearest-star 猜测。

### Rule and evidence

- 复用既有 matcher/resolver，不复制规则语义；
- 只有 `candidate_only` 候选可做外部 hydration；
- overlay、structured fallback、non-exact、multi-exact、candidate-only 或 resolver mismatch 不得升级为 citable；
- formal recommendation 只允许 selected + matched + unsuppressed + citable；
- `EvidenceBundle/v1` 不含原文或绝对路径；
- July 21 无正式规则时 classical narration 保持 blocked。

### Editorial and renderer script

- 只支持固定 `zh-CN`、80 秒、9:16 模板；
- package ID 绑定实际 claim class/text/source refs；
- classical quote asset 集合必须与 narration-allowed lineage 完全一致；
- `开口破局` 只能属于带 `现代文化转译` 披露的 modern interpretation；
- shot 与 claim 一一对应并连续覆盖 0..80,000 ms；
- `.ssc` 只使用固定命令白名单；Stellarium 只是 renderer。

### Package, review and preview

- SRT、JSON、`.ssc` 与 manifest 确定性生成；
- structured package 总计不超过 10 MiB、成员不超过 256；
- 同文件系统 staging 后使用 atomic no-replace 发布；
- astronomy、classical evidence、editorial、render 四维审核分别绑定 canonical artifact hash；
- classical review hash 同时绑定 `RuleAssessment/v1` 与 `EvidenceBundle/v1`；
- preview 只构造固定 1080x1920、80 秒、shell-free FFmpeg argv，timeout 最大 120 秒；
- `final.mp4` 不属于 B9；自动发布需要独立安全决策。

### Preview media evidence

- `PreviewMediaEvidence/v1` 绑定实际 `preview.mp4` 的 byte size、SHA-256、1080x1920、H.264、80,000±500 ms、1 video、0 audio；
- 文件必须是非 symlink regular file，受 512 MiB 上限约束并执行前后身份复验；
- ffprobe JSON 由外部调用者提供，模型不启动进程；空 programs/stream_groups 可兼容，非空即失败；
- `preview_observed=true` 必须有 media evidence；approved 还必须有截图；
- capability evidence 不保存机器绝对路径。

### FFmpeg runtime

- `preview-command.json` 保持机器无关，不写 Homebrew 或绝对二进制路径；
- B9 预览必须先对实际选中的 FFmpeg/ffprobe 执行字幕滤镜、`libx264`
  和最小字幕 burn-in smoke；
- `B9_FFMPEG_BIN`、`B9_FFPROBE_BIN` 可覆盖 PATH，但覆盖值本身不进入
  structured package；
- 仅检查 `ffmpeg -filters` 不足以证明可渲染；真实 smoke 失败必须在
  80 秒 preview 之前 fail-closed。

## 7. B9 final closeout result

真实 macOS G6 已由修正归档
`8a4af09210961fada5cb6e8ac1a3344d4055307bb7d8c48920c90f71c4020214`
完成并通过独立复验。Hosted CI 只验证代码与契约，未被用来替代
Stellarium、FFmpeg、截图或人工播放证据。

PR #50 的最终 exact head
`bec4b0a9c5b5d878367ef14341a9ba93752ec417` 通过 Development
Governance、Kaiyuan Stable Core 和 Kaiyuan Upstream Runtime，4 个变更
文件均为预期治理文档，且无 review 或 unresolved thread。PR #50
squash merged 为 `a10e33118c2e34f947a099492bb01e13a07a98a8`。

B9 已在 stable 生效为 `DONE`。这不授权自动发布、TTS、批量媒体或
`final.mp4`。

## 8. 永久安全边界

- v2 只合入 `stable/kaiyuan-v2`；
- `apps/local-kb-unified` 是正式 KB 唯一写入者；
- `apps/star-omen` 不执行正式 ingest 或正式 Qdrant mutation；
- `local_kb_default` 不得写、删、重建或迁移；
- raw corpus、`<pb:...>`、原字形、`&KRxxxx;` 不静默改写；
- candidate、ambiguous、missing、stale、unverified 不是正式证据；
- transport/auth/timeout/contract/collection 错误不得变成健康空结果；
- 模型只能生成候选；
- 自动发布需要独立安全决策。

## 9. 强制恢复顺序

1. `AGENTS.md`；
2. 本文件；
3. 实时 stable HEAD 和全部开放 PR；
4. `DEVELOPMENT_MANUAL.md`；
5. `TASKS.md`；
6. 当前阶段 decision/closeout；
7. 设计、计划和 G6 runbook；
8. 任务标记 `IN_PROGRESS` 后才允许写代码。

## 10. 下一动作

```text
ASTRO-R01 phases 1–5, DOC-R01 and PR #64 are integrated at stable 99c0a85c1f944add8d013aedbae830fe022b7c3b
→ keep C02/C09/C11/C13/C14/C31/C41/C43/C44/C45/C47 in provisional internal use pending Reviewer B
→ keep C03/C24/C33 isolated for evidence supplementation
→ keep PR #54 Draft and BLOCKED until a different human independently completes Reviewer B
→ validate real reviewed fixtures and the approval record without AI substitution; any frozen-gate failure remains BLOCKED
→ PR-C may publish canonical threshold-freeze.json only after every frozen gate passes
→ R05 does not authorize B10-PR-D/E/F; each remains BACKLOG until its entry gates pass and the task is separately recorded IN_PROGRESS
↳ VFL-T01 local S0 is DONE after renewed review of 33657fa / 8bcce818
→ keep VFL-T01 at a manual publication handoff; all improvement/learning outputs remain non-applying proposals and any later stage requires a separate task
→ GOV-T04 does not replace nightly, real-device, corpus, scientific, security, migration or human evidence
```

The R05 merge does not authorize a production multi-text schema, new Core14
claims, official ingest, Qdrant access, `local_kb_default` access, B11/B12,
automatic publishing or any operation on `main`.

D-031 permits only the additive VFL-T01 offline control plane. It does not
change the preceding B10/B11/B12 gates and cannot apply cross-module changes.
