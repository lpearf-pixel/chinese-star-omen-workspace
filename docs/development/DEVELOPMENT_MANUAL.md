# 《开元占经》Workspace 开发手册

本手册是 `chinese-star-omen-workspace` 的长期开发约束。任何开发者、Codex 会话、自动化代理或维护脚本在修改仓库前都必须先阅读本手册，并继续阅读 `TASKS.md`、`DECISIONS.md`、相关设计与实施计划。

## 1. 项目目标与边界

本仓库用于构建可追溯的中国古代星占研究系统，当前稳定发布线为《开元占经》v2。系统必须区分原始古籍、结构化知识、候选证据、正式证据、规则判断和研究结论。

目录职责：

```text
apps/local-kb-unified
  正式知识库、语料解析、embedding、Qdrant、检索 API、candidate validate/promote

apps/star-omen
  查询、filesystem fallback、candidate 生成、candidate sync、证据解析、规则引擎、研究报告

packages/kb-contracts
  上下游共享 schema、状态、错误码、manifest 与稳定 ID

packages/kb-text-core
  原文解析、页码/卷次/标题、规范化、offset 映射、匹配、锚点、passage 与排序

corpus/kaiyuan_zhanjing
  语料基线、来源说明、定点比对记录与审计配置
```

## 2. 分支与发布政策

- `main` 保留为历史 workspace 主分支，不接收《开元占经》v2 发布。
- `stable/kaiyuan-v2` 是 v2 稳定发布基线。
- 所有功能从 `stable/kaiyuan-v2` 建立 `codex/*` 或其他 feature branch。
- 功能通过 PR 合入 `stable/kaiyuan-v2`，不得直接 push 稳定分支。
- 普通任务 PR 以适用的本地门禁为主要验证依据；不得为每个提交或
  PR head 调度、重试或等待远端/self-hosted Runner。
- 不得把 v2 release PR 的 base 改为 `main`。
- `dev-test` 仅作为历史集成参考，不是 v2 release target。

推荐分支命名：

```text
codex/kaiyuan-<topic>-v2
fix/kaiyuan-<topic>-v2
docs/kaiyuan-<topic>-v2
```

## 3. 开发前强制阅读顺序

每次开始或恢复开发时，按顺序阅读：

1. 根目录 `AGENTS.md`
2. 根目录 `agent.md`
3. 根目录 `summary.md`
4. `docs/development/PROJECT_MEMORY.md`
5. 实时核验远端 stable HEAD 与全部开放 PR
6. 本手册
7. `docs/development/TASKS.md`
8. `docs/development/DECISIONS.md`
9. 当前主题设计文档 `docs/superpowers/specs/...`
10. 当前主题实施计划 `docs/superpowers/plans/...`
11. `docs/development/WORK_LOG.md` 中最新相关记录

若当前任务未在 `TASKS.md` 中登记，不得开始写代码。聊天、PR 评论和临时笔记不能代替任务台账。

## 4. 任务生命周期

允许状态：

```text
BACKLOG    已记录，尚未排期
READY      需求和验收条件明确，可开始
IN_PROGRESS 正在实现
BLOCKED    受外部信息、环境或依赖阻塞
VERIFYING  实现完成，正在运行门禁或 review
DONE       验收证据、CI、提交/PR 均已记录
CANCELLED  明确取消并记录原因
```

流程：

```text
BACKLOG → READY → IN_PROGRESS → VERIFYING → DONE
                         ↘ BLOCKED ↗
```

规则：

- 开发前将任务设为 `IN_PROGRESS`。
- 行为改变必须先添加或更新测试。
- 最终测试前将状态设为 `VERIFYING`。
- 只有在 `WORK_LOG.md` 记录测试命令、CI 结果和提交/PR 后才可设为 `DONE`。
- 范围变化、重要风险和新任务必须立即回写 `TASKS.md`。
- 代码 PR 必须修改 `TASKS.md` 或 `WORK_LOG.md`，治理 CI 会检查。

## 5. 古籍语料政策

### 5.1 不可变原文

- 原始《唐开元占经》文本未经人工校订。
- 不得静默改写原始字节、繁简、异体字、空白结构、`<pb:...>` 页码或 `&KRxxxx;` 字形实体。
- 检索规范化只存在于派生视图，不回写原文件。
- 任何更正必须进入校勘记录或覆盖层，并保留原值、建议值、来源、日期和审核状态。

### 5.2 全文与分卷

- 全文合并版和现有 121 个分卷共同校验。
- 分卷是 primary retrieval 的优先来源；全文用于审计、再生成和 provenance 备用。
- 同一 passage 同时来自分卷和全文时，主结果保留分卷，全文仅作来源链。

### 5.3 CText 使用

