# 重要开发决策记录

本文件记录会影响后续实现、安全、兼容、语料或发布方式的长期决策。新决策应追加，不应静默覆盖历史理由。

## D-001 — 《开元占经》v2 不合入 `main`

- **Status:** Accepted
- **Decision:** v2 稳定发布线使用 `stable/kaiyuan-v2`；功能分支通过 PR 合入该分支。
- **Reason:** `main` 保留历史 workspace 状态，避免将仍在演进的 RAG、语料和证据契约直接视为默认稳定产品。
- **Consequence:** 所有 v2 PR 必须检查 base；不得将 release PR retarget 到 `main`。

## D-002 — 上游是正式知识库唯一写入者

- **Status:** Accepted
- **Decision:** `apps/local-kb-unified` 是 official KB source of truth，只有它可以执行正式 ingest 和写入正式 Qdrant。
- **Reason:** 防止上下游各自 ingest 造成重复、冲突、版本漂移和不可追踪来源。
- **Consequence:** `apps/star-omen` 只生成 candidate、查询、fallback 和同步状态；不得直接写正式库。

## D-003 — 保护 `local_kb_default`

- **Status:** Accepted
- **Decision:** v2 开发和测试不得删除、重建、迁移或写入 `local_kb_default`。
- **Reason:** 保留现有运行环境和回滚能力。
- **Consequence:** v2 使用 `local_kb_kaiyuan_v2`；CI 使用随机 ephemeral collection。

## D-004 — 原始语料不可变，CText 只做定点比对

- **Status:** Accepted
- **Decision:** 上传的全文和现有分卷共同作为本地 raw corpus 基线，不静默校订；CText Wiki《開元占經》只用于人工或定点片段比对。
- **Source:** `https://ctext.org/wiki.pl?if=gb&res=348345&remap=gb`
- **Authorization record:** 用户确认本项目范围可二次开发。
- **Editorial status:** 本地文本和参考页面均按未经正式校订处理。
- **Reason:** 自动覆盖会破坏版本可追踪性，CText 页面也不能被假定为无误权威校本。
- **Consequence:** 不实现批量抓取；差异只生成审计记录或人工校勘覆盖层；保留 `<pb:...>` 与 `&KRxxxx;`。

## D-005 — 文本定位语义集中到 `kb-text-core`

- **Status:** Accepted
- **Decision:** 卷、页码、标题、段落、规范化、offset、anchor、hash 和 primary 排序统一由 `packages/kb-text-core` 提供。
- **Reason:** 之前 filesystem fallback 和 candidate generator 使用不同算法，导致同一查询 offset、excerpt 和排序不一致。
- **Consequence:** 上游 ingest、下游 fallback、candidate 和审计不得复制不兼容实现。

## D-006 — 检索意图与检索池分离

- **Status:** Accepted
- **Decision:** `query_mode` 表示用户意图，`retrieval_stage` 表示阶段，`card_types` 表示实际过滤池。
- **Reason:** 旧实现把 `query_mode=evidence` 隐式转为 primary pool，和 Stage1 structured pool 做 AND 后产生必然零结果。
- **Consequence:** Stage1 和 Stage2 显式传递 pool；冲突 book identifiers 返回 contract error。

## D-007 — Candidate sync 业务状态与运行错误分离

- **Status:** Accepted
- **Decision:** `pending|merged|needs_review|stale` 只表达业务状态；认证、超时、服务、collection 和 contract 问题使用 run-level structured error。
- **Reason:** 网络错误被转换为 `hits=[]` 会把失败误写为健康 `pending`。
- **Consequence:** 任一运行错误保留所有 manifest 原字节和原状态；只有健康 HTTP 200 无命中才是 `pending`。

## D-008 — 最终引用采用 fail-closed passage 校验

- **Status:** Accepted
- **Decision:** 只有 source、book、locator、page、paragraph、heading、anchor 和 hash 校验通过的 primary passage 才是 `citable`。
- **Reason:** 仅凭 `card_type=fenjuan/fulltext` 与路径字符串无法证明文件存在或引文仍有效。
- **Consequence:** legacy 最小引用保持可加载但默认 candidate-only；mismatch 返回精确状态。

