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

设置 API key 环境变量（以下示例只传递变量名，不把 secret 写入命令或 artifact），然后在每个操作者控制的阶段执行只读采集：

```bash
export KB_SEARCH_API_KEY='<由部署环境提供>'

make capture-release-observation PHASE=before_switch ACTIVE_COLLECTION="$BEFORE_COLLECTION" QUERY='熒惑守心' BASE_URL="$KB_BASE_URL" QDRANT_URL="$QDRANT_URL" API_KEY_ENV=KB_SEARCH_API_KEY OUT="$ARTIFACT_DIR/before_switch.json"

# 由部署环境所有者切换 read routing；采集器不会执行或授权切换。
make capture-release-observation PHASE=after_switch ACTIVE_COLLECTION=local_kb_kaiyuan_v2 QUERY='熒惑守心' BASE_URL="$KB_BASE_URL" QDRANT_URL="$QDRANT_URL" API_KEY_ENV=KB_SEARCH_API_KEY OUT="$ARTIFACT_DIR/after_switch.json"

# 如触发回滚，由部署环境所有者恢复 read routing 后再采集。
make capture-release-observation PHASE=after_rollback ACTIVE_COLLECTION="$BEFORE_COLLECTION" QUERY='熒惑守心' BASE_URL="$KB_BASE_URL" QDRANT_URL="$QDRANT_URL" API_KEY_ENV=KB_SEARCH_API_KEY OUT="$ARTIFACT_DIR/after_rollback.json"
```

每条命令只读取 KB Search health/meta/retrieve 与 Qdrant collection metadata/count。输出路径必须由调用者指定且不得已存在；任何认证、超时、传输、契约、collection、解析或写入错误都会失败退出，不生成部分 artifact，也不会转成零命中。

三个文件分别提供 `phase` 对象。操作者将其放入实际 `kaiyuan-release-drill-input/v1` root 的同名字段，并从已批准的 release manifest 填写 `expected_release_manifest`、事件编号及时间窗口；`phase_name` 只用于防止文件混淆，不进入阶段验证。验证器输出的 `kaiyuan-release-drill/v1` 是报告 schema，不可用作输入。组装不会切流、回滚、ingest 或改变任何 collection，完成后仍须运行第 5 节验证器。

推荐使用离线 assembler 代替人工复制。三次采集完成且已取得本次发布的批准 manifest 后运行：

```bash
make assemble-release-artifact \
  BEFORE_SWITCH="$ARTIFACT_DIR/before_switch.json" \
  AFTER_SWITCH="$ARTIFACT_DIR/after_switch.json" \
  AFTER_ROLLBACK="$ARTIFACT_DIR/after_rollback.json" \
  EXPECTED_MANIFEST="$APPROVED_MANIFEST" \
  OUT="$ARTIFACT_DIR/release-drill.actual.json"

python apps/local-kb-unified/scripts/verify_release_drill.py \
  --input "$ARTIFACT_DIR/release-drill.actual.json"
sha256sum "$ARTIFACT_DIR/release-drill.actual.json"
```

assembler 严格绑定三份 `phase_name`、要求 UTC 采集时间依次递增、只投影 manifest identity，并在创建输出前调用现有 B6 validator。输入/验证/输出错误不会创建或覆盖 artifact。该命令不联网、不切流、不执行回滚或 ingest，也不授权任何 collection 写入。

验证通过后，可将本次证据封装为可搬运、可离线复验的 deterministic ZIP。`RELEASE_HEAD` 必须是实际 40 位小写 Git SHA，`CREATED_AT` 必须是操作者记录的 canonical UTC `...Z` 时间；工具不会从 checkout 或本机路径猜测 provenance。

```bash
make create-release-evidence-bundle \
  BEFORE_SWITCH="$ARTIFACT_DIR/before_switch.json" \
  AFTER_SWITCH="$ARTIFACT_DIR/after_switch.json" \
  AFTER_ROLLBACK="$ARTIFACT_DIR/after_rollback.json" \
  EXPECTED_MANIFEST="$APPROVED_MANIFEST" \
  ASSEMBLED_INPUT="$ARTIFACT_DIR/release-drill.actual.json" \
  RELEASE_HEAD="<40-lowercase-git-sha>" \
  CREATED_AT="2026-07-18T12:15:00Z" \
  OUT="$ARTIFACT_DIR/release-evidence.zip"

make verify-release-evidence-bundle \
  BUNDLE="$ARTIFACT_DIR/release-evidence.zip"
sha256sum "$ARTIFACT_DIR/release-evidence.zip"
```

创建命令会重新组装 observation、对比 supplied drill input，并重跑 B6 validator；输出已存在时退出 `2` 且不覆盖。离线 verifier 不解压，会校验精确 member inventory、固定 ZIP metadata、size/hash，再重跑 B7-T02 assembly 和 B6 validator；篡改或语义不一致退出 `1`。

证据包通过不授权切流、回滚、ingest 或 collection 写入。创建和验证都不联网、不读取 Qdrant，也不访问或修改 `local_kb_default`。

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
