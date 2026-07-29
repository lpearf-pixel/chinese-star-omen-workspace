# Chinese Star Omen Workspace 全局记忆

> 跨会话恢复入口；不替代实时 GitHub、任务台账、设计、决策和阶段日志。恢复开发必须先重新核验远端 stable HEAD 与全部开放 PR。

## 1. 当前仓库事实

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Last verified stable HEAD: b0a39ff4ec243aefb324287e1ab1b1a564fc38b6
Verified at: 2026-07-30
Current closeout branch: codex/kaiyuan-b9-preview-media-closeout-v1
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
B9-G6-E1 preview-media evidence hardening: MERGED, closeout in progress
B9-G6 real macOS renderer evidence: READY after closeout
B9 overall: VERIFYING
B10: BLOCKED until real G6 evidence and final B9 closeout
```

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
```

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

## 4. Open legacy PRs

最后核验时旧路线 PR #1、#7 仍开放，均不以 `stable/kaiyuan-v2` 为目标。关闭前必须逐项证明已被 stable v2 完全取代。

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

## 7. 当前唯一未完成门禁：B9-G6

Hosted CI 没有启动 Stellarium 或 FFmpeg，不能作为真实 G6 证据。仍需在 macOS 完成：

```text
加载 exact scene.ssc
生成 exact preview.mp4
使用受限 ffprobe 字段验证媒体
人工核对 UTC、地点、对象、字幕和画面
最多 30 张截图及 size/SHA-256 inventory
canonical media-bound LocalCapabilityEvidence/v1
```

Runbook：`docs/development/B9_VERTICAL_SLICE_RUNBOOK.md`。

G6 完成前：

- B9 不得标记 DONE；
- B10 不得启动；
- 不得声称已有正式视频或可自动发布；
- synthetic CI review records 不是发布审核。

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
合并 preview-media docs-only closeout
→ 运行 macOS G6 collector
→ 上传 evidence archive
→ 独立验证媒体、脚本、命令、截图和工具版本
→ final B9 closeout
→ only then B10
```
