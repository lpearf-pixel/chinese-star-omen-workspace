# B6 《开元占经》v2 Stable 发布与回滚演练手册

本手册只适用于 `stable/kaiyuan-v2`。执行前依次读取 `AGENTS.md`、开发手册、任务台账、决策记录、B6-T03 设计/计划和最新工作日志。

## 1. 不可突破的边界

```text
Release target: local_kb_kaiyuan_v2
Protected legacy collection: local_kb_default
CI: synthetic snapshot or random ephemeral collection
Forbidden release branch: main
```

演练验证器是只读的：它不连接 Qdrant、不执行 ingest、不切换配置、不重启服务，也不修改 corpus、candidate 或 manifest。任何操作若准备删除、重建、迁移或写入 `local_kb_default`，立即停止。回滚期间保留新旧 collection，不执行清理。

## 2. 发布前置条件

1. PR base 是 `stable/kaiyuan-v2`，最新实际 head 的 required workflows 全绿且 review 已解决。
2. 上游已在 `local_kb_kaiyuan_v2` 完成一次成功 ingest；失败或空语料运行不得生成成功 manifest。
3. 保存待发布 `corpus_manifest.json`，确认这些 identity 字段完整：`schema_version`、`corpus_version`、`ingest_run_id`、`source_manifest_hash`、`collection`、`created_at`、`managed_by`、`collection_schema`。
4. `/v1/health` 必须 ready；`/v1/meta` 必须 `meta_status=ok`；不得把超时、认证、collection 或 contract 错误记录成零命中。
5. 指定操作者、变更窗口、回滚负责人、artifact 目录和事件记录编号。

## 3. 三阶段 artifact

以 `tests/fixtures/release_drill_v1.json` 为结构模板，建立独立的实际 artifact，不要覆盖 committed fixture。三个 phase 是：

- `before_switch`：切流前实际 read routing、health/meta、两阶段 smoke 和 collection 指纹；
- `after_switch`：切到 `local_kb_kaiyuan_v2` 后的同组观测；
- `after_rollback`：恢复切换前 read routing 后的同组观测。

每个 phase 的 `collections.local_kb_default` 必须记录：

```json
{"exists": true, "points_count": 41, "config_hash": "sha256:..."}
```

`config_hash` 应由规范化后的只读 collection configuration 计算；不得包含 API key、URL credential、原文、anchor 或 raw response body。三个 phase 的 protected fingerprint 必须完全一致。

若切换前 read routing 是 `local_kb_default`，允许回滚时恢复读取它；这不是写入授权。其 manifest identity 必须在 `before_switch` 与 `after_rollback` 一致，其 fingerprint 在所有 phase 一致。

## 4. 采集观测

对当前服务分别保存 health 和 meta 的 HTTP status 与 JSON。只有健康 200 response 才能写成 `status=ok`；传输或契约错误必须停止演练并保留原错误证据，不能写 `hits_count=0` 代替。

执行两个固定 smoke：

1. `structured_recall`：official structured pool，至少一个可核验 hit；
2. `primary_evidence`：official primary pool，至少一个可核验 hit。

记录 HTTP 200、服务实际返回的 `collection`、exact `retrieval_stage`、effective `card_types` 和 hit count。structured pool 必须是六类 v2 structured cards，primary pool 必须严格为 `fenjuan|fulltext`；两阶段都必须命中当前 phase 的 `active_collection`。

primary hit 的最终引用仍须另行通过 B4 resolver `status=citable`；这是人工保存的附加 release evidence，不是本演练 JSON 验证器声称完成的检查。正 hit 计数不会自行提升证据等级。

## 5. 切换与 manifest 对账

变更 routing 的具体命令由部署环境所有者执行，不进入验证器或 CI。把 `KB_SEARCH_DEFAULT_COLLECTION`（以及所有明确指定 collection 的下游配置）切到 `local_kb_kaiyuan_v2` 后重启受影响的只读服务。

采集 `after_switch`，并逐字段比较 `/v1/meta` 与 artifact 顶层 `expected_release_manifest`。collection、corpus version、ingest run、source manifest hash 或 schema 任一不一致都必须回滚，不得继续观察期。

运行：

```bash
cd apps/local-kb-unified
python scripts/verify_release_drill.py --input /path/to/release-drill.actual.json
```

退出码：`0` 表示完整演练通过；`1` 表示合法 artifact 中至少一个检查失败；`2` 表示文件、UTF-8、JSON 或 root contract 无效。失败报告不构成健康空结果。

## 6. 回滚触发与执行

以下任一情况立即恢复 `before_switch.active_collection`：health degraded、meta mismatch、任一 smoke 运行错误或零命中、人工 B4 citable evidence 检查回归、protected fingerprint 漂移、未知 collection/schema、或观测缺失。

回滚步骤：

1. 恢复切换前记录的 read routing 和对应 manifest 文件；
2. 重启受影响的只读服务；
3. 不删除 `local_kb_kaiyuan_v2` 或原 collection；
4. 采集 `after_rollback` health/meta/smoke/fingerprints；
5. 重新运行验证器，确认 rollback collection 和 manifest identity 与 `before_switch` 完全一致；
6. 若 protected fingerprint 漂移，作为数据安全事件处理，不尝试由脚本自动修复。

## 7. 证据与完成定义

保存 artifact 并计算 SHA-256：

```bash
sha256sum /path/to/release-drill.actual.json
```

在 `WORK_LOG.md` 记录：release head、PR、实际 stable merge SHA、三条 workflow run ID、验证命令/退出码、artifact SHA-256、操作者、时间、切换前后 collection、manifest identity、回滚原因（如有）和遗留风险。

CI 的 committed synthetic fixture 只证明验证器契约可重复执行，不证明任何生产 collection 已切换或回滚。B6-T03 的代码完成也不授权自动生产变更。
