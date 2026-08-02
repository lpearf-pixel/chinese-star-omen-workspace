# 对 `audit_early.md/json` 的独立交叉审阅

审阅对象：C02、C03、C09、C11、C13。未修改原报告、源工作簿或 GitHub。

结论：**当前版本不可直接进入整合**。版本身份、定位和边界研究总体可靠，但有 2 项 Critical 输出契约问题和 5 项 Important 语义/资格问题。修正后可整合，无需重做全部古籍取证。

## Critical

### CR-1｜4 条 recommendation.relation 违反既定八值枚举

证据：本项目分层表规定 Relation 只能从 `合 | 犯 | 入 | 守 | 掩 | 离 | 留 | 逆` 选择（`downloads/古星占研究/B10-pilot-core14-human-stratification.md`）。当前 JSON 却将原生词直接写入顶层枚举：

- C03：`乘、貫、蝕、吞` 非枚举值；
- C09：`同舎` 非枚举值；
- C11：`同舎、隨、接` 非枚举值；
- C13：`鈎己、還居、乘` 非枚举值。

这些词应继续保存在 `atomic_rules[].relation_native` 或说明字段，但 recommendation 的 schema 字段必须规范化。建议：

| Case | recommendation.relation 建议 | 另行登记 |
|---|---|---|
| C02 | `入` | “乘”为算法操作，不是天象关系 |
| C03 | `逆, 犯`；若 passage 标签包含史例再加 `掩` | `乘/貫/蝕/吞` 存 native relation |
| C09 | `合, 离, 守, 逆`；`犯`仅 historical_note | `同舎` 存 native relation |
| C11 | `合, 离, 入`；`掩`仅 historical_note | `同舎/隨/接` 存 native relation |
| C13 | `入, 留, 犯, 合, 逆, 守` | `鈎己/還居/乘` 存 native relation |

若整合器严格验证枚举，当前 JSON 会直接失败，因此为 Critical。

### CR-2｜五条 special_tags 均混入未授权标签

既定 `special_case_tags` 只允许 `ambiguous | duplicate | conflict` 或空。当前报告使用 `algorithmic、boundary_fragment、historical_note、ancient_units、source_parallel、same_book_parallel、color_shape、shape_omen、transmitted_parallel` 等大量非枚举值。

建议把它们迁往独立字段，例如 `evidence_features`、`boundary_status`、`phenomenology_notes`；顶层 `special_tags` 只保留合法值。按本次审阅：C02/C09/C11 可为空；C03、C13可在具体疑难原子规则上标 `ambiguous`，但不宜自动标 case 级 `conflict`（见 IM-2、IM-3）。

## Important

### IM-1｜Citation eligible 必须改成显式双字段，C03 尤其不能只给一个 YES

报告在叙述层已经写清“五条整段 NO、局部部分 YES”，这个研究判断是合理的；问题在 JSON recommendation 仍只有：

```json
"citation_eligible": "YES",
"citation_scope": "……局部；整段NO"
```

