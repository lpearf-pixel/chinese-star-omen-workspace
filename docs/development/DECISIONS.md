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
