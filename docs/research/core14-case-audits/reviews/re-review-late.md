# B10 后期四案 scoped re-review

复核对象：修订后的 `audit_late.md`、`audit_late.json`；只对照 `review_late.md` 原 Critical/Important，不扩大新研究。

## 结论

**仍不可直接整合。** C24 的作用域、`cloud_qi`、11 atoms、A–G 映射，C44-R4，C45 人物/天象 `留`，以及 C47《乙巳占》异文和限定 duplicate 结论均已实质修复；但还有两项会污染正式整合字段的 Critical。

## Critical

### 1. 单值 `citation_eligible` 仍把 atomic citation 错写回 original row

原审稿要求：四条 frozen row 的 `citation_eligible_whole` 均为 `NO`；若现有整合表只有一个 `Citation eligible` 字段，四条都应填 `NO`，atomic 结论另列。

修订稿虽然新增了三层口径，却仍保留以下机器字段：

| Case | `whole_row_citation` | `atomic_citation` | `recommendation.citation_eligible` |
|---|---|---|---|
| C24 | NO | mixed | NO |
| C44 | NO | YES after repair / R4 string-only | **YES** |
| C45 | NO | YES | **YES** |
| C47 | NO | YES with textual limits | **YES** |

Markdown 总表同样把 C44/C45/C47 的 `Annotation citation` 写为 YES。新增的 policy 又定义 `annotation_citation_scalar` 为 case-level recommendation，但这并未改变原表字段“当前文字能否直接作为引用证据”的既定含义；更没有消除下游继续读取 legacy `recommendation.citation_eligible` 的风险。

**阻塞原因。** C44 原行左右均截，C45 原行止于《幽明录》按语中，C47 原行左跨上一子目且右截《车类秦书》。将 scalar 留作 YES 会使整行在整合时被误判为可直接引用，正是原 Critical 尚未解决的情况。

**必须修改。** C44/C45/C47 的 `recommendation.citation_eligible` 与任何映射到现有工作表单值的 annotation scalar 均改为 `NO`；继续保留 `whole_row_citation=NO` 和逐 atom 的 citation 对象。若希望保留“本案有可引用原子”的聚合信息，应使用不会映射到正式单值的新字段，例如 `has_citable_atoms=true`。

### 2. 修复后的 section 仍有 5 个正式枚举值越界

对 JSON 递归检查 `Formal candidate / Eligibility / Risk / Computability` 后，仍得到：

```text
INVALID cases.0.sections.1.formal_candidate NO_UNDER_CURRENT_RELATION_SCHEMA
INVALID cases.0.sections.1.eligibility schema_extension_or_no_candidate_pending
INVALID cases.0.sections.1.risk medium-high
INVALID cases.0.sections.1.computability mostly_not_computable_with_partial_duration_or_length_fields
INVALID cases.3.repaired_section.eligibility eligible_unless_external_variant_policy_requires_conflict
```

这说明报告末尾的 `ENUM_CHECK_OK relation=0 special=0` 只验证了 relation/special tags，没有覆盖项目同样受限的 Formal、Eligibility、Risk、Computability。当前 JSON 若作为整合输入会失败或产生私有值。

**必须修改。** 建议将说明性判断移到 note，正式字段只放枚举：

- C24-S9：`formal_candidate=NO`；当前 schema 下 `eligibility=no_candidate`（若管理员尚未裁决，可用 `needs_review`，但须与 Formal 约束统一）；`risk` 在 `medium|high` 中单选；`computability` 在 `not_computable|partially_computable` 中单选。按现稿自身“有个别长度/持续字段”的说明，`partially_computable` 更一致。
- C47 repaired section：正式 `eligibility=eligible`；“若终局政策纳入外部实质异文则改 conflict”放入 `eligibility_policy_note`，不能塞进枚举值。

完成后应重新做真正的递归枚举检查，而不只检查 `relation_terms` 与 `special_tags`。

## Important

### 3. C24-S9 的聚合 atomic citation 文案需与六个 atom 状态对齐

C24-S9 section 写 `atomic_citation=mixed`，但 S9-R1…R6 的 `citation.status` 全部是 YES，只是分别带 carrier-string、restored-context 或 taxonomy 限制。该差异不会单独阻塞整合，但会使聚合统计难以解释。

建议二选一：

- section 改为 `YES_WITH_LIMITS`，并保留每个 atom 的 scope；或
- 保持 `mixed`，明确列出哪个 atom 在正式 citation 统计中计 NO，以及原因。

Formal/no-candidate 与 citation 是不同维度；不能仅因 S9 缺正式 relation 就把可核对的 carrier string 计为不可引用，也不能反过来用 citation YES 证明其 Formal 合格。

## 已解决

### C24 original / S8 / S9、cloud_qi 与 11 atoms