公开比对来源：Chinese Text Project Wiki《開元占經》。项目已获用户确认可在本项目范围二次开发。

必须准确表述：

- CText 页面用于人工或定点片段比对。
- 不实现批量抓取、镜像或自动覆盖本地语料。
- CText 文本同样可能未经正式校订。
- 比对结果只产生 `exact_raw`、`exact_normalized`、`mismatch` 等审计记录。
- 发现差异时不得自动修改 immutable raw corpus。

## 6. 文本解析与定位唯一来源

卷次、页码、标题、段落、规范化、offset、anchor、hash 和 primary 排序必须复用 `packages/kb-text-core`。

禁止在上游、下游或脚本中另写不兼容的实现。核心语义：

```text
exact_raw
exact_normalized
loose_window
heading_only
```

只有 `exact_raw` 和 `exact_normalized` 可以成为 exact primary 候选。`loose_window` 和 `heading_only` 只能作为 related/clue。

排序原则：

```text
exact_raw + fenjuan
exact_normalized + fenjuan
exact_raw + fulltext
exact_normalized + fulltext
loose_window + fenjuan
loose_window + fulltext
heading_only
```

所有展示 snippet/excerpt 必须来自命中位置，禁止退回 `text[:N]` 文件头策略。

## 7. 知识库与 Qdrant 安全

- `apps/local-kb-unified` 是正式 KB source of truth。
- 只有上游 ingest 可以写正式 Qdrant。
- 下游不得调用 ingest、不得直接 upsert/delete 正式 collection。
- `local_kb_default` 是受保护的旧 collection：测试和 v2 开发不得删除、重建、迁移或写入。
- v2 使用 `local_kb_kaiyuan_v2`；CI 使用随机临时 collection。
- stale point 删除只能作用于明确带有 v2 `managed_by` 标记的 point。
- 空语料、embedding 失败或 upsert 失败时，不得执行 stale 删除，不得发布成功 manifest。

增量 ingest：

```text
unchanged hash → skip embedding
new passage    → insert
changed passage→ upsert
removed managed passage → delete stale point
```

## 8. 检索契约

三个概念必须分离：

```text
query_mode       用户意图：knowledge/evidence/support
retrieval_stage  检索阶段：structured_recall/primary_evidence/support_context/auto
card_types       本次实际检索池
```

不得根据 `query_mode=evidence` 隐式追加 primary card type 后再与 Stage1 card type 做 AND。

Canonical 字段：

- 写入与 HTTP wire 使用 `kb_book_id`。
- 读取过渡期兼容 `book_id`。
- 同时提供且值冲突时必须返回 contract error。

正式 evidence 查询顺序：

```text
Stage 1 upstream Qdrant structured_recall
Stage 2 upstream Qdrant primary_evidence
仅当官方 primary 成功请求且无结果时，才允许 filesystem fallback
```

错误与健康空结果必须区分：

```text
HTTP 200 + hits=[]             正常无命中
401/403                        authentication_failed
404 COLLECTION_NOT_FOUND       collection_not_found
408/client timeout             timeout
422 contract error             contract_error
429/5xx/connectivity           upstream_unavailable
invalid JSON/shape             invalid_response
```

禁止捕获异常后返回空列表。

## 9. Candidate 工作流

标准流程：

```text
downstream generate candidate
→ upstream validate
→ manual approve/reject
→ upstream promote approved
→ upstream ingest
→ downstream sync status
```

边界：

- 下游只写 `apps/star-omen/data/generated_candidates/`。
- incoming/pending/rejected/stale candidate 不得进入正式 ingest。
- promote 只处理 `review_status=approved`。
- promote 后由上游标记 `source_namespace=official`。
- pending candidate 只能进入 candidate/overlay 结果，不能进入 final exact evidence。

Candidate sync 必须是事务性的：

1. 读取全部 manifest。
2. 检查上游 meta。
3. 校验全部本地 card/source/anchor/hash。
4. 查询正式 extract card。
5. 在内存中规划全部状态。
6. 任一网络或契约错误则不写任何 manifest。
7. 全部成功后原子替换文件。

同步状态只表示业务状态：

```text
pending
merged
needs_review
stale
```

认证、超时、服务和契约错误是 run-level error，不得伪装为业务状态。

## 10. 可引用证据标准

`card_type=fenjuan/fulltext` 只是必要条件，不是充分条件。最终 `citable` 必须验证：

```text
path confined under kb_root
source exists
card_type primary
kb_book_id matches
canonical source_locator matches
page_marker exists and belongs to locator
paragraph_index resolves when supplied
heading_path matches when supplied
anchor_text can be relocated
content/raw/normalized hash matches declared semantics
```

验证状态：

