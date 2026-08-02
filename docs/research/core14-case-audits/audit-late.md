# B10 核心14条专题／后期四案古籍预审（独立审稿后修订）

对象：C24、C44、C45、C47。性质：`AI_PRE_REVIEW_REVISED_AFTER_INDEPENDENT_REVIEW`，不是 Reviewer A/B 人类标注。访问日期均为 **2026-08-01**。

固定载体为 Kanripo `KR3g0018` commit [`eb17a11a6a8a40922ccff01f727e2b5df7f3e734`](https://github.com/kanripo/KR3g0018/tree/eb17a11a6a8a40922ccff01f727e2b5df7f3e734)。所有 carrier string 保留原字形；断句、书名识别、枚举规范化与正文分开，未静默校改。

## 口径先行

本报告严格区分三个作用域：

1. `original_row`：冻结工作簿原行，可能从句中开始、跨标题或止于按语中。
2. `repaired_section`：依据固定载体标题和上下页恢复后的整节。
3. `atomic_rule`：最小可独立说明来源、天象事实与占应的原子。

正式关系枚举只允许 `合｜犯｜入｜守｜掩｜离｜留｜逆`。`暈、珥、穿、貫、出、至、還、舍、抵、干犯、拂、掃、在、凌、鬬` 等均放在 `native_relation_terms`，不得混入正式字段。正式 `special_case_tags` 只允许 `ambiguous｜duplicate｜conflict` 或空；本次仅 C24=`ambiguous`，其余三案为空。

Citation 也分三层：

- `annotation_citation_scalar`：表内 case 级单值建议；C24=`NO`，C44/C45/C47=`YES`。它按 C02 的 pilot 先例表示“本案经边界修复后有可引用原子”，不表示冻结 row 可以整段引用；整行资格始终另读 `whole_row_citation=NO`。
- `whole_row_citation`：冻结原行是否可以作为一个整体引用；四案均=`NO`。
- `atomic citation`：按原子逐条判；修复边界后多可引用，但疑难字串仅可引原字串，不能引未裁决释义。

## 原行结论总表

| Case | Formal | Annotation citation | Whole row | Atomic | Eligibility | Celestial | Formal relation | Complexity | Risk | Computability | Special tags |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C24 | YES | NO | NO | mixed | ambiguous | five_planets, lunar_mansions, cloud_qi | 离, 逆 | cross_passage | high | partially_computable | ambiguous |
| C44 | YES | YES | NO | YES after repair；R4 仅原字串 | eligible | sun, moon, cloud_qi | 入 | compound | medium | partially_computable | — |
| C45 | YES | YES | NO | YES | eligible | guest_star, lunar_mansions | 入, 犯, 守, 掩 | compound | high | partially_computable | — |
| C47 | YES | YES | NO | YES with textual limits | eligible（暂定） | comet, guest_star, lunar_mansions | 犯 | cross_passage | high | partially_computable | — |

这张表只表示 `original_row`。修复节的标签不得反写覆盖原行；尤其 C24 原行仍跨 S8/S9 并保留 `cloud_qi`，C47 原行仍是 `cross_passage/high`。

---

## C24 · 卷38 / 038-13b

主证：[Kanripo 卷038 L214–244](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_038.txt#L214-L244)；对校：[维基文库卷038 oldid 655950](https://zh.wikisource.org/w/index.php?title=唐開元占經_(四庫全書本)/卷038&oldid=655950)。检查范围 12b–14a。

### Original row、S8、S9 必须同时保留

冻结 row 从 `則填星為之動` 起，跨过新标题 `填星穰氣暈彗九`，并收入 `填星珥魚（氣如魚形在填星旁）`、`填星旁有雲如狗狀`、`填星生氣而為黄穰…不出五日`。因此 row-level celestial 必须是：

> `five_planets, lunar_mansions, cloud_qi`

其中 `cloud_qi` 来自 row 内 S9，不可因 S8 修复而删除。原行 Formal=`YES`，因为 S8 有 `離舍／逆行`；whole-row citation=`NO`，因为左截、跨节且 `㑹客環守` 未决；Eligibility=`ambiguous`；Complexity=`cross_passage`；Risk=`high`；Computability=`partially_computable`。

| Scope | 标题/范围 | Celestial | Formal relation | Formal | Citation | Eligibility | Complexity | Risk |
|---|---|---|---|---|---|---|---|---|
| original_row | S8 句中起，跨 S9，止于 S9-R3 句中 | five_planets, lunar_mansions, cloud_qi | 离, 逆 | YES | whole NO / atomic mixed | ambiguous | cross_passage | high |
| C24-S8 | `填星流動與列星鬬八`，R1–R5 | five_planets, lunar_mansions | 离, 逆 | YES | 不整节合引 / mixed | ambiguous（R4） | compound | high |
| C24-S9 | `填星穰氣暈彗九`，R1–R6 | five_planets, cloud_qi | — | 当前 schema 下 NO | 不整节合引 / atomic YES with limits | no_candidate（研究记录保留） | compound | high |

S8 来源全量：`雒書、元命包、晉陽秋（按语内）、春秋緯、鈎命决、石氏、荆州占、郗萌`。S9 来源全量：`洛書、黄帝占、孝經内記、荆州占、巫咸、郗萌`。保留 S8 **雒**／S9 **洛** 的载体字形；`黄帝占` 不径改或径同《黃帝五星占》。

### 完整原子及旧 A–G 覆盖

`row_membership` 仅用 `inside｜left_restoration｜right_restoration`。S9-R3 从 row 内起，其后件由 14a 右补，故另列 segment 层。

| 新 ID | 旧别名 | Membership | 原字串／范围 | 正式 relation | Native terms | 原子 citation |
|---|---|---|---|---|---|---|
| S8-R1 | — | left_restoration | `石氏曰禮德義刑殺盡失則填星為之動` | — | 動 | YES，补齐左界后整原子 |
| S8-R2 | — | inside | `填星動摇離舍使者交接道路` | 离 | 動摇、離舍 | YES；来源写 `continuing attribution under 石氏 (not repeated; confidence medium)` |
| S8-R3 | — | inside | `荆州占曰填星動女主有怒若有怨` | — | 動 | YES |
| S8-R4 | A | inside | `郗萌曰填星變色逆行相凌而鬬㑹客環守其國無道` | 逆 | 變色、逆行、凌、鬬、㑹客環守 | NO，未定串只能作为校勘问题展示；`守` 暂缓进入枚举 |
| S8-R5 | — | inside | `荆州占曰填星與列舍鬬不出其年分亡地死將` | — | 與列舍鬬 | YES |
| S9-R1 | B | inside | `洛書曰黄帝起填星珥魚氣如魚形在填星旁` | — | 珥魚 | YES，仅载体字串与形态层 |
| S9-R2 | C | inside | `黄帝占曰填星旁有雲如狗狀有土功期一月` | — | 旁有雲 | YES |
| S9-R3 | D | inside + right segment | row 内至 `…不出五日`；14a 续 `五榖賤…不出三旬中民多疾病亦死` | — | 生氣、為黄穰 | YES，仅恢复完整后件后的整原子 |
| S9-R4 | E | right_restoration | `荆州占曰填星出穰氣長四丈一曰雨土` | — | 出穰氣 | YES，研究性记录 |
| S9-R5 | F | right_restoration | `巫咸曰填星自暈有土功有䘮` | — | 自暈 | YES，研究性记录 |
| S9-R6 | G | right_restoration | `郗萌曰填星出彗所居下國受兵亡地不出一年` | — | 出彗 | YES，载体字串；`彗` 为形态／类型待决，不先建成另一颗天体 |

旧 A–G 因而全部有唯一映射：A→S8-R4，B→S9-R1，C→S9-R2，D→S9-R3，E→S9-R4，F→S9-R5，G→S9-R6；同时补回旧拆分漏掉的 S8-R1/R2/R3/R5。

### S8-R4 校读与 formal guard

同书结构平行：

- [卷23 oldid 655920](https://zh.wikisource.org/w/index.php?title=唐開元占經_(四庫全書本)/卷023&oldid=655920)：`嵗星變色逆行相凌而鬬舍合留舍環守其國無道`。
- [卷30 oldid 655934](https://zh.wikisource.org/w/index.php?title=唐開元占經_(四庫全書本)/卷030&oldid=655934)：`熒惑變色逆行相凌而鬬㑹舍還其國無道`。
- 卷38：`填星變色逆行相凌而鬬㑹客環守其國無道`。

平行只辅助识别稳定骨架，三条来源标记也不同，不能互称同源异本或据改。正式 C24 relation 只取 `离,逆`；`守` 位于未裁决串中，暂缓。`動、凌、鬬、環` 等均仅 native。

---

## C44 · 卷8 / 008-11b

主证：[Kanripo 卷008 L187–214](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_008.txt#L187-L214)；对校：[维基文库卷008 oldid 655890](https://zh.wikisource.org/w/index.php?title=唐開元占經_(四庫全書本)/卷008&oldid=655890)。冻结 row 左缺第一条甘氏句首，右截第一条《太公隂祕》，故 whole-row citation=`NO`；补边后原子可引，annotation scalar=`YES`。

左补：

> `甘氏曰日暈而珥有雲穿之者天下名士死`

右补：

> `太公隂祕曰日暈有五色雲如杵貫日從外入外人歸勝從内出内人勝欲知姓字白者商赤者徵青者角黒者羽黄者宫`

正式 relation 仅 `入`。`暈、珥、穿、貫、出` 全部保留在 native 字段。Complexity=`compound`，Risk=`medium`，Computability=`partially_computable`，special tags 为空。

| Atom | 来源 | 事实层摘要 | Formal | Citation scope |
|---|---|---|---|---|
| C44-R1 | 甘氏 | 日暈而珥、有雲穿之 | — | YES，左补完整原子 |
| C44-R2 | 髙宗日傍氣圖 | 日暈兩珥、下有黄雲 | — | YES |
| C44-R3 | 甘氏 | 兩珥在外、聚雲在中與外 | — | YES |
| C44-R4 | 春秋感精符 | `有立雲貫日出國多妖孽` | — | YES，**仅无标点原字串** |
| C44-R5 | 洛書摘亡辟 | 日暈兩珥、立雲貫之 | — | YES |
| C44-R6 | 春秋緯 | 日暈兩珥、黄雲貫之 | — | YES |
| C44-R7 | 黄帝兵法 | 日月暈、雲氣從傍入 | 入 | YES |
| C44-R8 | 太公隂祕 | 五色雲如杵貫日、從外入／從内出 | 入 | YES，右补完整原子 |

C44-R4 固定串是 `有立雲貫日出國多妖孽`。至少有两读：

1. `有立雲貫日，出國多妖孽`
2. `有立雲貫日出，國多妖孽`

[识典影印页](https://www.shidianguji.com/zh/book/NGJ892411999012282111706/chapter/1lo8shfrruya1) 支持第二种常见断法；裁决前不把 `出國` 稳定翻成“所见之国”。这限制 R4 的释义引用，不影响其他干净原子作为历史占候规则引用。

---

## C45 · 卷83 / 083-7b

主证：[Kanripo 卷083 L115–141](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_083.txt#L115-L141)；对校：[维基文库卷083 oldid 656040](https://zh.wikisource.org/w/index.php?title=唐開元占經_(四庫全書本)/卷083&oldid=656040)；《後漢書》平行：[卷83 oldid 1458140](https://zh.wikisource.org/w/index.php?title=後漢書/卷83&oldid=1458140)。

冻结 row 在《幽明錄》按语中截断，whole-row citation=`NO`；完整主占辞原子可引，annotation scalar=`YES`。原行 Formal relation=`入,犯,守,掩`；恢复到 8a 下一标题前的 full section 再增加 `留`。原行与修复节都为 `compound`；Risk=`high`；special tags 为空。

### 人物留宿与天象留必须拆开

| 载体串 | 语法主体 | 判定 |
|---|---|---|
| `仍留宿夜與婢臥` | 人 | 人物留宿，排除 celestial `留` |
| `上留遵俱寢` | 人 | 皇帝留严遵共寝，排除 celestial `留` |
| `郄萌曰黑星抵留座星者曰天子惡之` | 黑星 | 真天象 `留`，纳入 repaired full-section relation |

不得因为前两处同形词是假阳性，就误删 8a 的天象 `抵留`。

### 原子与层级

| Atom | 类型／来源 | 载体事实 | Formal relation | Citation scope |
|---|---|---|---|---|
| C45-R1 | 文曜鈎主占辞 | 客星入太微、犯黃帝座 | 入, 犯 | YES，完整主规则 |
| C45-R2 | 文曜鈎续文 | 至座而還 | —（至、還为 native） | YES |
| C45-R3 | 文曜鈎续文 | 守犯三十日已上 | 守, 犯 | YES；30 日是可用持续阈值 |
| C45-R4 | 荆州占 | 客星舍五帝座 | —（舍为 native） | YES |
| C45-R5 | 石氏 | 蒼白星抵座／座旁 | —（抵为 native） | YES |
| C45-H1 | 幽明錄按语 | 客星移掩帝座甚逼，後退 | 掩 | YES，仅作志怪／历史按语；人物 `留宿夜` 排除 |
| C45-H2 | 後漢書按语 | 客星犯天子宿 | 犯 | YES，仅作按语并注明传世异文 |
| C45-R6–R8 | 8a 石氏／荆州占 | 赤／黑／黃白星抵座或座旁 | —（抵为 native） | YES，右补后的各原子 |
| C45-R9 | 8a 郄萌 | 黑星抵留座星 | 留 | YES，右补后的真天象留 |

《占經》按语作 `客星犯天子宿`、`嚴遵`；传世《後漢書·嚴光傳》作 `客星犯御坐甚急`、`嚴光`。只并列异文，不以今本静默覆盖 carrier。

---

## C47 · 卷89 / 089-18a

主证：[Kanripo 卷089 L304–334](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_089.txt#L304-L334)；对校：[维基文库卷089 oldid 656052](https://zh.wikisource.org/w/index.php?title=唐開元占經_(四庫全書本)/卷089&oldid=656052)。

父标题是 `彗孛犯南方七宿`，子标题是 `東井彗孛犯東井`。冻结 row 左带上一子目“參彗孛犯參”的《班固天文志》按语尾，右截《車類秦書》按语，故 original-row Complexity=`cross_passage`、Risk=`high`、whole-row citation=`NO`。修复后的子节才是 `compound/medium`。Formal relation 仅 `犯`（carrier `干犯` 规范映射为枚举 `犯`）；`拂、掃、出、在` 只进 native。annotation scalar=`YES`，special tags 为空。

### 标题、按语和实体层级

- 前一子目按语必须排除；本节止于 `陳卓曰彗在東井…見七十日主當之`，下一标题 `鬼彗孛犯輿鬼` 起即结束。
- 《車類秦書》括注内部再分：天象记录、张益／孟光奏议、苻坚不纳与后验史述，不能平铺成主占辞。
- 对象写作 `客星〔形似彗／或名蚩尤旗〕`：`客星` 是记录标签，`狀如彗` 是形态，`或名蚩尤旗` 是名／类，不是三颗天体。
- 固定载体作 `車類秦書`；`車頻《秦書》` 只作为可能的规范识别名并列，绝不静默改 carrier。

### 原子 citation

| Atom | 来源/层 | 核心字串 | Formal | Citation scope |
|---|---|---|---|---|
| C47-R1 | 黃帝占 | `彗孛干犯東井…大使出野有兩軍相當…` | 犯 | YES |
| C47-R2 | 甘氏 | `彗星干犯東井其國兵起` | 犯 | YES |
| C47-H1 | 車類秦書天象记录 | `客星出尾箕…或名蚩尤旗拂于東井…` | — | YES，仅历史按语观测层 |
| C47-H2 | 张益、孟光奏议 | `彗起尾箕…拂東井…燕首兆亂於秦` | — | YES，仅奏议解释层 |
| C47-R3 | 荆州占 | `彗星干犯東井則大臣謀…` | 犯 | YES，须披露《乙巳占》 `謀／誅` |
| C47-R4 | 石氏 | `彗星出東井…` | — | YES |
| C47-R5 | 郗萌占 | `掃出東井上莖煞漸漸長…` | — | YES，**仅原字串**；不把未决串解释成 “tail grows” |
| C47-R6 | 陳卓 | `彗星出東井民人䜛言…` | — | YES |
| C47-R7 | 陳卓 | `彗在東井…相當之時見七十日…` | — | YES，须披露 `時／無時`；carrier 的 `時` 不删除 |

### 最强规则平行：《乙巳占》卷八

固定版本：[维基文库《乙巳占/8》oldid 2623978](https://zh.wikisource.org/w/index.php?oldid=2623978&title=乙巳占/8)。它与主占辞直接同文，证据优先级高于只平行历史按语的《晋书》。

| 占經卷89 | 乙巳占卷八 | 实质异文 | 处理 |
|---|---|---|---|
| `彗星干犯東井則大臣謀其國用兵期百八十日` | `彗干犯東井則大臣誅其國用兵期百八十日` | `謀／誅` | 保留占經 `謀`，并列异文，不静默改 |
| `彗在東井…見五十日相當之時見七十日主當之` | `彗在井…見五十日相當之見七十日主當之` | `時／無時`，另有 `東井／井` | 保留占經 `時`，并列异文，不静默删 |

外部异文是否触发 terminal `conflict` 取决于整合政策。本预审暂留 C47=`eligible`、special tags 空；如果项目明确规定传世强平行的实质异文必须终结为 conflict，再统一改为 `conflict`，不能自造标签。

### 《晋书》事件平行与 duplicate 撤销

[《晉書》卷113 oldid 2135052](https://zh.wikisource.org/w/index.php?title=晉書/卷113&oldid=2135052) 保存苻坚事件近文：`有彗星出於尾箕，長十餘丈，名蚩尤旗，經太微，掃東井，自夏及秋冬不滅`。与 carrier 有 `客星／彗星、狀如彗而末曲或名／名、拂／掃、自夏及冬／自夏及秋冬、張益孟光／張孟` 等异文；它是历史事件平行，不是同书 duplicate 的自动证据。

fixed-commit 记录查询包括：

> `彗星干犯東井／彗孛干犯東井／彗在東井大人死／彗星出東井民人／大使出野有兩軍相當／車類秦書／苻堅九年／張益孟光／狀如彗而末曲／蚩尤旗拂于東井`

限定结论只能写：

> **截至记录的 fixed-commit 查询，未发现另一条同书/样本实质重复。**

广搜 `蚩尤旗` 虽命中卷85、94、98，但都是类型／云气通论，不是同一苻坚—尾箕—东井事件。此结论不证明记录比较域之外绝无 duplicate；预填 `duplicate` 因当前无同书／样本重出证据而暂撤。

---

## 可计算性与人工门槛

- C24：`逆行、離舍` 在坐标系、宿界与停滞容差固定后可部分计算；颜色、斗凌、云气形态和 `㑹客環守` 不可直接操作化。
- C44：可定义日盘、晕环、云区和时间方向后检测 `入`；`暈、珥、立雲、聚雲、五色、如杵` 仍需版本化阈值。
- C45：`守犯三十日已上` 给出持续时间，但 `犯、抵、掩、守` 都缺空间阈值；颜色与形状需标定。
- C47：30/50/70 日可作为期限字段；`干犯、拂、掃`、历史长度单位、形态与缺测规则仍需外加定义。

四案故都保守标为 `partially_computable`，但这不等于原文提供了现代天文判定阈值。

## 整合建议

1. C24 保留 `original_row + C24-S8 + C24-S9` 三层；原行不得删除 `cloud_qi`，A–G 仅作兼容别名。
2. C44、C45 可按原子整合为 `eligible`；冻结整行仍不得整体引用。
3. C47 可暂撤 `duplicate` 并整合为 `eligible`，同时强制披露《乙巳占》的 `謀／誅、時／無時`；若项目终局政策要求外部实质异文入 `conflict`，再一致调整。
4. 正式 relation 与 special tag 只用项目枚举；所有载体词、层级、边界修复、历史按语和检索限定均放描述字段。

## 验证记录

在修订后的 JSON 上运行 `jq` parse、递归枚举、四案覆盖、C24 atom/alias 覆盖、scope matrix 与原字串 guard 检查，exit code=`0`。逐字输出：

```text
JSON_PARSE_OK
ENUM_CHECK_OK relation=0 special=0
CASE_COVERAGE_OK C24,C44,C45,C47
C24_ATOM_COVERAGE_OK atoms=11 S8=5 S9=6 aliases=A-G
SCOPE_MATRIX_OK whole_row=NOx4 scalar=NO,YES,YES,YES complexity=cross,compound,compound,cross C24_cloud_qi=present
TEXT_GUARD_OK C24/C44/C45/C47 carrier strings and duplicate qualifier preserved
```

再运行逐原子 citation、C24-S9 来源、C45 人物／天象词类、C47《乙巳占》与 duplicate query，以及最终推荐枚举检查，exit code=`0`。逐字输出：

```text
REVIEW_INVARIANTS_OK per_atom_citation=all C24_S9_sources=6 C45_human_vs_celestial=separated C47_yisi_variants=2 duplicate_queries=main+note
FINAL_ENUM_VALUES_OK C24=离,逆/ambiguous C44=入/empty C45=入,犯,守,掩/empty C47=犯/empty
```
