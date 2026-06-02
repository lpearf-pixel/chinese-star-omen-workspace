# Local KB Unified

本项目是“本地知识库 + 开发环境一体化”的可执行脚手架，用于快速在本机搭建可持续维护的 RAG 环境。

## 使用目标

- 本地可运行：核心服务可稳定启动并通过健康检查
- 可持续维护：索引、日志、备份和迁移都有文档闭环
- 可迭代优化：先跑通，再逐步做检索质量与评测优化
- 多 Agent 就绪：其它自动化/Agent 可通过 **HTTP 检索/RAG** 集成（Compose 服务 `kb-search`，契约见 `docs/agent-search-api.md`）；整理/批量写入知识库可走 **Cursor Skill** `.cursor/skills/local-knowledge-base/`

## Stack

- OpenWebUI: 统一问答入口
- Ollama: **建议在 macOS 宿主机安装**（Metal），**不在** Compose 中跑 ollama 容器；详见 [`docs/m3max-host-ollama.md`](docs/m3max-host-ollama.md)
- Qdrant: 向量检索
- PostgreSQL: 结构化元数据
- Docker Compose: 服务编排
- KB Search API: 面向多 Agent 的 JSON 检索/RAG（**Docker Compose 服务**，`make up` 即启动），见 `kb-search/README.md` 与 `docs/agent-search-api.md`

## Project Layout

- `docker-compose.yml`: 核心服务编排
- `.env.example`: 环境变量模板
- `Makefile`: 常用命令入口
- `docs/`: 架构、运维、迁移与 FAQ 文档
- `scripts/`: 初始化与健康检查脚本
- `index-jobs/`: 索引任务脚手架
- `kb-search/`: 多 Agent HTTP 检索/RAG（镜像构建上下文 + 可选本地 uvicorn）
- `.cursor/skills/local-knowledge-base/`: Cursor **Agent Skill**（批量整理知识源、`make ingest`、调 KB Search API）
- `scripts/install_cursor_kb_global.sh`: 安装到 **`~/.cursor/skills/` + `~/.cursor/rules/`**，使**任意 Cursor 项目**在启动后都能用同一套知识库规则与 Skill

### Cursor 配置（知识库 Agent，全项目可用）

Cursor 会加载用户目录下的 `~/.cursor/skills` 与 `~/.cursor/rules`。在本仓库执行**一次**：

```bash
make install-cursor-global
```

然后**完全退出并重新打开 Cursor**。之后打开**任意项目**，对话里提到知识库 / ingest / RAG / 整理项目等，Agent 会按全局 Rule 指向本仓库路径与 `~/.cursor/skills/local-knowledge-base/SKILL.md`。

- 卸载：`bash scripts/install_cursor_kb_global.sh -u`
- 若移动了本仓库路径，请重新执行 `make install-cursor-global` 以更新 Rule 中的绝对路径。

**分步图文式说明（在其它项目里怎么用）**：见 [`docs/cursor-other-projects-skill.md`](docs/cursor-other-projects-skill.md)。

## Quick Commands

```bash
# 1) 首次初始化
cp .env.example .env

# 2) macOS：安装并启动宿主机 Ollama（https://ollama.com），再拉模型（走 Metal）
bash scripts/pull_ollama_models.sh

# 3) 启动核心服务（无 ollama 容器；WebUI/kb-search 经 host.docker.internal 连宿主机 11434）
make up

# 4) 健康检查（会 curl 宿主机 11434）
bash scripts/healthcheck.sh
# 或只拉指定 tag：bash scripts/pull_ollama_models.sh gemma4:31b

# 5) 初始化索引任务环境
bash index-jobs/setup_env.sh

# 6) 写入 Qdrant（首次建议 --recreate；知识源见下方说明）
make ingest

# KB Search API 已随步骤 3 的 make up 启动（映射 KB_SEARCH_API_PORT）
# 若只改了 kb-search 代码：make kb-search
# 若需删掉旧容器并无缓存重建 kb-search 后再全栈启动：make rebuild
# kb-search 镜像构建时 pip 很慢：在 .env 设 PIP_INDEX_URL（见 .env.example / docs/runbook.md）
# KB Search 烟测：bash scripts/kb_retrieve_smoke.sh
# 下游查询手册：docs/kb-query-manual.md
# 详见 kb-search/README.md
```

## Quick Start

1. 复制环境变量

```bash
cp .env.example .env
```