```text
citable
candidate_only
missing_source
source_outside_root
book_mismatch
card_type_mismatch
locator_mismatch
page_mismatch
paragraph_mismatch
heading_mismatch
anchor_mismatch
hash_mismatch
```

规则引擎只有在 resolver 返回 `status=citable` 时才能设置 `primary_evidence_found=true`。

## 11. 测试驱动与调试

### 11.1 行为改变

必须遵循：

```text
写失败测试
→ 确认失败原因正确
→ 最小实现
→ focused test
→ related regression
→ full required gates
```

不得在未观察 RED 的情况下声称测试驱动完成。

### 11.2 Bug 修复

先收集证据并定位根因：

- 复现最小失败；
- 查看完整 traceback、HTTP body、CI artifact；
- 检查最近改动；
- 明确是实现错误、测试过期、契约变化还是环境问题；
- 修复根因，不通过降低断言、吞异常或跳过测试掩盖问题。

### 11.3 禁止做法

- 为让 CI 变绿而删除有效断言；
- 将错误转换为 `[]`、`None`、`unknown` 等成功形态；
- 使用 broad `except Exception: pass`；
- 在多个模块复制同一解析逻辑；
- 未验证就标记 `DONE`；
- 在测试中访问或写入 `local_kb_default`。

## 12. 门禁矩阵

### 12.1 日常开发：本地优先

按改动选择 focused test，并在本地运行全部适用回归：

```text
make contracts-test
make text-core-test
make downstream-test
make upstream-test
```

普通开发、修复、文档、任务级 feature PR 和中间 head：

- 不以 Runner 可用作为开始或继续开发的条件；
- 不在每次提交或 PR 更新后调度、重试或等待 Runner；
- 本地不能运行的门禁必须记录为 `NOT RUN` 或 `BLOCKED`，不得记为通过；
- 可以继续不依赖该远端环境的功能开发。

### 12.2 大版本合并 stable：一次最终统一 Runner

只有当一个大版本的最终候选已完成代码、文档、review 和本地门禁，并
准备合入 `stable/kaiyuan-v2` 时，才对该 exact head 运行一次最终统一
Runner。该统一验证覆盖：

```text
Python 3.9 text-core compatibility
Python 3.12 text-core and downstream
Docker Compose config
secret/machine-path scan
Qdrant incremental reconciliation
Qdrant retrieval contract
candidate roundtrip
CText local spot-check audit
development governance
```

最终 Runner 结果只绑定该 exact head。之后任何代码、测试或状态文档
变化都会使证据过期；大版本合入 stable 前必须在新 head 上重新运行。
Runner 不可用或未完成时，状态只能是 `NOT RUN`/`BLOCKED`，不得把旧
commit 的绿色结果或本地通过写成 Runner 通过，也不得合并该大版本
stable 候选。

### 12.3 独立专项证据

真实设备、Stellarium/FFmpeg、科学复算、语料审核、双人标注、数据库
迁移、安全检查和生产发布等证据继续遵循各任务显式契约。这些证据不能
被 Runner 替代，也不得反过来把 Runner 变成日常开发前置依赖。

`gh` 只是 GitHub 客户端之一，不是项目门禁。已认证 GitHub App 或 API
能提供等价、可审计操作时，应直接使用，不得因本机缺少 `gh` 阻塞工作。

## 13. 文档与决策

- 长期规则放 `DEVELOPMENT_MANUAL.md`。
- 所有任务和状态放 `TASKS.md`。
- 每次开发批次和测试证据放 `WORK_LOG.md`。
- 重要架构与安全选择放 `DECISIONS.md`。
- 主题设计与实施步骤分别放 `docs/superpowers/specs/` 和 `docs/superpowers/plans/`。
- 文档不得保留未解释的 `TODO`、`TBD` 或与实现相矛盾的状态。

## 14. Commit、PR 与完成定义

提交应小而可审计，消息建议：

```text
test: define ...
feat: implement ...
fix: preserve ...
docs: record ...
ci: gate ...
```

PR 必须说明：

- base/head；
- 不触碰 `main` 和 `local_kb_default`；
- 用户可见行为；
- 数据迁移或兼容影响；
- 测试矩阵；
- 已知限制；
- 回滚方式。

任务可标记 `DONE` 的条件：

1. 验收条件全部满足；
2. focused 和 required regression 通过；
3. 验证结果按第 12 节准确记录；若该任务是大版本 stable 合并候选，
   其 exact head 的最终统一 Runner 必须为绿色；
4. `TASKS.md` 和 `WORK_LOG.md` 已更新；
5. 无未解释的安全、语料、兼容或数据风险；
6. PR review 完成并只合入 `stable/kaiyuan-v2`。

本手册持续有效，直到仓库明确记录新的替代决策。