- 已建立 `original_row + C24-S8 + C24-S9` 三层；修复节未反写原行。
- original row 已恢复 `five_planets, lunar_mansions, cloud_qi`，Formal=`YES`、whole row=`NO`、Eligibility=`ambiguous`、Complexity=`cross_passage`、Risk=`high`、Computability=`partially_computable`。
- 已有 11 atoms：S8=5、S9=6；旧 A–G 唯一映射完整：A→S8-R4，B–G→S9-R1–R6；补回旧拆分遗漏的 S8-R1/R2/R3/R5。
- S9 六个来源 `洛書、黄帝占、孝經内記、荆州占、巫咸、郗萌` 已齐；`雒／洛` 与《黄帝占》身份 guard 已保留。
- 正式 relation 已回到 C24 original/S8=`离,逆`，`守`因 `㑹客環守` 未决而暂缓；native terms 已分栏。

### C44-R4

已保留无标点 carrier string `有立雲貫日出國多妖孽`，并列两种断句；未再把 `出國` 固定翻成“所见之国”。R4 citation 已限定为原字串，问题解决。

### C45 人物/天象 `留`

已明确排除人物 `仍留宿夜`、`上留遵俱寢`，并在 repaired full section 保留 8a 真天象 `黑星抵留座星` 的正式 `留`；original row relation 不含 `留`，full-section relation 才增加 `留`。问题解决。

### C47《乙巳占》与 duplicate

- 已加入固定 `oldid 2623978` 的《乙巳占》强规则平行，并记录 R3 `謀／誅`、R7 `時／無時`（及 `東井／井`）；未静默据改 carrier。
- R5 已限于原字串，R7 已保留《占经》`時`并披露平行异文。
- duplicate 查询已扩到主占辞与历史按语，结论已限定为“截至记录的 fixed-commit 查询，未发现另一条同书/样本实质重复”，并明确不证明比较域之外绝无 duplicate。暂撤 `duplicate` 的表述现已合格。
- original row=`cross_passage/high` 与 repaired child section=`compound/medium` 已分开。

## 可整合门槛

当前只需完成两项 Critical：

1. 将四条 frozen row 的正式单值 Citation 全部统一为 `NO`，atomic citation 独立保留。
2. 清除上述 5 个 Formal/Eligibility/Risk/Computability 私有值并运行递归枚举验证。

完成后，本次 scoped re-review 不再阻塞 C24/C44/C45/C47 的内容整合；C24 仍按 `ambiguous`，C44/C45 按 `eligible`，C47 按当前政策暂作 `eligible`并保留外部异文说明。

---

## 最终 gate（pilot policy clarification 后复核）

**本节取代前文的临时阻塞结论。最终 gate：PASS／可整合；Critical=0。**

### Citation 三层口径

按已确定的 pilot policy，`annotation_citation_scalar` / legacy `recommendation.citation_eligible` 是 **annotation-case 聚合值**，表示该案存在修复后可引用的 atoms；它不是 frozen whole row 的整行可引值。因此 C44、C45、C47 的 annotation scalar=`YES` 与 `whole_row_citation=NO` 是有意的分层表达，不构成矛盾，也不要求把 annotation scalar 改为 NO。C24 因未决串仍保持 annotation scalar=`NO`、whole row=`NO`。

复核 JSON 与 Markdown 后确认：

- 四案的 `citation_scalar_scope` 都是 `annotation_case; not whole-row quotation`；
- 四案 `whole_row_citation` 全为 `NO`；
- annotation scalar 为 YES 的 C44/C45/C47 均有 `has_citable_atoms=true`，并保留逐 atom citation scope；
- Markdown 的口径说明与原行总表同样明确区分 annotation、whole row 与 atomic citation。

在该固定政策下，没有发现会把 frozen row 误导为整行可引的新增 Critical。前文 Critical 1 因政策澄清而关闭并由本节取代。

### 递归枚举复核

对修订后的 JSON 重新递归检查 Formal、Eligibility、Risk、Computability、relation 与 special tags：

```text
FORMAL_ELIGIBILITY_RISK_COMPUTABILITY_INVALID=0
RELATION_INVALID=0
SPECIAL_INVALID=0
LEGACY_INVALID_VALUES=0
```

前文五个越界值已经全部清除：

- C24-S9 现为 `formal_candidate=NO`、`eligibility=no_candidate`、`risk=high`、`computability=partially_computable`；说明移入 policy note；聚合 atomic citation 已统一为 `YES_WITH_LIMITS`。
- C47 repaired section 现为 `eligibility=eligible`；终局政策可能变更的条件说明已移入 `eligibility_policy_note`。

前文 Critical 2 与 C24-S9 的 Important 聚合问题均已关闭。

### 非阻塞一致性建议

C24 recommendation 没有显式 `has_citable_atoms`，但其 `atomic_citation=mixed` 且包含可引 atoms。若该字段在下游被解释为“所有案例都必须显式布尔”，建议为 C24 补 `has_citable_atoms=true`；否则应在 schema note 中说明该字段仅随 annotation scalar=`YES` 出现。此项不改变 C24 annotation scalar=`NO`，也不阻塞本次整合。

**最终结论：PASS／可整合。旧 gate 的两项 Critical 已关闭；未发现新的内容级或下游误导级 Critical。**
