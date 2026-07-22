# B9-PR-A 启动与执行记录

## 2026-07-22 — task started

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Verified stable HEAD before branch: d63bfd458764bf7999ff20b4c367f53c0b4f31fe
Feature branch: codex/kaiyuan-b9-contract-registry-v1
Task: B9-PR-A Contract registry and compatibility
State: IN_PROGRESS
```

## 实时仓库核验

- stable 与 `d63bfd...` identical；
- 开放 PR 只有旧路线 #1、#7；
- 没有现存 B9 实现 PR；
- B9-PR-A 已获用户明确授权；
- B9-PR-B 及以后任务保持 `BACKLOG`。

## 稳定分支治理事件

建立分支前曾误用 contents API，在 stable 直接新增临时 `README.tmp`。发现后立即停止实现并删除该文件。比较 `cd630c44...` 到修复后 stable 显示净文件差异为空，但 stable 历史新增了两个直接提交。后续不改写历史，不隐藏事件；所有实现只能在 feature branch 通过 PR 合入。

## 固定范围

本 PR 只实现：

1. `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1` 严格 Pydantic 契约；
2. 三份 JSON Schema 和一个 schema registry；
3. canonical JSON bytes；
4. claim/source reference、UTC、有限数、稳定 ID 和跨对象引用验证；
5. v1 兼容检查；
6. fixtures、focused tests、property smoke 和 CI 门禁。

明确不实现 Skyfield、星官目录、检索、规则适配器、编辑脚本、Stellarium、FFmpeg 或媒体。

## TDD 顺序

```text
提交测试和 fixture scaffolding
→ 在生产模块不存在时观察 RED
→ 实现最小契约层
→ focused GREEN
→ 增加兼容、负向和 property smoke
→ related regression
→ review / exact-head CI
```

## 测试环境说明

当前执行容器不能通过 `git clone` 解析 GitHub 域名，因此：

- 远端文件和分支操作使用 GitHub contents API；
- focused RED/GREEN 在本地构造的最小工作区运行；
- 完整仓库 regression 与 Python 3.12 环境以 GitHub Actions exact-head 结果为权威；
- 不因本地环境缺少依赖而降低断言或跳过 CI。
