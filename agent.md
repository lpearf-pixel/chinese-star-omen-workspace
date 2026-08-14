# Chinese Star Omen — 新 Work 全局资料

本文件是跨会话快速接管入口，面向新的 Codex Work、维护者和审查者。
强制规则仍以根目录 `AGENTS.md` 为最高仓库内指令；当前状态以实时 GitHub、
`docs/development/TASKS.md` 和 `docs/development/WORK_LOG.md` 为准。

## 1. 每次开始时必须做什么

按以下顺序读取和核验，不得只相信本文件中的快照：

1. `AGENTS.md`
2. `agent.md`
3. `summary.md`
4. `docs/development/PROJECT_MEMORY.md`
5. 实时读取远端 `stable/kaiyuan-v2` HEAD 和全部开放 PR
6. `docs/development/DEVELOPMENT_MANUAL.md`
7. `docs/development/TASKS.md`
8. `docs/development/DECISIONS.md`
9. 当前任务的设计、计划和 `WORK_LOG.md` 最新记录

开始修改前必须报告：仓库路径、分支、HEAD、工作区是否干净、stable
基线、相关 PR、允许范围、禁止范围、验收标准和验证命令。过期 SHA 只能
作为历史线索，不能作为当前事实。

## 2. 项目定位与目录职责

本仓库构建可追溯的中国古代星占研究系统，当前发布线是《唐开元占经》
Kaiyuan v2。原始古籍、派生结构、候选证据、正式证据、规则判断和研究
结论必须保持分层。

- `apps/local-kb-unified`：正式知识库、解析、embedding、Qdrant、检索 API、
  candidate validate/promote；唯一允许执行 official ingest 的组件。
- `apps/star-omen`：只读检索、filesystem fallback、候选生成、证据/规则/
  天文/星官/视频研究；不得写正式 Qdrant。
- `packages/kb-contracts`：共享 schema、状态、错误码、manifest、稳定 ID。
- `packages/kb-text-core`：卷页标题、原文 offset、anchor、hash、passage、排序
  的唯一实现来源。
- `corpus/kaiyuan_zhanjing`：不可静默改写的原始语料与审计基线。
- `docs/development`：任务、决策、验证证据和跨会话状态。

## 3. 分支、PR 与远端操作

- v2 稳定目标仅为 `stable/kaiyuan-v2`；禁止把 v2 合入或改写 `main`。
- 功能使用 `codex/*`/feature branch，经 Draft PR 交付；不得直接 push stable。
- 普通技术选择、测试失败和可逆修复由代理持续处理，不要默认把本地命令
  转交用户。
- 未经明确授权，不合并 PR、不运行大版本 Runner、不删除分支、不 force
  push、不改 base、不进行不可逆操作。
- 远端 ref 更新只能在已核验父提交的前提下非强制 fast-forward；更新后
  必须读回 PR 的 base/head/draft/merged 状态和树一致性。
- 只有缺失权限/凭据、付费、不可逆操作、必须修改保护分支或重大产品方向
  变化才停下询问。

## 4. 不可突破的资料与证据边界

- `local_kb_default` 禁止写入、删除、重建或迁移；v2 使用
  `local_kb_kaiyuan_v2`，测试使用随机临时 collection。
- 原始语料字节、`<pb:...>`、异体字、空白结构和 `&KRxxxx;` 实体不得静默
  修改；校勘进入可追溯记录/覆盖层。
- CText/Wikisource 等公开源用于定点比对和来源补证，不能未经设计做批量
  镜像或自动覆盖本地原文。
- transport/auth/timeout/contract/collection/parse 错误不得转换为健康空结果。
- candidate、pending、ambiguous、rejected、stale、unverified 都不是正式
  可引用证据。
- 模型只能生成候选、转写或拆分建议，不能代替 Reviewer A/B、批准规则或
  把不确定材料升级为古典结论。
- `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1` 等冻结契约
  不得原地破坏性重解释；语义破坏必须新版本。

## 5. 科学与外部媒体规则

