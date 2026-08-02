# Scoped re-review of revised `audit_early`

复审对象：`agent-reports/audit_early.md` 与 `audit_early.json`。范围严格限定为 `review_middle_of_early.md` 原列问题，以及 relation / special / citation / roles / URL / complexity 六类结构自检；未重新展开古籍全文研究，未修改被审报告、工作簿或 GitHub。

结论：**尚不可进入整合**。原 2 项 Critical 输出契约问题已经结构化修复，5 项 Important 中 3 项已解决，但 C03、C13 的 case-level `conflict` 语义仍未按原复审意见处理；C03 又使标量 Citation 与报告自己的聚合政策相冲突。当前计数：**Critical 2 / Important 0 / Minor 0**。

## Critical

### RR-CR1｜C03 的 conflict 与标量 Citation 仍未解决

状态：**NOT ADDRESSED；阻塞整合。**

证据：

- JSON 仍为 `eligibility="conflict"`、`special_tags=["conflict"]`、`citation_eligible="NO"`。
- 同一 recommendation 又把 conflict 定义为“跨来源占应分歧；不表示各占应逻辑互斥”。这恰好承认它不是原复审要求的冲突：饥、主死、流民、战争、败亡可以并存，多来源异占不自动构成逻辑 conflict。
- C03-C/D/E/F/H 均已逐原子标为 `current_passage/YES`；B/G 维持 NO，原子处理正确。因此按报告开头“只要可拆出完整原子句，case-level Citation eligible 可为 YES”的政策，case 标量应为 YES。
- Markdown 又在“统一建议”写“五条均为 YES”，但摘要表和 C03 结论写 C03=NO，形成报告内部矛盾。

建议：C03 改为 `eligibility="eligible"`、`special_tags=[]`、`citation_eligible="YES"`；保留 `citation_eligible_whole="NO"`，并继续让 B/G 为 atom-level NO。若另有 pilot 展示字段必须保留旧 NO，应另命名为独立门禁字段，不能复用 Citation eligible。

### RR-CR2｜C13 仍把传世平行异文提升为 case conflict

状态：**NOT ADDRESSED；阻塞整合。**

证据：

- JSON 仍为 `eligibility="conflict"`、`special_tags=["conflict"]`。
- 修订版已经正确承认《乙巳占》“不是《開元占經》同版校本”，并把 E-PAR 标作 `parallel_only`；这反而确认“失火/失地”“守氐/无守氐”只是版本化平行文差异，不能使《開元占經》当前载体的 E1/E2 失去 case-level eligible 身份。
- E1、E2 与 F 均是当前 passage 完整可引原子；平行文没有否定这些载体句。

建议：C13 改为 `eligibility="eligible"`、`special_tags=[]`；保留 E1/E2 的 carrier reading，把 E-PAR 作为 `parallel_variant` / `parallel_only` 证据，不静默统一“失火/失地”。

## 原问题逐项状态

| 原问题 | 状态 | 复核结论 |
|---|---|---|
| CR-1 recommendation Relation 越出八值枚举 | ADDRESSED | 五案顶层 relation 与所有 `relation_normalized` 均落在 `合/犯/入/守/掩/离/留/逆`；native lexeme 已下沉原子层。 |
| CR-2 Special tags 混入未授权值 | ADDRESSED（结构） | 顶层只剩合法 `conflict` 或空；其他特征迁至 `evidence_features`。C03/C13 的 conflict 语义仍分别由 RR-CR1/2 阻塞。 |
| IM-1 whole / atom Citation 双层输出 | PARTIALLY ADDRESSED | `citation_eligible_whole=NO`、逐原子 scope/eligible 与 ID 映射均已实现；C03 标量与自身聚合政策矛盾，见 RR-CR1。 |
| IM-2 C03 conflict 缺互斥证据 | NOT ADDRESSED | 修订版虽明确“不逻辑互斥”，却仍保留 conflict。 |
| IM-3 C13 平行异文不应使 whole case conflict | NOT ADDRESSED | 已正确分出 `parallel_only`，但 case 仍为 conflict。 |
| IM-4 C03/C09 celestial 角色混层 | ADDRESSED | C03 主标签为 moon/five_planets/eclipse，參为 historical_note；C09 主标签为 five_planets/lunar_mansions，sun 为 outcome_only，cloud_qi 为 context_or_outcome。 |
| IM-5 把人名虚构成“某某占”书名 | ADDRESSED | 未再出现郗萌占、陳卓占、韓楊占、巫咸占；相关实体以 person/authority 建模。 |
| MI-1 Complexity rubric 不统一 | ADDRESSED | 已明确只有跨小节/主题/主体单元才是 cross_passage；C02/C03=cross_passage，C09/C11/C13=compound。 |
| MI-2 Wikisource query URL 未编码 | ADDRESSED | 结构化 evidence URL 已无非 ASCII 中文 query；oldid 数字未改。 |

