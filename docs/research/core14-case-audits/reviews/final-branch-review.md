# Final branch review — B10 Core14 source audit

审查对象：`lpearf-pixel/chinese-star-omen-workspace`

- Base：`stable/kaiyuan-v2` @ `e111e7a69c421e2c19378c0f556f04b80379132d`
- Head：`codex/kaiyuan-b10-c24-source-mapping-v1` @ `34618bd2a23691b1b41c56f7f4ebc53ed1e44260`
- PR：Draft PR #56，open、mergeable，base/head 正确
- 方式：GitHub connector 只读 fetch/compare；未修改 GitHub、工作簿或审计材料

## 结论

**APPROVED：Critical 0 / Important 0 / Minor 0。**

Core14 主证据包、统一总报告和结构化审计通过核心门禁。首次审查提出的 I1、M1 已在 head `34618bd2` 修复，并经 scoped re-review 关闭；分支可进入后续 VERIFYING/DONE 交付流程。

## Critical

无。

## 已关闭的 Important

### I1｜已有 C24 专项说明与 Core14 终态的 computability 冲突 — ADDRESSED

`docs/research/B10_C24_SOURCE_COMPARISON.md` 在 “Scope and current disposition” 明写 C24 为 `not_computable`；但以下本轮终态均为 `partially_computable`：

- `docs/research/B10_CORE14_SOURCE_AUDIT_REPORT.md` 的 14 案矩阵与阈值说明；
- `corpus/research_sources/b10-core14/audit-late.json` 的 `original_row`、S8、S9 和 recommendation；
- `docs/research/core14-case-audits/audit-late.md` 及最终 late re-review。

后者的理由也一致：C24 的逆行、离舍和“四丈/五日”等部分字段具有潜在可计算性，但缺宿界、速度、形态、单位和缺测规则，所以是 partial，而不是完全不可计算。旧专项说明与最终包共存且未标为 superseded，会让读取单一 C24 文档的人得到相反终态。

Scoped re-review：最新文件已改为 `partially_computable`，并明确只有逆行及显式 duration/length 字段在版本化坐标、单位和容差政策后可能重建；定性 cloud/qi morphology 与占应仍不可计算。该表述与总报告及 late audit 一致，`客環守` 的 ambiguous 裁决未被改变。**CLOSED。**

## 已关闭的 Minor

### M1｜实施计划的 “live state” 已过期 — ADDRESSED

`docs/superpowers/plans/2026-08-01-b10-core14-source-audit.md` 标题下仍写 `Status: IN_PROGRESS`，阶段 1–2 为 `IN_PROGRESS`、3–6 为 `PENDING`；当前 `TASKS.md` 的 B10-R01/R02 已为 `VERIFYING`，总报告也写三组审计与交叉复核完成、Draft PR #56 已建立。

Scoped re-review：计划总状态现为 `VERIFYING`；阶段 0–5 均为 `DONE`，阶段 6 为 `VERIFYING`，与 TASKS 及 Draft PR #56 的实际状态一致。**CLOSED。**

## 已通过的门禁

1. **变更范围。** 相对 stable 共 26 个文件：只涉及 `docs/research`、`docs/superpowers/plans`、`docs/development/TASKS.md` 与 `corpus/research_sources`。没有代码、合同、workflow、KB/Qdrant、`local_kb_default`、Reviewer A/B 或工作簿变更。
2. **分支与 PR。** 分支 ahead 33、behind 0，merge base 等于 stable HEAD；PR #56 为 Draft，目标为 `stable/kaiyuan-v2`，没有指向 `main`。
3. **Core14 覆盖。** 结构化文件恰含 14 个唯一 case：C02、C03、C09、C11、C13、C14、C24、C31、C33、C41、C43、C44、C45、C47。
4. **原子计数。** early 39 + middle 52 + late 39 = **130**；130 个 atomic ID 全部唯一。
5. **统一裁决。** Formal 14/14 YES；annotation scalar 12 YES、C03/C24 NO；whole-row 14/14 NO；Eligibility 为 11 eligible、C03/C13 conflict、C24 ambiguous。
6. **枚举。** 顶层正式 relation 全部限定在 `合｜犯｜入｜守｜掩｜离｜留｜逆`；special tags 全部限定在 `ambiguous｜duplicate｜conflict` 或空。native lexeme 与 outcome/commentary relation 没有混入正式枚举。
7. **Citation 作用域。** whole 与 atomic 已分层。early atoms 有逐条 eligible/scope；middle 52 atoms 全有 scope；late atoms 全有 citation status/scope。修复上下文没有反写为 frozen-row whole YES。
8. **C24 三层与歧义。** `original_row`、C24-S8、C24-S9 三层均保留；5+6=11 atoms；`cloud_qi` 留在 original row；`客環守` 原字保存，`守` 未因未决句读提升为正式 relation；卷23/30仅作同书结构平行。
9. **C47 异文。** 明确保存《乙巳占》`謀／誅`、`時／無時`，以及《晋书》史例差异；`車類秦書` 与 `車頻《秦書》` 分作载体读法/规范识别候选；duplicate 只在固定比较域内暂撤，没有宣称全域无重复。
10. **来源固定。** Wikisource register 有 13 个唯一 oldid，覆盖全部 14 case；Kanripo context 文件有 14 case block、统一固定 commit，42 个页标。Wikisource/Kanripo 明示为同一四库本系统的转录核对，不冒充独立异本。
11. **哈希。** Core14 manifest 中列出的 18 个文件在审查时逐字节 SHA-256 全部匹配；C24 Wikisource 摘录与 Kanripo parallel 文件的 manifest 哈希也匹配。最新总报告 hash 已在 manifest 同步登记。
12. **相关 Wikisource 本地化边界。** `B10_RELATED_WIKISOURCE_LOCALIZATION_PLAN.md` 与 TASKS B10-R03 均为 `PLANNED/BACKLOG`；本 PR 不批量下载。计划包含 P0/P1/P2、oldid、原字、卷页、哈希、manifest、版本身份、citation scope 与失佚书处理，明确不冻结 schema、不 ingest KB。
13. **安全负面门禁。** 新增研究文件未发现 `/workspace`、`/tmp`、`/Users` 或 sandbox 绝对路径。`TASKS.md` 中既有一处 `/Users/...` 是 stable 已存在的历史拒收说明，不是本分支新增路径。
14. **审查轨迹。** 三组 re-review 的最终 gate 均为 Critical=0/PASS；旧 review 的原始阻塞被保留为审计轨迹，并由文件末尾的最终裁决明确取代。

## 最终门禁

**APPROVED。** Scoped re-review 未发现 I1/M1 的残留矛盾；PR #56 仍为 open Draft，base/head 仍分别是 `stable/kaiyuan-v2` 与目标 feature branch。
