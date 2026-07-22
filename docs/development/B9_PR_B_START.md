# B9-PR-B Scientific Provider and Asterism Catalog Start

## 2026-07-22 — task started

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Stable branch: stable/kaiyuan-v2
Verified stable HEAD: 8bc8d0c8f91f78e4a4faceb22a037b9c526596c0
Feature branch: codex/kaiyuan-b9-scientific-provider-v1
Task: B9-PR-B Scientific provider and asterism catalog
State: IN_PROGRESS
```

## 实时仓库核验

- stable 与 `8bc8d0c8...` identical；
- 开放 PR 仅旧路线 #1、#7；
- B9-PR-A 已实现并完成 docs-only closeout；
- B9-PR-C 及以后保持 `BACKLOG`。

## 固定范围

本 PR 只实现：

1. 版本化科学约定：UTC/TT/TDB、ICRS/视位置、地心/站心、黄道参考平面、无折射几何高度；
2. 显式本地星历文件边界：文件存在、大小、SHA-256 与逻辑名验证；
3. Skyfield provider：固定时间点的太阳系天体坐标、固定星坐标、角距、月相和站心高度/方位；
4. toolchain manifest：Python、Skyfield、星历、timescale、约定和星官目录版本，不记录绝对路径；
5. 版本化中国星官目录：精确 modern object ID / alias 查找、状态和来源；
6. 科学黄金、变形、离线集成和星官目录测试。

明确不实现 KB 检索、RuleAssessment、古籍规则匹配、编辑脚本、Stellarium 执行、FFmpeg、媒体或发布。

## 固定来源

### 离线星历

- 测试环境使用 `skyfield-data==7.0.0` 提供本地 `de421.bsp` 和 timescale data；
- provider 的运行接口仍要求调用方显式传入星历路径和期望 SHA-256；
- 正常运行和测试禁止隐式网络下载。

### 角宿一

- Stellarium Chinese sky-culture file pinned at commit `3972e97101e4321079279b5e5660b074fafc030a`；
- file: `skycultures/chinese/star_names.zh_CN.fab`；
- file blob SHA: `fe8761576dc6c5cd4a65e3551a81ead6122c895f`；
- exact entry: `65474|_("角宿一") 1`；
- SIMBAD Spica identity: HIP 65474，ICRS J2000 `13 25 11.57937 -11 09 40.7501`。

目录不得根据角距离猜测其他星官。没有唯一、来源充分映射的对象返回 `unresolved`。

## TDD 顺序

```text
提交 missing-module / fail-closed tests
→ 观察 RED
→ 实现 conventions/toolchain/catalog pure layer
→ 实现显式 local ephemeris provider
→ focused GREEN
→ fixed Skyfield examples and metamorphic checks
→ full exact-head CI / independent review
```

## 环境说明

当前执行容器不能稳定通过 git clone / package index下载完整仓库与星历。远端文件和分支操作使用 GitHub API；纯模块 focused RED/GREEN 可在本地最小工作区运行；包含 `skyfield-data` 的完整 Python 3.12 集成和全仓回归以 GitHub Actions exact-head 结果为权威。不得因本地网络限制降低断言。