## D-009 — Passage 级增量 ingest

- **Status:** Accepted
- **Decision:** 使用稳定 passage identity 和内容 hash 进行 skip/insert/upsert/delete reconciliation。
- **Reason:** 全量重新 embedding 成本高，且难以安全删除失效 point。
- **Consequence:** stale 删除仅限 v2 managed points；失败和空语料不得删除旧 point 或发布成功 manifest。

## D-010 — 文件化开发治理

- **Status:** Accepted
- **Decision:** 采用 `AGENTS.md`、开发手册、任务台账、工作日志、决策记录五层治理结构，并用 CI 要求代码 PR 更新任务或工作日志。
- **Reason:** 避免任务仅存在于聊天中、计划状态与实际代码脱节、开发会话遗漏安全边界。
- **Consequence:** 开发前必须阅读手册；任务先入台账；完成后回写验证证据；治理门禁对稳定线 PR 生效。

## D-011 — 规则条件采用三值语义

- **Status:** Accepted
- **Decision:** 所有适用规则条件使用 `pass | fail | unknown`；未配置条件不参与聚合，缺失或无效测量值为 `unknown`，不能视为通过。
- **Aggregation:** 核心身份失败为 `not_matched`；已知非核心失败为 `partial_match`；无已知失败但存在 unknown 为 `insufficient_data`；全部适用条件通过后，再根据 B4 citable evidence 判定 `matched` 或 `candidate_only`。
- **Scoring:** `trigger_ratio = pass_count / applicable_count`，unknown 进入分母但不进入分子，未配置条件不进入分母。
- **Reason:** 古代与现代天象研究资料常存在测量缺口。把缺失值当通过会制造虚假的完整匹配；把缺失值当失败又会伪造负面观测。三值状态能同时保持 fail-closed 和研究可解释性。
- **Compatibility:** 保留 `missing_conditions`、旧状态和旧输出字段，新增 `condition_states`、`unknown_conditions`、`failed_conditions`、`trigger_ratio` 与 `insufficient_data`。
- **Consequence:** 非有限数必须输出严格 JSON-safe trace；非法阈值和非法 rule trigger 配置明确失败；B5-T02 再单独实现冲突组 resolution policy。

## D-012 — 冲突解析采用确定性分组策略并区分正式与临时推荐

- **Status:** Accepted
- **Decision:** 同一 `conflict_group` 由单一 `resolution_policy` 解析；支持 `highest_score`, `highest_priority`, `prefer_primary_evidence`, `manual_review`。同组 policy 不一致或未知 policy 明确失败。
- **Ordering:** 各 policy 先按其主维度排序，再按其余 score/priority/evidence 维度排序，最终统一以升序 `rule_id` 打破完全相同的 tie。
- **Manual review:** 多候选 `manual_review` group 不产生正式 selected rule；仅暴露 deterministic provisional id。只有没有正式推荐时，top-level 才暴露 `provisional_recommended_rule_id`，并保持 `recommended_rule_id=null`。
- **Auditability:** suppressed rule 不从 `matches` 删除；每行保存 selected/suppressed/manual 状态，group trace 保存候选、顺序、选择、临时选择和抑制原因。
- **Reason:** 冲突解析既要可复现，又不能把人工复核候选静默升级为研究结论。独立纯 resolver 使 policy 可单测且不污染条件、证据或检索边界。
- **Compatibility:** 无冲突和默认 `highest_score` 保留旧的 priority/score 全局推荐边界；保留 `conflict_detected`, `conflict_reasons`, `recommended_rule_id`，新增 provisional/status/trace 字段。

## D-013 — 规则证据迁移只接受唯一精确 passage，并写入独立输出

- **Status:** Accepted
- **Decision:** legacy primary evidence 只有在 `kb-text-core` 找到唯一 exact raw 或 exact normalized primary passage，且补齐后的引用通过 B4 resolver `status=citable` 时才标记 `migratable`。
- **Fail-closed:** ambiguous、loose、heading-only、无 anchor、无 evidence 和 validation failure 均不得产生正式迁移结果。
- **Write policy:** audit 默认只读；apply 必须写调用方指定的独立输出 JSON，拒绝覆盖输入；全计划验证成功后才原子替换输出。
- **Provenance:** 每项保留 before/after、match type、passage trace 和状态；原始规则与 raw corpus 均不静默改写。
- **Reason:** 批量补字段若依赖模糊匹配会把错误卷页固化成正式证据。唯一精确命中加 resolver 二次验证能够复用既有 citation 边界并保持可审计回滚。

