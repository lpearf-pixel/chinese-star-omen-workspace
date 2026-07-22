# B9-PR-A Contract Registry Closeout

## 2026-07-22 — implementation merged

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Release branch: stable/kaiyuan-v2
Feature branch: codex/kaiyuan-b9-contract-registry-v1
PR: #32
Base before merge: d63bfd458764bf7999ff20b4c367f53c0b4f31fe
Final feature head: 8bc3e4ae97780cd0f9f6f9c935508fd374684c4e
Development Governance: 29889316084 — success
Kaiyuan Stable Core: 29889316073 — success
Kaiyuan Upstream Runtime: 29889316046 — success
Squash merge: 26b4ce14afbc0010357c0fd9bc21bc69aa025f70
```

## 交付

- `AstronomyEvent/v1`、`RuleAssessment/v1`、`VideoPackage/v1` 严格 Pydantic 契约；
- Draft 2020-12 JSON Schema 快照；
- schema registry 与 canonical fixture manifest；
- 三份 canonical valid fixture；
- stable ID、UTC、有限数、推荐状态和同包引用 fail-closed；
- nested `$defs` 的 recursive additive-optional compatibility；
- property smoke、fixture、Pydantic/JSON Schema negative 和 review regressions。

## TDD与审查证据

```text
RED 1: ModuleNotFoundError: src.video_pipeline
RED 2: valid package stable-ID issue + nested enum drift, 2 failed
RED 3: strict coercion/recommendation/visibility/fixture gaps, 11 failed / 1 passed
RED 4: illegal condition-state key produced zero JSON Schema errors
GREEN local focused suite: 26 passed
```

独立差异审查修复了：

1. 负向测试被无关中文ID错误掩盖；
2. 兼容检查未递归 `$defs`；
3. bool/数值字符串被数值字段转换；
4. formal recommendation 可以指向非 matched rule；
5. visible/not_visible 缺少目标/太阳高度；
6. fixture manifest 为空且 registry 未绑定真实 fixture；
7. JSON Schema 未关闭不匹配的 condition-state 键。

最终 PR changed files 仅为26个契约、Schema、fixture、测试和治理文件。没有 Skyfield计算、星官目录、检索、规则适配、语料、candidate、ingest、Qdrant、`local_kb_default`、Stellarium、FFmpeg、媒体或发布改动。

GitHub 返回零 review threads、零 submitted reviews；PR 在 exact-head 三项工作流全部成功后由 Draft 转 Ready，并使用 expected head 执行 squash merge。远端 `stable/kaiyuan-v2` 已核验等于 `26b4ce14...`。

## 治理事件

建立功能分支前曾误用 contents API，直接在 stable 加入临时 `README.tmp`，发现后立即删除。净文件差异为空，但两个直接提交保留在 stable 历史。事件已在 `TASKS.md`、start log和PR正文公开记录，未改写历史。

## 后续边界

B9-PR-B 必须从本 closeout 合入后的新 stable HEAD 建独立分支，只实现科学约定、固定星历provider接口和版本化中国星官目录，不得把检索、RuleAssessment、编辑或媒体提前带入。