## 六类附加自检

| 检查 | 结果 | 说明 |
|---|---|---|
| Relation | PASS | recommendation 与原子 normalized relation 均符合八值枚举。 |
| Special | PASS（结构） | 只使用合法三值或空；C03/C13 的语义误用见 Critical。 |
| Citation | PASS（结构）/ FAIL（C03 语义） | 五案 whole 均 NO，原子 ID 与聚合映射一致；C03 case scalar 不一致。 |
| Roles | PASS | C03/C09 outcome/context/history 角色和人名实体均已拆分。 |
| URL | PASS | Wikisource 中文标题已百分号编码。 |
| Complexity | PASS | 五案与书面 rubric 一致。 |

结构自检命令结果：

```text
json=PASS
relation_enum=PASS
special_enum=PASS
citation_structure=PASS
celestial_roles=PASS
person_identity=PASS
url_encoding=PASS
complexity_rubric=PASS
C02  YES  NO  eligible
C03  NO   NO  conflict  conflict
C09  YES  NO  eligible
C11  YES  NO  eligible
C13  YES  NO  conflict  conflict
self_check=7/7 structural groups passed
```

## Integration gate

**不通过。** 仅需修正 RR-CR1 与 RR-CR2，无需重做已通过的关系枚举、角色、URL、边界或 Complexity 工作。两项改为 `eligible` 并清除 case-level conflict 后，可再次做轻量结构复核。

## Controller-policy adjudication

本小节依据控制裁决追加，**覆盖本文此前对 conflict 定义及 C03/C13 terminal 值的判断**。已定 policy 为：`conflict` 包括“跨来源占应分歧”或“会改变规则读法的物质异文”，不要求逻辑互斥；C03 的 Citation 标量按 pilot 人工门禁固定为 NO，C13 固定为 YES，两案 whole 均为 NO。不再评议该政策本身。

### 已由控制裁决消解的两项

- 原 RR-CR1 的 conflict 语义异议：**WITHDRAWN**。C03 确有《河圖帝覽嬉》《荆州占》《天官書》等跨来源占应分歧；`eligibility=conflict`、`special_tags=[conflict]` 符合已定定义。C03 recommendation 的 Citation 标量 NO、whole NO，以及 B/G atom NO、其余若干 atom YES，也符合人工门禁例外。
- 原 RR-CR2：**WITHDRAWN**。C13 的《開元占經》“失火/守氐”与《乙巳占》“失地/无守氐”会改变规则读法，且载体、平行文和 `parallel_only` 已分层；`eligibility=conflict`、case Citation YES、whole NO 符合已定定义。

### 剩余 Critical：Markdown Citation 总则自相矛盾

在控制 policy 下仍有 **1 项 Critical**：`audit_early.md` 的“统一建议”写“Citation eligible 采用 case 至少有一完整原子句的口径，所以五条均为 YES”，与同文件版本口径、总结表、C03 结论、Fix log 及 JSON 明定的 `C03=NO` 相冲突。

这不是政策争议，而是同一交付物中两个不相容的字段说明。结构化 JSON 本身一致，证据引用与原子映射也一致；仅需把该 Markdown 句改为类似：

> Citation eligible 原则上以完整原子聚合；按 pilot 人工门禁例外，C03 case 标量为 NO，其余四条为 YES。五条 whole 均为 NO，atom 资格另存。

### 控制口径下的最终门禁

- C03 conflict、C13 conflict：PASS。
- C03/C13 证据身份、原子 scope、Citation JSON 字段：PASS。
- 剩余 Critical：**1**（Markdown Citation 总则与控制 policy/JSON 自相矛盾）。
- Integration gate：**仍阻塞，但只需修正这一处 Markdown 说明；无需改 C03/C13 的 terminal conflict 或 Citation 标量。**

## Final gate closure

仅复核前述剩余 Critical。`audit_early.md` 的统一建议现已明确：C02/C09/C11/C13 的 case Citation 为 YES，C03 按 pilot conflict 门禁例外为 NO；这与版本口径、总结表、C03 个案结论、Fix log 及 JSON recommendation 完全一致。

- 剩余 Critical：**0（CLOSED）**。
- C03：`citation_eligible=NO`、`citation_eligible_whole=NO`、`eligibility=conflict`，一致。
- C13：既定 terminal 与 Citation 无需修改。
- Final integration gate：**APPROVED**。