2. 安装 [Ollama](https://ollama.com)（macOS 宿主机，Metal），并拉模型：

```bash
bash scripts/pull_ollama_models.sh
```

3. 启动 Docker 服务（不含 Ollama 容器）：

```bash
make up
```

`pull_ollama_models.sh` 会拉取 `.env` 中的 `CHAT_MODEL`、`EMBED_MODEL` 与 **`OLLAMA_EXTRA_MODELS`**。在 OpenWebUI 可选模型；**KB Search RAG** 使用 `.env` 的 `CHAT_MODEL`，修改后需 **`docker compose up -d kb-search`** 或 `make restart`。

4. 健康检查

```bash
bash scripts/healthcheck.sh
```

5. 初始化索引任务环境

```bash
bash index-jobs/setup_env.sh
```

6. 将知识库灌入 Qdrant（**API 检索依赖此步**）

```bash
make ingest
```

- 默认：若存在 `~/KnowledgeBase/sources` 则用该目录；否则用仓库内 `sample-kb/`（含 `notes/`、`docs/`、`code/`）。
- 可通过 `.env` 中 `KB_SOURCES_ROOT` 指定其它路径（相对路径相对仓库根目录）；路径含空格时请用引号。
- **Obsidian 为增量知识源（非唯一）**：设置 `KB_ENABLE_OBSIDIAN_SOURCE=true` 与 `KB_OBSIDIAN_ROOT` 后，在**不替换**上述主源逻辑的前提下合并索引；与主源路径相同时对 `.md` 启用 frontmatter / wiki-link / 标题分节。示例路径：  
  `/Users/kandysmith/Library/Mobile Documents/iCloud~md~obsidian/Documents/pyh/_kb-ingest`  
  详见 `docs/knowledge-sources.md`。

7. KB Search API

- **`make up` 已包含** 服务 `kb-search`（默认 `http://127.0.0.1:8008`）。
- **用法与示例**（`retrieve` / `rag`、curl）：见 **`kb-search/README.md`**。
- **下游查询手册**（请求结构、`filters` / `query_mode`、payload 字段、零命中排障）：**`docs/kb-query-manual.md`**。
- **HTTP 契约**：**`docs/agent-search-api.md`**。
- 修改了 `kb-search/` 代码或 `requirements.txt` 后：**`make kb-search`**（或 `docker compose up -d --build kb-search`）。
- 无 Docker、仅本地调试：`bash scripts/run_kb_search.sh`（仓库根执行）。
- 快速烟测：`bash scripts/kb_retrieve_smoke.sh`；单次探测：`python3 scripts/kb_query_probe.py "你的问题" --literal-first`。

## Ports

- OpenWebUI: `3000`
- Ollama API: `11434`
- Qdrant HTTP: `6333`
- Qdrant gRPC: `6334`
- PostgreSQL: `5432`
- KB Search API：`KB_SEARCH_API_PORT`（默认 `8008`）映射到容器内服务，见 `kb-search/README.md`

## 文档导航（按执行顺序）

### 0) 先看整体规划

- `plan.md`: 分阶段目标、范围、验收标准
- `docs/implementation-checklist.md`: 当前进度与 DoD 对照清单

### 1) 容器启动后继续落地

- `docs/knowledge-sources.md`: **多知识源**（主源 + 可选 Obsidian 增量）
- `docs/kaiyuan-obsidian-metadata-spec.md`: **《唐開元占經》** 分层 frontmatter + 路径推断（`KB_KAIYUAN_METADATA_INFER`）
- `docs/kaiyuan-frontmatter-bootstrap-checklist.md`: 第一批手补勾选表
- `docs/operation-guide-after-containers.md`: 从“容器已启动”到“可问可查”的操作路线
- `docs/index-jobs-spec.md`: 索引任务实现规范（`ingest.py` / `rag_query.py`）
- `docs/data-contract.md`: 索引输入输出与字段约定
- `docs/kb-query-manual.md`: **KB Search 查询手册**（下游集成：`filters`、`query_mode`、响应字段、排障）
- `docs/agent-search-api.md`: **多 Agent / 自动化** 的 HTTP 检索与 RAG 契约

### 2) 稳定运行与排障

- `docs/m3max-host-ollama.md`: **macOS 宿主机 Ollama（Metal）** + Docker 其它服务、容器旧模型说明
- `docs/runbook.md`: 日常启停、巡检、故障处理
- `docs/faq.md`: 常见问题与快速修复
- `docs/log-schema.md`: 日志字段统一规范

### 3) 验收、基线与迁移

- `docs/acceptance-test-cases.md`: 验收测试与调参记录
- `docs/config-baseline.md`: 配置基线与变更对照
- `docs/migration.md`: 新机器迁移步骤

## 建议执行路径

- 新环境：`Quick Start` -> `operation-guide-after-containers` -> `implementation-checklist`
- 日常维护：`runbook` + `faq` + `log-schema`
- 版本迭代：`acceptance-test-cases` + `config-baseline`
- 机器切换：`migration`
- 多 Agent 集成：`kb-query-manual`（上手）→ `agent-search-api`（契约细节）；`make up` 后 Base URL 见 `KB_SEARCH_API_PORT`
# Local-KB-Unified