这会让只读取布尔字段的下游把残段误当作整段可引。C03 左端“法令散”属于跨页句尾，右端又进入下一主体“熒惑入月中”；其原 passage 显然不能整段引用（[卷12固定提交 L87–98](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_012.txt#L87-L98)）。

建议五条统一为：

```json
"citation_eligible_whole": "NO",
"citation_eligible_atomic": "YES"
```

并在每个 atom 继续保留 `citation_eligible_current/expanded`。若必须兼容旧单字段，应明确它是 atomic 聚合值，用户界面必须显示“整段 NO / 局部 YES”，不能只显示 YES。C03-B 的“一年二年乘之”句读未定、C03-G“邦主無”疑脱，应分别维持 atom-level NO 或 needs_review；不能用 case 级局部 YES 覆盖。

### IM-2｜C03 的 conflict 判定缺少“互斥”证据

报告把饥、主死、流民、战争、国亡、相食等多来源占应称为“冲突”。这些结果可以并存，且《开元占经》本来就是按来源并列异占；来源不同或占应多样不自动构成逻辑冲突。真正的问题是两处语义不确定：“一年二年乗之”和“邦主無”。

《史记·天官书》“月蝕歲星，其宿地飢若亡”确能直接支持 C03-E；《晋书》“奄/掩”支持史例字词变体。它们没有否定其他来源。建议：

- case Eligibility 改为 `eligible`（只发布 E/F/H 等完整原子句）；
- C03-B、G atom 标 `ambiguous` 或 `citation_eligible=NO`；
- 仅当项目明确规定“同一前件的任何不同占应都算 conflict”时才保留 conflict，并应把该政策写明。当前报告没有此政策证据。

### IM-3｜C13 的“失火/失地”是传世平行异文，不足以让整个 case=conflict

《开元占经》固定本明载“熒惑逆行氐失火，一曰守氐多火災”（[卷31 L142–152](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_031.txt#L142-L152)）；《乙巳占》卷五作“火逆行氐，失地，一曰多火災”。这是两个载体的实质异文，值得登记，但《乙巳占》并不是《开元占经》同一载体的另一校本，不能反向使《开元占经》当前字句失去引用资格。

建议：

- 保留两条版本化读法，不静默改“失火”为“失地”；
- C13-E1 的 source 固定为《开元占经》内引巫咸，citation 可为 YES；
- 平行读法另列 `parallel_variant`；
- case Eligibility 改为 `eligible`，最多对 E1/E-PAR 标 `ambiguous/source_divergence`（后者不放进三值 special_tags）。

只有在项目将“传世平行文的不同结果”定义为 conflict 时，才可保留原结论；当前报告的依据更像校勘异文而非逻辑冲突。

### IM-4｜C03/C09 的 celestial 标签混合了主体、占应与历史上下文

- C03 的 `lunar_mansions` 只来自历史按语“月掩歲星在參”，不是核心占辞对象。核心为 `moon, five_planets, eclipse`；若保留，应标 `context_only/historical_note`。
- C09 的 `sun` 来自“歲星與填星合於張者則太陽晝”，在句法上是合之后的天象型占应，不是观测前件；应标 `outcome_only`。
- C09 的 `cloud_qi` 来自“又曰井泉髙而平原出雲”，其主语和与两星相合的依存关系都不明确。报告自身在 B atom 写 `subject=null`，却仍把 cloud_qi 当主标签，证据不足。应降为 `context_or_outcome`，不要作为主候选的 antecedent celestial。
- C09 的 `lunar_mansions` 因核心条件“合於張”而成立；C11 的斗、東井、天津和 C13 的氐也都是核心客体，标签成立。

建议主标签：C03=`moon,five_planets,eclipse`；C09=`five_planets,lunar_mansions`。在额外 `celestial_roles` 中分别记录 C03 `lunar_mansions:historical_note`、C09 `sun:outcome_only`、`cloud_qi:context_or_outcome`。

### IM-5｜JSON 把人名改造成不存在或未证实的书名

原文是“郗萌曰”“陳卓曰”“韓楊曰”“巫咸曰”，但 JSON ancient_books 写成《郗萌占》《陳卓占》《韓楊占》《巫咸占》。除非有独立书目证据，不能凭“某人曰”造出书名。

受影响：C09、C11、C13。建议实体结构：

```json
{"name":"郗萌","entity_type":"person","role":"quoted_author"}
```

《荆州占》《黄帝占》《天官书》《晋阳秋》《乙巳占》才作为 book/text。C11 首条“又曰”承前《荆州占》的判断可保留为“高概率承前”，但应在 attribution confidence 中表达，不能靠把人名统一改成“某某占”解决。

## Minor

### MI-1｜C09/C11 边界风险没有遗漏，但 Complexity 口径需要统一

两报告均已准确发现边界：

- C09 左端为《宋书》按语尾，右端“至百”须续 5a“九十二日……”（[卷20 L67–82](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_020.txt#L67-L82)）；
- C11 左端“白合同舍”与右端“三十日舍”均残，分别须补 4a/5a（[卷21 L67–80](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_021.txt#L67-L80)）。

因此不是“遗漏边界风险”。但二者仍标 `Complexity=compound`，而 C02 因跨小节/跨页标 `cross_passage`。若 cross_passage 指提取窗口跨越语义/页界，C09/C11（以及C03/C13）也应改；若它只指跨小节标题，则 compound 可保留。整合前须写清 rubric，不能同一边界形态两种处理。

### MI-2｜Wikisource oldid 数字正确，但 JSON 中未编码中文 query URL 实测返回 HTTP 400

经 MediaWiki API核对：卷012=655898、020=655914、021=655916、031=2506688、104=772441；commit `eb17a11a…e734` 与定位页标均正确。问题仅是 JSON 里的 oldid URL 使用未百分号编码的中文 query。直接请求会返回 400；Markdown 渲染器可能代为编码，但结构化消费者未必。

建议改成 percent-encoded 永久链接，例如卷012：

`https://zh.wikisource.org/w/index.php?title=%E5%94%90%E9%96%8B%E5%85%83%E5%8D%A0%E7%B6%93_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B7012&oldid=655898`

## Approved

### AP-1｜版本身份、commit 与 locator 全部通过

| Case | oldid/API核对 | Kanripo 页标 |
|---|---|---|
| C02 | 卷104 `772441`，2016-10-25 | `KR3g0018_WYG_104-16a` |
| C03 | 卷012 `655898`，2016-10-15 | `KR3g0018_WYG_012-5b` |
| C09 | 卷020 `655914`，2016-10-15 | `KR3g0018_WYG_020-4b` |
| C11 | 卷021 `655916`，2016-10-15 | `KR3g0018_WYG_021-4b` |
| C13 | 卷031 `2506688`，2024-12-18，确为较新修订 | `KR3g0018_WYG_031-8b` |

固定 commit 与五个行号区间均能覆盖目标及相邻页。

### AP-2｜C02 从 computable 降为 partially_computable 正确

16a 算式本身清楚，但“蝕行法”依赖 15b 的间量/半位定义和配图、方数；“推日蝕法”又在 16b 才完句（[卷104 L255–286](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_104.txt#L255-L286)）。因此不能称当前 passage 可独立运行。`partially_computable + medium risk` 是审慎结论。Celestial=`sun,moon,eclipse` 合适；括注里的太白不应加入 five_planets。

### AP-3｜五条边界恢复总体可靠

C02三小节和右端续页、C03左右主体转换、C09历史按语尾与192日续句、C11双端残句、C13“入天门至氐前”和“于野”续句均与固定文本吻合。整段均应 NO，拆出的完整出处句才可局部 YES。

### AP-4｜平行文选择总体可靠

- C03《史记·天官书》直接支持“月蝕歲星，其宿地飢若亡”；《晋书》支持奄/掩史例。
- C09《史记》土木合公式及《乙巳占》近似占应可作为传世平行，且报告没有用七寸静默替换三尺。
- C11卷34确实把“糴貴/道上多死人”合并成无署名一条（[卷34 L24–35](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_034.txt#L24-L35)），报告正确提醒不得据此抹去卷21来源边界。
- C13《乙巳占》失地/多火灾是真实平行差，但其语义等级需按 IM-3 调整。
- CText 没有被当作独立异本，处理正确。

### AP-5｜原子规则主体—关系—占应的主干大体可用

C02 A–D、C03 E/F/H、C09 A/D/E/F、C11 B–G、C13 B–F 是可继续整合的骨架。需剔除或降级：C03-B/G（句读/脱文未决）、C09-B/C（主体为空且可能仅是上下文/占应），并按 CR-1 把 native relation 与 schema relation 分栏。

## 建议的整合门禁

1. 先修 CR-1、CR-2，否则 JSON 不满足枚举契约。
2. 将五条 citation 改为 whole/atomic 双字段；保留 atom 级 current/expanded。
3. C03、C13 不以“多源异占/平行异文”自动判 conflict；若保留，必须提供项目级 conflict 定义。
4. 主 celestial 与 outcome/context/historical_note 分角色；尤其修 C03、C09。
5. 人名与书名分实体类型。
6. 明确 cross_passage 的判定 rubric 后再统一 Complexity。

完成上述 1–5 后，可进入整合；第 6 项可作为整合前统一清洗处理。

## 问题计数

- Critical：2
- Important：5
- Minor：2
- Approved：5