- Stellarium 是固定版本的星官映射/可视化来源之一，不是唯一科学权威。
- 传统星官成员、月宿区域、最近成员距离和古典关系词必须分别建模。
- 单时刻不能证明 `入`、`犯`、`守`、`留`；无阈值/时长/速度证据时保持
  objective measurement 或 `ambiguous_relation`。
- 外部视频只作为研究线索，必须绑定 creator/work ID、固定 URL、UTC 时间、
  captured span 和 SHA-256；无原文/字幕/OCR 时显式 `source_missing`。
- 现代机构材料只能支持其实际陈述。不得把“烈风”自动等同台风、热带气旋
  或海上风暴，也不得把现代气象定义反推为古籍占辞证据。

## 6. 任务与开发流程

新任务必须先进入 `docs/development/TASKS.md`，状态只使用：

```text
BACKLOG → READY → IN_PROGRESS → VERIFYING → DONE
                         ↘ BLOCKED ↗
```

执行顺序：

1. 核验真实仓库和远端状态，保护已有用户改动。
2. 在 TASKS 中登记目标、范围、禁区、验收和交付边界。
3. 行为改变先写失败测试，确认 RED 原因，再做最小实现。
4. 先 focused，再跑与变更规模相符的回归/治理/编译/边界检查。
5. 独立审查发现 Critical/Important 时先复现再修复，不能盲目接受。
6. 最终门禁前标记 `VERIFYING`；把命令、数量、SHA、PR 和遗留风险写入
   `WORK_LOG.md` 后才能标记 `DONE`。
7. 文档证据提交会改变 HEAD，必须在最终文档头上重新运行适用门禁。

## 7. 常用验证命令

从仓库根目录执行；应按任务选择，不要为了小文档变更虚报全量验证：

```bash
.venv/bin/python -m unittest discover -s scripts/tests -p 'test_*.py' -v
.venv/bin/python scripts/check_development_governance.py --base <stable-sha> --head HEAD
make contracts-test
make text-core-test
env -u CODEX_PRIMARY_RUNTIME_PYTHON PATH="$PWD/.venv/bin:$PATH" make downstream-test
make upstream-test
.venv/bin/python -m compileall -q apps/star-omen/src apps/star-omen/tests
git diff --check
git status --short
```

普通 Draft/文档任务不运行 Runner。只有完整大版本候选准备合入 stable，且
代码、文档和审查均冻结后，才为 exact head 运行一次统一 Runner；之后任何
提交都会使该 Runner 证据失效。

## 8. 配置、凭据与隐私

- secrets 只放环境变量或被忽略的本地配置；不得写入仓库、日志、测试
  fixture、PR 正文或交接文档。
- 不输出 raw HTTP error body、私有绝对路径、API key、token、命中原文或
  未授权个人数据。
- 官方语料、Qdrant、数据库/vector 数据和模型文件不得提交。
- 任何 destructive 命令先解析精确目标；禁止 broad path、未解析变量和
  `git reset --hard`/force push 作为常规恢复手段。

## 9. 新 Work 的默认工作方式

- 用户偏好长任务连续自主推进：列出计划后直接执行，常规技术选择采用推荐
  方案，直到实现、测试、审查和交付完成再汇报。
- 小改动运行 focused+适用治理；大版本/稳定集成运行全量门禁。
- 每次阶段结束回写 `TASKS.md`、`WORK_LOG.md`；长期规则更新本文件或
  `AGENTS.md`，不要把临时日志、一次性命令输出和短期实验塞进 `agent.md`。
- 最终报告必须包含：完成内容、变更文件、验证命令/通过数量、独立审查、
  本地/远端 HEAD 与 tree、PR 状态、未运行项和剩余风险。

## 10. 当前状态入口

最新易读快照见 `summary.md`；详细权威历史见：

- `docs/development/PROJECT_MEMORY.md`
- `docs/development/TASKS.md`
- `docs/development/DECISIONS.md`
- `docs/development/WORK_LOG.md`

任何新 Work 都应先实时核验 stable 和开放 PR，再更新这些文件中的过期事实。