## D-014 — Primary passage cache 只缓存原文快照与解析结果

- **Status:** Accepted
- **Decision:** `apps/star-omen` 使用进程内、容量受限、线程安全的 LRU，按 resolved path、parser identity 和 exact-byte SHA-256 复用严格 UTF-8 source snapshot 与 `kb-text-core` passage；不缓存查询结果或 `citable` 结论。
- **Invalidation:** 每次加载读取并 hash exact bytes；content hash 或 parser identity 变化即重新解析。`mtime_ns` 与 size 保留为指纹/观测字段，但不得替代 hash，因此即使时间戳与长度被保留也不会返回陈旧 passage。
- **Failure:** missing、unreadable、invalid UTF-8、unstable read 或 parse error 不得回退到旧 entry，也不得转换为健康空结果。
- **Reason:** filesystem fallback、resolver 与 migration 重复解析相同 Markdown；共享只读 passage snapshot 可以降低解析成本，同时不改变检索顺序、证据校验或原始语料。
- **Consequence:** cache 仅存在于下游进程内，不写磁盘、corpus、candidate 或 Qdrant；正式 evidence 每次仍执行 B4 全部 fail-closed checks。

## D-015 — 可观察性使用附加 envelope，错误语义保持不变

- **Status:** Accepted
- **Decision:** downstream retrieval 与 candidate sync 使用 `kb-observability/v1` 附加 envelope 记录 monotonic latency、请求/原始/返回 pool、fallback reason、collection、corpus version 和 structured run error。
- **Error boundary:** retrieval 失败仍抛 `KBSearchError`，trace 只附加到 `details.observability`；sync 失败仍返回 `run_status=error` 且 manifest 原子不写。Telemetry `run_error` 只 allowlist `code/status_code/retryable`，权威 top-level error 保持原契约，避免复制可能含 secret/content 的 upstream message/details。
- **Provenance:** collection 来自 effective response/request/meta；corpus version 只来自 upstream response/meta。两阶段 official 值必须一致才提升到顶层，冲突时为 null 并记录 `provenance_conflicts`，不伪造或猜测。
- **Safety:** trace 严格 JSON-safe，不记录 secret、anchor、source content 或 raw error body；成功 manifest 不持久化 nondeterministic latency。
- **Reason:** in-band versioned trace 能被 CLI、测试与报告共同消费，同时避免引入外部 telemetry 服务或改变 B4 的健康空结果、运行错误和 candidate 状态边界。

## D-016 — Stable 发布演练采用只读三阶段快照对账

- **Status:** Accepted
- **Decision:** B6-T03 使用 `before_switch → after_switch → after_rollback` 三阶段 JSON 观测和纯验证器演练切换；验证器不连接或修改 Qdrant，不执行 ingest，也不更改服务配置。
- **Manifest:** 切换后的 `/v1/meta` 必须与期望 release manifest identity 完全一致；回滚后的 meta 必须恢复到切换前记录的 manifest identity。missing、invalid 或 mismatch 均 fail-closed。
- **Rollback:** 回滚只恢复切换前记录的 read routing。若原路由为 `local_kb_default`，允许恢复读取，但任何阶段都不得写入、删除、重建或迁移该 collection。
- **Protection:** `local_kb_default` 的 `exists`、`points_count` 和 `config_hash` 指纹在三个阶段必须完全一致；缺少快照也视为失败。
- **Reason:** 直接自动切换生产服务需要环境权限且带来数据风险；只写手册又无法提供可重复证据。纯验证器可在 CI 使用 synthetic fixture，并让生产操作保存同一契约的审计 artifact。
- **Consequence:** CI 通过仅证明验证器和演练契约有效，不等同于生产已发布；生产证据必须另行记录实际 artifact hash、release head、workflow 和操作者。
