# B10 后期四案独立内容审稿

审阅对象：`audit_late.md`、`audit_late.json`，以及 GitHub 分支 `codex/kaiyuan-b10-c24-source-mapping-v1` 上的 `docs/research/B10_C24_SOURCE_COMPARISON.md`（该文件 SHA `58fffef962b8adedd06e8d10aff317153ccd21c4`）。本审稿只读核查，未修改原报告或 GitHub。

核查基线：Kanripo `KR3g0018` 固定 commit `eb17a11a6a8a40922ccff01f727e2b5df7f3e734`；正式 B10 `relation_terms` 仅允许 `合｜犯｜入｜守｜掩｜离｜留｜逆`，`special_case_tags` 仅允许 `ambiguous｜duplicate｜conflict` 或空。以下须严格区分：`original_row`（冻结样本原文）、`repaired_section`（按标题补齐后的整节）、`atomic_rule`（可单独引用的原子句）。

## Critical

### 1. C24 被错误收缩成第八节，因而错误删除 original row 的 `cloud_qi`

**证据。** 冻结 row 从 `則填星為之動` 起，明确跨过标题 `填星穰氣暈彗九`，并收入 `填星珥魚（氣如魚形在填星旁）`、`填星旁有雲如狗狀`、`填星生氣而為黄穰…不出五日`。固定文本见 [卷38 L225–244](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_038.txt#L225-L244)。因此：

- late audit 所说“第八节主体删除 `cloud_qi`”只对 `repaired_section_8` 成立，不能覆盖 `original_row`。
- `original_row.celestial` 应为 `five_planets, lunar_mansions, cloud_qi`；其中 `lunar_mansions` 由 `離舍／列舍` 支持，`cloud_qi` 由第九节 row 内文字支持。
- `original_row.complexity` 必须仍为 `cross_passage`；把边界修复后的第八节标成 `compound` 可以，但必须另设作用域。
- `original_row` 的建议应为 Formal `YES`、Citation whole `NO`、Eligibility `ambiguous`、Risk `high`、Computability `partially_computable`。`逆行`可在坐标系与停滞容差固定后计算，故由 `not_computable` 改为 partial 合理。

**建议。** 整合报告至少建立两个兄弟 section，而不是“保留第八节、排除第九节”：

1. `C24-S8 填星流動與列星鬬八`：恢复标题及 R1–R5；celestial=`five_planets,lunar_mansions`。
2. `C24-S9 填星穰氣暈彗九`：保留 row 内 B、C、D-fragment，并把 14a 的 D-continuation、E、F、G 标为 `restored_right_context`；celestial 至少=`five_planets,cloud_qi`，`彗`在 G 中只作待裁决的形态/类型词，不先平铺成另一颗天体。

冻结 row 仍保留跨节身份与 `cloud_qi`；两个 section 的标签不得反写覆盖 row 标签。

### 2. 分支文档的 C24-A—G 不是完整的“原子拆分”，且与 Formal 口径冲突

**证据。** 分支文档把第八节只留下 C24-A（郗萌歧义句），漏掉同节四个原子：

- `石氏曰禮德義刑殺盡失則填星為之動`
- `填星動摇離舍使者交接道路`
- `荆州占曰填星動女主有怒若有怨`
- `荆州占曰填星與列舍鬬不出其年分亡地死將`

同时 B—G 却扩展到原 row 右界之后的 14a 全节续文。由此，“after splitting into C24-A through C24-G”既不是冻结 row 的穷尽拆分，也不是第八、九两节的清晰层级。

更关键的是，B—G 的 `珥魚／旁有雲／生氣／出穰氣／自暈／出彗` 均没有现行正式 relation 枚举中的词。它们可以保留为研究性形态/云气子记录，但在 schema 不扩展前，不能声称每个都是正式 B10 relation candidate。

**建议。** 改为 `S8-R1…R5` 与 `S9-R1…R6` 两层编号；另设 `row_membership=inside|left_restoration|right_restoration`。Formal `YES` 是 case-level（至少 S8-R2 有 `离`，S8-R4 有 `逆`但文字歧义），不能表述为 B—G 每条均正式合格。

### 3. 四案的正式 relation 与 special tag 均混入越界枚举

late JSON 的 `relation` 使用了 `凌、鬬、暈、珥、穿、貫、出、至、還、舍、抵、干犯、拂、掃、在` 等非 schema 值；`special_tags` 又使用 `boundary_repaired、historical_note、lexical_false_positive_excluded、hierarchical_labels、parallel_not_duplicate` 等非正式值。它们可作为自由文本的 philological descriptors / QA flags，不能进入正式字段。

| Case / scope | 正式 `relation_terms` | 仅叙述、不进枚举 |
|---|---|---|
| C24 original row | `离, 逆`；`守`因在 `㑹客環守` 未定串中暂缓 | 動、凌、鬬、環等 |
| C44 original row / repaired atoms | `入` | 暈、珥、穿、貫、出 |
| C45 original row | `入, 犯, 守, 掩` | 至、還、舍、抵 |
| C45 repaired full section | `入, 犯, 守, 掩, 留` | `留`只来自 8a 真天象 `抵留`；人物留宿不计 |
| C47 | `犯`（`干犯`规范映射为 `犯`） | 拂、掃、出、在 |

正式 `special_case_tags` 建议：C24=`ambiguous`；C44=空；C45=空；C47 在 duplicate 撤销且不把外部异文纳入 terminal conflict 时为空。其余信息移入 notes。若整合规范把《乙巳占》的“謀／誅”异文视为发布冲突，则 C47 应用 `conflict`，而不是自造 `parallel_not_duplicate`。

### 4. Citation eligible 没有区分 frozen row 与原子局部

late summary 给 C44/C45/C47 `Citation eligible=YES`，但理由实际只支持“边界修复后、按原子句引用”。冻结 row 的实际情况是：

| Case | `citation_eligible_whole` | `citation_eligible_atomic` | 依据 |
|---|---:|---:|---|
| C24 | NO | mixed | 跨两节且左截；R4 `㑹客環守` 不可定读；干净局部可引 |
| C44 | NO | YES after repair | 左缺甘氏句首，右截《太公隂祕》 |
| C45 | NO | YES | row 在《幽明錄》按语中截断；主占辞局部完整 |
| C47 | NO | YES | 左带上一子目《班固天文志》按语尾，右截《車類秦書》按语 |

**建议。** 整合时强制保留两个字段。若现有表只能有一个 Citation eligible，按表内定义“当前文字能否直接作为引用证据”，四条 frozen row 都应填 `NO`；在 reviewer note 中另写 `atomic=YES`。不能用修复后的全文结论回填 frozen row 为 YES。

## Important

### 5. C47 漏掉最强的规则平行《乙巳占》，并因此漏报两处关键异文

**证据。** 《乙巳占》卷八“彗孛入列宿占”保存：

- `彗干犯東井，則大臣誅，其國用兵，期百八十日`，对 C47-R3 的 `大臣謀`；这是 `謀／誅` 实质异文。
- `彗在井，大人死。見三十日，兵將當之；見五十日，相當之；見七十日，主當之`，对 C47-R7；该平行没有《占经》载体中突兀的 `時`。

见 [《乙巳占》卷八](https://zh.wikisource.org/zh-hans/乙巳占/8)；固定《占经》文本见 [卷89 L316–333](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_089.txt#L316-L333)。late audit 只列《晋书》事件平行、《三十国春秋辑本》派生本及《太平御览》类型平行，未覆盖与主占辞直接同文的《乙巳占》。

**建议。** 把《乙巳占》置于“外部传世规则平行”层，优先级高于只对应历史按语的《晋书》。R3 记录 `謀／誅`，R7 记录 `時／無時`；在未固定《乙巳占》版本或影像前，不静默据改，但不得再称这两条完全无异文。

### 6. C47 撤销 `duplicate` 的方向可接受，但 late 报告所展示的全书检索不足以支持绝对否定

late audit 展示的查询集中在《車類秦書》历史按语：`車類秦書／苻堅九年／張益孟光／狀如彗而末曲／蚩尤旗拂于東井`。这不足以证明整个 C47 主占辞无实质重复，因为 duplicate 也可能落在黄帝占、甘氏、荆州占、陈卓各规则上。

本次复核补查 `彗星干犯東井／彗孛干犯東井／彗在東井大人死／彗星出東井民人／大使出野有兩軍相當`，固定 commit 的代码索引均只命中卷89；广搜 `蚩尤旗` 命中卷85、94、98，但都是类型/云气通论，不是苻坚—尾箕—东井事件的同条重出。故没有证据支持预填的“全书存在同源副本”。

**裁决。** 可以**暂时撤销** `duplicate`，但表述应是“截至记录的 fixed-commit 查询，未发现另一条同书/样本实质重复”，不能写成已证明全书绝无重复。还须明确 duplicate 的比较域是 B10 inventory、整部《占经》，还是跨书语料；《乙巳占》是强平行/潜在来源关系，不应被误作《占经》内部 duplicate。

### 7. C44-R4 的断句与释义过度确定

固定载体为无标点串 `有立雲貫日出國多妖孽`。late audit 断为 `有立雲貫日，出國多妖孽`，其“出国多妖孽”语义不稳；另一有影印页面支持的常见断法是 `有立雲貫日出，國多妖孽`（见[识典卷八，相关行](https://www.shidianguji.com/zh/book/NGJ892411999012282111706/chapter/1lo8shfrruya1)），CText 又采用不同标点。

**建议。** R4 保留无标点 carrier string，并列至少两种断句；在影像/独立校本裁决前，不把 `出國`翻成“所见之国”。这不妨碍整段作为历史占候材料，但该原子的语义释义应标 ambiguous 或 citation 仅限原字串。

### 8. C24 引书清单不完整，且 R2 的来源层级应重审

第九节完整续文还明确有 `荆州占、巫咸、郗萌`。Markdown 的书目段漏 `荆州占、郗萌`，JSON 的 `ancient_books` 则三者全漏；这与分支文档已经列出的 C24-E/F/G 自相矛盾。

第八节 `石氏曰…填星為之動　填星動摇離舍…　荆州占曰…` 中，R2 位于 `石氏曰` 与下一个显式引书标记之间。JSON 直接写 `source=unattributed continuation` 过强；至少应写 `continuing attribution under 石氏 (not repeated; confidence medium)`，或说明为何切断石氏来源范围。

**建议。** 按 section 建全量来源表：

- S8：`雒書、元命包、晉陽秋（按语内）、春秋緯、鈎命决、石氏、荆州占、郗萌`。
- S9：`洛書、黄帝占、孝經内記、荆州占、巫咸、郗萌`。

保留 `雒／洛` 字形差异；`黄帝占` 不等同《黄帝五星占》。

### 9. C47-R5、R7 仍有校读风险，不能全部当作无疑义原子

- R5 的 `上莖煞漸漸長` 本身语义/断句未决；late translation 直接化为 “tail grows” 属解释性补足。
- R7 的 `…相當之時見七十日…` 中 `時` 突兀；《乙巳占》平行作无 `時`，但尚不能静默删除。

**建议。** R5 标 `textually_uncertain`，只引用原字串；R7 保留《占经》读法并列《乙巳占》异文。C47 case-level Formal 仍为 YES，atomic citation 仍可由 R1/R2/R4/R6 等支撑，但不能宣称 R1–R7 每条都已清洁定读。

### 10. Formal / Eligibility / Risk 必须跟作用域绑定

建议整合矩阵如下：

| Case / scope | Formal | Citation whole / atomic | Eligibility | Complexity | Risk | Computability |
|---|---:|---|---|---|---|---|
| C24 original row | YES | NO / mixed | ambiguous | cross_passage | high | partially_computable |
| C24 S8 repaired | YES | 不整节合引 / mixed | ambiguous（R4）；干净原子可 eligible | compound | high | partially_computable |
| C24 S9 repaired | 当前 relation schema 下不宜单独入正式样本；保留研究记录 | 不整节合引 / mixed | schema extension 或 no_candidate 待管理员定 | compound | medium–high | mostly not，个别长度/持续信息需版本化 |
| C44 original row | YES | NO / YES after repair | eligible after atomic split | compound | medium | partially_computable |
| C45 original row | YES | NO / YES | eligible after atomic split | compound | high | partially_computable |
| C47 original row | YES | NO / YES | eligible（暂撤 duplicate；外部异文另记） | cross_passage | high | partially_computable |
| C47 repaired child section | YES | 不整节合引 / mixed-YES | eligible 或按异文政策标 conflict | compound | medium | partially_computable |

late audit 把 C47 repaired section 仍写 `cross_passage`、Risk=`medium`，又用它回填原 row；这两者应拆开。C47 raw row 的前后跨界与截断使风险至少为 high，修复后的 child section 才可降为 medium。

## Minor

1. 固定 commit 与四个 Kanripo 宽范围链接本身正确；建议在整合报告再给精确标题行：C24 标题约 L225、下一标题 L237；C44 目标句群约 L195–205；C45 标题 L125、末句 L139；C47 父标题约 L316、下一子标题 L333。宽范围可保留作上下文。
2. 四个 Wikisource oldid（卷008 `655890`、卷038 `655950`、卷083 `656040`、卷089 `656052`）在两份 late 文件中前后一致；整合时仍应保留标题+oldid，不以 current page 代替。卷23 `655920`、卷30 `655934` 仅属 C24 内部结构平行。
3. C24 的卷23、30、38 是同书“结构公式平行”，但来源标记并不相同：卷23 明属 `荆州占`，卷38 明属 `郗萌`，卷30 位于 `韓楊曰`之后。可辅助分词，不应称为同源异本或直接据改。
4. `車類秦書` 是固定载体读法，应保留；`車頻《秦書》`只能作为校名/辑本题名并列。late audit 此点正确，但 JSON 中可明确分为 `carrier_reading` 与 `normalized_identification_candidate`。
5. 分支 C24 文档的 Sources 只链 Kanripo commit 根节点；建议整合引用固定文件+行号，便于复核，但不影响版本固定性。

## Approved

1. **版本与大边界。** 四案均固定到同一 Kanripo commit；C44 左补 `甘氏曰日暈而珥有雲穿之者`、右补全首条《太公隂祕》，C45 扩至 8a 下一标题前，C47 排除上一子目《班固天文志》按语并恢复父/子标题，均与固定文本相符。
2. **C45 词类过滤。** `仍留宿夜`、`上留遵俱寢` 都是人物行为，必须排除；8a `郄萌曰黑星抵留座星者曰天子惡之` 是天象语境，正式 full-section relation 可保留 `留`。late audit 的核心判断正确。
3. **C45 实体/层级。** 《幽明录》《后汉书》材料应标历史/志怪按语，`客星移掩帝座`与人物动作不能平铺；书内来源 `文曜鈎、荆州占、石氏、幽明錄、後漢書、郄萌` 的基本身份区分正确。
4. **C47 层级。** `彗孛犯南方七宿`为父标题，`東井彗孛犯東井`为子标题；《車類秦書》按语内部再分天象记录、太史奏议、后验史述，且 `客星〔形似彗／或名蚩尤旗〕`不是三颗天体。此层级分析可直接整合。
5. **Computability。** 四案均以 `partially_computable` 最稳妥：C24 有逆行/离舍，C44 有方向性入晕，C45 有三十日持续阈值，C47 有三十/五十/七十日；但角距、宿界、颜色、形态、缺测规则均需外加版本化定义。

## 是否可整合

**结论：不可原样整合；完成上述 Critical 修正后可有条件整合。** 最低门槛是：

1. C24 同时保留 original row 与 S8/S9 两个 section，恢复 row-level `cloud_qi`，补齐 S8 原子与 S9 来源。
2. 所有正式 relation/special tag 回到项目枚举；描述词移到 notes。
3. 四案拆出 whole-row 与 atomic citation 口径。
4. C47 加入《乙巳占》强平行及 `謀／誅、時／無時` 异文，并把 duplicate 撤销改成“fixed-commit 检索下暂未发现同书/样本重复”的限定结论。

满足这四项后，C44、C45 可整合为 `eligible`；C24 保持 case-level `ambiguous`；C47 可暂作 `eligible`（若项目把外部传世异文纳入 terminal 分类，则改 `conflict`），且四条 frozen row 的 citation whole 均为 `NO`、atomic 局部另判。
