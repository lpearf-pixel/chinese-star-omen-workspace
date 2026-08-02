# B10 核心 14 条中期卷组古籍研究预审

范围：C14、C31、C33、C41、C43。性质：AI 古籍研究预审，不是 Reviewer A/B 标注；未改动工作簿。

访问日期统一为 **2026-08-01**。现存载体为唐瞿曇悉達编《唐開元占經》（四库全书文渊阁本系统）；下列“郗萌、石氏、甘氏、陳卓”等和书名均是载体内引文来源，不应与现存载体混同。CText 仅可帮助检索，因与 Wikisource/Kanripo 同出四库文本且另加现代标点，本报告不把它算独立异本。

## 版本身份与通用证据

| 卷 | Wikisource 永久版本 | 修订时间 | Kanripo 固定版本 |
|---|---|---|---|
| 031 | [oldid 2506688](https://zh.wikisource.org/w/index.php?title=%E5%94%90%E9%96%8B%E5%85%83%E5%8D%A0%E7%B6%93_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B7031&oldid=2506688) | 2024-12-18；本组中明显较新的修订 | [031 固定提交行文](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_031.txt#L261-L344)；[raw](https://raw.githubusercontent.com/kanripo/KR3g0018/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_031.txt) |
| 043 | [oldid 772363](https://zh.wikisource.org/w/index.php?title=%E5%94%90%E9%96%8B%E5%85%83%E5%8D%A0%E7%B6%93_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B7043&oldid=772363) | 2016-10-25 | [043 固定提交行文](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_043.txt#L201-L245)；[raw](https://raw.githubusercontent.com/kanripo/KR3g0018/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_043.txt) |
| 045 | [oldid 655964](https://zh.wikisource.org/w/index.php?title=%E5%94%90%E9%96%8B%E5%85%83%E5%8D%A0%E7%B6%93_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B7045&oldid=655964) | 2016-10-15 | [045 固定提交行文](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_045.txt#L122-L168)；[raw](https://raw.githubusercontent.com/kanripo/KR3g0018/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_045.txt) |
| 074 | [oldid 656022](https://zh.wikisource.org/w/index.php?title=%E5%94%90%E9%96%8B%E5%85%83%E5%8D%A0%E7%B6%93_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B7074&oldid=656022) | 2016-10-15 | [074 固定提交行文](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_074.txt#L155-L189)；[raw](https://raw.githubusercontent.com/kanripo/KR3g0018/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_074.txt) |
| 079 | [oldid 656032](https://zh.wikisource.org/w/index.php?title=%E5%94%90%E9%96%8B%E5%85%83%E5%8D%A0%E7%B6%93_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B7079&oldid=656032) | 2016-10-15 | [079 固定提交行文](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_079.txt#L96-L146)；[raw](https://raw.githubusercontent.com/kanripo/KR3g0018/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_079.txt) |

`ancient_books.scope` 统一采用 `current_passage | boundary_repair | wider_context | parallel`：载体与本案原子直接引书为 `current_passage`；用于补齐截断的来源为 `boundary_repair`；相邻但不入原子的来源为 `wider_context`；跨书/跨卷对读为 `parallel`。C43 后续巫咸、《黄帝占》另标 `context_only`。逐书结构化映射见 JSON。

## C14｜卷31 / KR3g0018_WYG_031-18a

### 边界与恢复

- 所属小节：**「熒惑犯心五」**（031-15a 起），下一小节 **「熒惑犯尾六」**（031-19b）。原 passage 横跨 031-18a，并在左右两端截句。
- 左边界：原首“惑守心”应上接 031-17b 末“郗萌曰熒”，恢复为“**郗萌曰熒惑守心……**”。
- 右边界：原末按语“熒惑逆行守心三年”应下接 031-18b“**三月京都饑人相食**”，随后另起“春秋緯説題辭曰……”。
- 最小可引用范围：从“郗萌曰熒惑守心有反者……”至袁宏《漢紀》按语完整结束；若只引用单条，则分别截取郗萌、荆州占、陳卓、玄冥占的完整句，不并入前后按语。

建议断句（保留字形；方括号为释读补足，不改底本）：

> 郗萌曰：「熒惑守心，有反者從太子起；一曰九卿為害；又曰大國兵四起，天子軍破；又曰：[守心]二十日，相死；又曰：守心留十日，后死；又曰：守心三十日，有女䘮。」郗萌曰：「熒惑守心、房間三十日，地動。」又占曰：「熒惑守心，有反者從宗家。」（案宋書天文志曰……）荆州占曰：「熒惑守心，色黒，有兵必敗。」陳卓曰：「熒惑守心，期三十日，彗星出。王都西南指[所指闕]。」𤣥冥占曰：「熒惑守心，為饑。」（案袁宏漢紀曰……三年三月，京都饑，人相食。）

白话：火星停守心宿，被解释为太子、九卿或宗室发动叛乱、战争、死亡、女丧、地震、饥荒等征兆；若呈黑色，则用兵必败。陳卓的一条说，火星守心后三十日将有彗星出现；“王都西南指”的句法或所指有脱漏，暂不强解。

### 层次、来源与关键裁决

- 天象事实：按语中的“晉元康九年……熒惑守心；八月入羽林”和“安帝永初元年……熒惑逆行守心”是史例；可与[《宋書》卷24](https://zh.wikisource.org/wiki/%E5%AE%8B%E6%9B%B8/%E5%8D%B724)、[袁宏《後漢紀》卷16](https://zh.wikisource.org/zh-hant/%E5%BE%8C%E6%BC%A2%E7%B4%80_%28%E5%9B%9B%E5%BA%AB%E5%85%A8%E6%9B%B8%E6%9C%AC%29/%E5%8D%B716)对读。宋书今本作“元康九年二月”，本卷按语作“六月”，存在月分异文；《晉書》系统又作六月，不能静默统一。
- 占应：反乱、兵败、死亡、女丧、地动、饥，以及“彗星出”。
- 历史按语：赵王伦、三王起兵及京都饥荒等，是编者验证材料，不是占辞条件。
- **“彗星出”裁决**：是“熒惑守心，期三十日”之后的预测性占应，不是与“熒惑守心”同层的共时天象。决定性平行文见卷88“彗孛名狀占”：“陳卓占曰熒惑守心期三十日彗星出”，且同列“填星守熒惑……彗星出”等生成公式（[卷88固定提交](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_088.txt#L29-L38)）。因此 celestial 可保留 comet，但必须标作 **outcome_only**；不可把它编码为第二个观测主体。
- 书内引书/人名：郗萌、《荆州占》、陳卓、《玄冥占》；按语引沈约《宋書·天文志》、袁宏《漢紀》。现存载体始终是《唐開元占經》。

### 平行文与校勘

| 底本原字 | 平行文/史书 | 建议 |
|---|---|---|
| “陳卓曰熒惑守心期三十日彗星出王都西南指” | 卷88止于“彗星出” | 以卷88确认“彗星出”为占应；“王都西南指”另列残疑，不补宾语。 |
| 宋书按语“元康九年六月” | 《宋書》卷24作“二月”；《晉書》系统作“六月” | 登记二月/六月异文，不裁改。 |
| “后死” | Wikisource/Kanripo相同 | 保留“后”字；可释为“之后死亡”，也可能读“后死”，语义未决。 |

### 原子规则

| ID | 主体→客体 | 关系/条件 | 占应 | 来源 | Citation scope |
|---|---|---|---|---|---|
| C14-R01 | 熒惑→心 | 守；时长未明 | 反者从太子起 / 九卿为害 / 大国兵起、天子军破 | 郗萌 | expanded_context |
| C14-R02 | 熒惑→心 | 守约20日（省主语） | 相死 | 郗萌 | expanded_context |
| C14-R03 | 熒惑→心 | 守/留10日 | 死（“后死”句法待定） | 郗萌 | expanded_context |
| C14-R04 | 熒惑→心 | 守30日 | 女䘮 | 郗萌 | expanded_context |
| C14-R05 | 熒惑→心、房間 | 守30日 | 地動 | 郗萌 | current_passage |
| C14-R06 | 熒惑→心 | 守 | 反者从宗家 | 又占（承郗萌段） | current_passage |
| C14-R07 | 熒惑→心 | 守；色黒 | 有兵必敗 | 荆州占 | current_passage |
| C14-R08 | 熒惑→心 | 守；期30日 | 彗星出（天象型占应） | 陳卓 | current_passage；duplicate_of=卷88对应公式 |
| C14-R09 | 熒惑→心 | 守 | 饑 | 玄冥占 | current_passage |

可操作性：30/20/10日可作持续时间；“逆行”若取按语可由黄经速度符号判定；但“守、留”均无角距或速度阈值，“色黒”无光度/色指数阈值，“心、房間”需星官坐标和边界模型。因此 **partially_computable**，实现时必须把角距、最小持续时间、速度阈值作为版本化参数，不能把古义假装成现代固定数值。

字段复核：Celestial=`five_planets, lunar_mansions, comet`（其中 comet 的角色为`outcome_only`）；Relation（占辞）=`守, 留`，按语另有`入, 逆`；Complexity=`compound`（只跨页和同节多来源，不跨主题单元）；Computability=`partially_computable`；Risk=`medium`；Special=`[]`。重复只挂在 C14-R08 的 `duplicate_of/parallel_same_book`，不提升为 case 标签。Formal candidate=`YES`；Citation eligible=`YES`（存在完整局部原子）；whole_passage_citation=`NO`；Eligibility=`eligible`。

未决：①“王都西南指”所指对象；②“后死”句法；③宋书史例二月/六月；④“守心房間”究竟“守心与房之间”还是“守心房间”的传统凝固说法。

## C31｜卷43 / KR3g0018_WYG_043-12b

### 边界、实体与断句

- 所属小节：**「填星犯太㣲四十四」**（043-11b），下一节“填星犯黄帝座四十五”（043-14a）。
- 左边界应上接 043-12a：“石氏曰填星入西門出東門……”，原 passage 从该句中部开始；右边界应续到 043-13a“入西門西折出右掖門……不從主命”。
- 卷66星官定义明确：“太㣲西蕃……上將北間為太陽西門……次將北間為中華西門……次相北間為太隂西門”，东蕃同理（[卷66固定提交](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_066.txt#L287-L328)）。所以 **太陰西門/東門是太微蕃垣的门隙名，不是月亮**；中華门、太陽门也同属门隙。Celestial 中不得因“太陰”加入 moon。
- “春秋緯合誠圗”是书名《春秋緯合誠圖》；“合”不是关系词。

建议断句：

> 石氏曰：「填星入西門、出東門，皆為人君不安，欲求賢佐；入中華西門、出中華[東]門，為臣出令；入太陰西門、出太陰東門，皆為天下大亂，有䘮若大水。」春秋緯《合誠圗》曰：「填星入中華闕門者，為臣弑主之候。」黄帝占曰：「填星東行入太㣲廷、出東門，天下有兵急；若守將相、丞御史，大臣有死者；若入端門、守廷，大禍至；入南門、出東門，國大旱；若入南門南行、出西門，國有大水；逆行入東門、出西門，大國破亡；若順入西蕃而留不去，楚國凶殃。」郗萌曰：「填星入西門、犯天庭、出端門，皆為大臣伐主；入西門，西折出右掖門，皆為大臣假主之威而不從主命。」

方括号“東”只据平行文提出补字，不写回原文。白话：土星穿越太微各门、在宫廷或将相等星官处停守、逆行或滞留，被分别解释为君主不安、臣下擅令或弑主、战争、大臣死亡、旱涝、亡国等。

### 平行文、异文与来源

- 卷28岁星条作“入中華西門出中華東門……入太隂西門出太隂東門”（[卷28固定提交](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_028.txt#L242-L258)）；卷36荧惑条、卷58辰星条也同式（[卷36](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_036.txt#L108-L135)、[卷58](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_058.txt#L198-L218)）。卷43“出中華門間”高度疑为“出中華東門”的脱/讹，但仅建议校勘。
- 《合誠圖》同式在卷28作“嵗星入華闕門者為臣殺之候之”，卷36作“熒惑入華闕門臣殺之候也”，卷58作“辰星入華闕門為臣弑之候也”。“殺/弑”“中華闕门/華闕门”均登记为对象/措辞异文，不混成一个无版本身份的标准句。
- 书内引书/作者：石氏、《春秋緯合誠圖》、《黄帝占》、郗萌；实体释义另引卷66《黄帝占》《春秋元命包》。载体为《唐開元占經》。

### 原子规则

| ID | 主体→客体 | 关系/条件 | 占应 | 来源 | Citation scope |
|---|---|---|---|---|---|
| C31-R01 | 填星→太微西/东门 | 入西、出东 | 人君不安，欲求贤佐 | 石氏 | expanded_context |
| C31-R02 | 填星→中華西/东门 | 入西、出东；载体作“出中華門間”，“東”仅为校补候选 | 臣出令 | 石氏 | expanded_context；textual_variant |
| C31-R03 | 填星→太陰西/东门 | 入西、出东 | 天下大乱，有丧或大水 | 石氏 | expanded_context |
| C31-R04 | 填星→中華闕門 | 入 | 臣弑主之候；他卷“殺/弑”仅登记异文 | 春秋緯合誠圖 | current_passage；textual_variant |
| C31-R05 | 填星→太微廷/东门 | 东行入、出东 | 天下兵急 | 黄帝占 | current_passage |
| C31-R06 | 填星→将相、丞御史 | 守 | 大臣死 | 黄帝占 | current_passage |
| C31-R07 | 填星→端門/廷 | 入端门、守廷 | 大祸至 | 黄帝占 | current_passage |
| C31-R08 | 填星→南门/东门 | 入南、出东 | 国大旱 | 黄帝占 | current_passage |
| C31-R09 | 填星→南门/西门 | 入南、南行、出西 | 国大水 | 黄帝占 | current_passage |
| C31-R10 | 填星→东门/西门 | 逆行入东、出西 | 大国破亡 | 黄帝占 | current_passage |
| C31-R11 | 填星→西蕃 | 顺入、留不去 | 楚国凶殃 | 黄帝占 | current_passage |
| C31-R12 | 填星→西门/天庭/端门 | 入、犯、出 | 大臣伐主 | 郗萌 | current_passage |
| C31-R13 | 填星→西门/右掖门 | 入西，西折出右掖 | 大臣假主威、不从主命 | 郗萌 | expanded_context |

可操作性：“逆行”可从土星视黄经速度判断；“入/出门”必须先把门隙两侧星映射到具体星表，并定义穿越线段/垣界的时刻；“守”及“犯”无角距，“留不去”无速度与日数。故 partially_computable；不得把《合誠圖》的“合”或“太陰门”的“太陰”做实体误标。

字段复核：Celestial=`five_planets`，另设 target_entity_types=`enclosure, asterism` 承接太微、门隙和太微内星官；不得把太微编码为`lunar_mansions`。Relation=`入, 守, 留, 逆, 犯`（删除误命中的`合`）；Complexity=`compound`（同一太微主题单元内跨页、多来源）；Computability=`partially_computable`；Risk=`high`；Special=`[]`。卷43“門間/東門”与他卷“殺/弑”仅作为原子级 `textual_variant`，不构成逻辑冲突。Formal candidate=`YES`；Citation eligible=`YES`；whole_passage_citation=`NO`；Eligibility=`eligible`。

未决：①“中華門間”的底本字形是否有影印可复核；②“入中華闕門”是否等同特定中華门隙，不能仅凭词形合并；③“若守將相丞御史”中“丞御史”的切分与所指星官。

## C33｜卷45 / KR3g0018_WYG_045-8b

### 上下小节与完整边界

- 上节：**「太白王相休囚死三」**（045-7a）。原首“不祥”属于 045-8a“當其囚也……有死色妖言多不祥”，故左边界至少回到“當其囚也而有王色……”。该节至 045-8b“其退舎也兵不成行”结束。
- 下节：**「太白光色芒角四」**（045-8b）。原末“凶山”应续 045-9a“崩地裂……脩邊地”，首条《荆州占》到此完整；再起“甘氏曰候太白以秋庚辛……”。
- 因而 passage 不是一个规则，而是“王相休囚死”尾段 + 新标题 + “光色芒角”首条。整段不能一口引用，拆分后可引。

恢复原文骨架（保留原字）：

> 當其囚也而有王色大將反成有相色下犯其上有休色野多暴兵盗賊並起有死色妖言多不祥所留之舎不可舉事用兵其進舎也歲多雹霜萬物不成其退舎也秋冬無霜雪　當其死也而有王色流水湯湯有相色野火煌煌有休色金幣不行有囚色國多虎狼其留守也野獸食人其進舎也白刃鏘鏘其退舎也兵不成行
>
> 太白光色芒角四　荆州占曰秋三月太白出西方色當白而不白逆行必有金石之妖且見隕星墜為石石之所下冦至其野凶山崩地裂出水無火而金自燔天雨血髙臺自壓見此二者國有大䘮及為祠蓐收西海之神命及為役命兵令勤事試車馬警邊境脩邊地

建议断句：

> 當其囚也，而有王色，大將反成；有相色，下犯其上；有休色，野多暴兵，盗賊並起；有死色，妖言多不祥。所留之舎，不可舉事用兵；其進舎也，歲多雹霜，萬物不成；其退舎也，秋冬無霜雪。當其死也，而有王色，流水湯湯；有相色，野火煌煌；有休色，金幣不行；有囚色，國多虎狼；其留守也，野獸食人；其進舎也，白刃鏘鏘；其退舎也，兵不成行。
>
> 荆州占曰：「秋三月，太白出西方，色當白而不白，逆行，必有金石之妖；且見隕星墜為石，石之所下，冦至其野，凶；山崩地裂，出水；無火而金自燔；天雨血；髙臺自壓。見此二者，國有大䘮……」

白话：第一节按太白处于“囚/死”等季节旺衰状态而呈现其他状态的颜色、并按停留/前进/退行，配出兵变、灾害等占应。第二节说秋季太白本当白而不白且逆行，将出现金石异象、陨石、敌寇和山崩等灾异；这不是现代自然因果陈述。

### 来源、平行与校勘

- 上节书内引《荆州占》与甘氏（目标尾段承甘氏）；下节首条为《荆州占》，后续引甘氏、石氏、班固《天文志》《天官書》等。载体仍为《唐開元占經》。
- 《乾象通鑑》有近似“若秋三月，太白出西方，色當白，不白而逆，必有金石之祅，且見隕星……”（[直达页](https://www.shidianguji.com/book/NGJ892411999009527115717/chapter/1loelzsu63ium)）。这是后出汇编平行，不足以单独改《开元占经》；其“妖/祅”“逆行/不白而逆”登记异文。
- 国家图书馆影像检索片段有“石之下寇至其野”而转写本作“石之所下冦至其野”；未逐字核影像前，不删“所”。

### 原子规则（主要条目）

| ID | 主体/条件 | 关系 | 占应 | 来源 | Citation scope |
|---|---|---|---|---|---|
| C33-R01 | 太白当囚而有王色 | 状态+颜色 | 大将反成 | 甘氏段 | expanded_context |
| C33-R02 | 太白当囚而有相色 | 状态+颜色 | 下犯其上 | 甘氏段 | expanded_context |
| C33-R03 | 太白当囚而有休色 | 状态+颜色 | 暴兵、盗贼并起 | 甘氏段 | expanded_context |
| C33-R04 | 太白当囚而有死色 | 状态+颜色 | 妖言多不祥 | 甘氏段 | expanded_context |
| C33-R05 | 太白→所留之舍 | 留 | 不可举事用兵 | 甘氏段 | expanded_context |
| C33-R06 | 太白→进舍 | 进 | 雹霜、万物不成 | 甘氏段 | expanded_context |
| C33-R07 | 太白→退舍 | 退 | 秋冬无霜雪 | 甘氏段 | expanded_context |
| C33-R08 | 太白当死而有王/相/休/囚色 | 状态+颜色（四分） | 流水/野火/金币不行/虎狼 | 甘氏段 | expanded_context |
| C33-R09 | 太白 | 留守 | 野兽食人 | 甘氏段 | expanded_context |
| C33-R10 | 太白 | 进舍 / 退舍 | 白刃鏘鏘 / 兵不成行 | 甘氏段 | expanded_context |
| C33-R11 | 太白 | 秋三月；出西方；当白而不白；逆行 | 金石之妖 | 荆州占 | current_passage |
| C33-R12 | 同上 | 同上 | 见陨星坠石；落区有寇 | 荆州占 | current_passage |
| C33-R13 | 同上 | 同上 | 山崩地裂、出水等灾异 | 荆州占 | expanded_context |

可操作性：季节“秋三月”、出西方和逆行可由历日/视运动部分计算；“留守/进舍/退舍”缺速度阈值及舍界；“色當白而不白”、王相休囚死色和芒角缺颜色、亮度、视觉角度阈值。“隕星墜為石”是占应而非太白观测字段。故 partially_computable。

字段复核：Celestial=`five_planets, meteor`（其中 meteor 的角色为`outcome_only`）；Relation=`守, 留, 逆`（“进/退”不在既定枚举）；Complexity=`cross_passage`；Computability=`partially_computable`；Risk=`medium`；Special=`[]`。Formal candidate=`YES`；Citation eligible=`YES`；whole_passage_citation=`NO`；Eligibility=`eligible`。

未决：①“見此二者”究指紧邻哪两异象；②“石之所下”影像字形；③“當其囚/死”的历法季节模型与颜色分类不能由本段单独定量。

## C41｜卷74 / KR3g0018_WYG_074-9b

### 边界、断句与层次

- 所属小节：**「流星犯紫宫十四」**（074-9a），下一节“流星犯北極十五”（074-11a）。原首是《宋天文志》长按语中段；核心占辞从“石氏曰”起。原末“水旱不”须下接 074-10a“調”。
- 建议核心断句：

> 石氏曰：「流星入紫宫，主憂；天下多死者；臣犯主。」又曰：「入紫宫，使者憂。」又曰：「入紫宫，使者復命，名曰使星；諸侯有來使者。」班固《天文志》曰：「孝昭元平元年三月丙戌，流星出翼、軫東北，干太㣲紫宫；始出小，旦入大，有光；入有聲如雷，三鳴止。」〔校读：《漢書·天文志》作“干太微，入紫宮；始出小，且入大，有光；入有頃，聲如雷”。〕占曰：「流星入紫宫，天下大凶。」其年四月癸未，宫車晏駕。荆州占曰：「流星入紫宫，水旱不調。」

白话：流星进入紫微宫，被解释成君主忧惧、多人死亡、臣下冒犯君主、使者忧或来使，以及水旱失调。汉昭帝史例记录一颗流星从翼、轸东北出现，经过太微进入紫宫，伴随亮光和雷声；随后附会帝崩。

- **“臣犯主”是占应的人事关系，不是天象关系词**。卷84“客星犯紫宫中帝座，大臣犯主”也呈“天象犯座 → 大臣犯主”的平行结构（[卷84固定提交](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_084.txt#L193-L200)）。Relation 只取流星“入”；班固史例的“干太微”可登记事实层，但不把人事“犯”混入。
- **载体与校读分层**：本卷载体原文是“干太㣲紫宫”，没有“入”；不得静默写成“干太微，入紫宫”。《漢書》现存本提供校读“干太微，入紫宮”，并另有“且/旦”“入有頃/入有聲”异文；见[《漢書》卷26](https://zh.wikisource.org/wiki/%E6%BC%A2%E6%9B%B8/%E5%8D%B7026)。若采用“入紫宫”释读，必须标为 `collated_reading`，不冒充 `carrier_text`。
- 书内来源：司马彪《天文志》、沈约《宋天文志》（左侧按语）、石氏、班固《天文志》、《荆州占》；右续还有韦昭《洞纪》。载体为《唐開元占經》。

### 原子规则

| ID | 主体→客体 | 关系/条件 | 占应 | 来源 | Citation scope |
|---|---|---|---|---|---|
| C41-R01 | 流星→紫宫 | 入 | 主忧 | 石氏 | current_passage |
| C41-R02 | 流星→紫宫 | 入 | 天下多死者 | 石氏 | current_passage |
| C41-R03 | 流星→紫宫 | 入 | 臣犯主（人事占应） | 石氏 | current_passage |
| C41-R04 | 流星→紫宫 | 入 | 使者忧 | 石氏 | current_passage |
| C41-R05 | 流星→紫宫 | 入/复入语义待考 | 使者复命、诸侯来使 | 石氏 | current_passage |
| C41-R06 | 流星→太微、紫宫 | carrier_text=“出翼軫東北干太㣲紫宫”；collated_reading=“干太微，入紫宮”；小→大、有光、有声 | 史实记录，非占应 | 班固天文志 | current_passage |
| C41-R07 | 流星→紫宫 | 入 | 天下大凶 | 班固天文志所载占 | current_passage |
| C41-R08 | 流星→紫宫 | 入 | 水旱不调 | 荆州占 | expanded_context |

可操作性：如果有现代流星轨迹，可判断轨迹是否穿过紫宫多边形；但古文未给紫宫边界版本、入界容差、亮度、持续时间，且“有聲”涉及延迟与观测地点。故 partially_computable，而非 fully computable。

字段复核：Celestial=`meteor`，另设 target_entity_types=`enclosure, asterism` 承接紫宫、太微及翼轸；不得把紫宫/太微编码为`lunar_mansions`。Relation=`入`（删除人事占应中的“犯/守”）；Complexity=`compound`；Computability=`partially_computable`；Risk=`medium`（载体与《漢書》路径、字词须分层）；Special=`[]`。Formal candidate=`YES`；Citation eligible=`YES`；whole_passage_citation=`NO`；Eligibility=`eligible`。

未决：①“入有聲”与《漢書》“入有頃，聲如雷”的文字关系需影印本复核；②“使者復命”是否隐含“出后复入”，本句未明说，不宜加条件。

## C43｜卷79 / KR3g0018_WYG_079-7b

### 边界、实体与断句

- 原首属于上节 **「客星犯虚四」**：须上接 079-7a末“石氏曰客星”，恢复“石氏曰客星犯守虚……”。079-7b中部新起 **「客星犯危五」**。采用**最小修界**：原末“甘氏曰客星出危大臣被刑”只续至 079-8a“法官有憂；國多水災；有土功，王者築宫室，期不出年”而止。其后的“甘氏曰客星守危……”、郗萌、巫咸、《黄帝占》等属于 `context_only`，不纳入本案原子；下一节为“客星犯營室六”。
- “離宫”实体由卷61明定“離宫六星”“主隱藏”，是营室附近星官（[卷61固定提交](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_061.txt#L120-L151)；卷106又列“營室二星、離宫六星”：[卷106](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_106.txt#L36-L43)）。因此“逆行在離宫北”是“在星官離宫之北”，**不是关系词‘离’**。

建议断句：

> 石氏曰：「客星犯守虚，近一年，逺二年，當有哭泣之事。」（郗萌曰：「國有哭臨之事。」）陳卓曰：「客星犯守虚，天下有謀。」
>
> 客星犯危五。郗萌曰：「客星犯危，國有哭泣之事。」（案宋書天文志曰：魏明帝景初二年十月癸巳，客星見危，逆行，在離宫北、螣蛇南；三年正月，明帝崩。）一曰：「多雨水，五穀不收，人相食於道。」荆州占曰：「客星入危，有土功，王者築宫室；不出一年，大水；不出三年，大飢，萬人無食。」百二十占曰：「他星入危，有盖屋之事；色赤，大變；青，憂。」甘氏曰：「客星出危，大臣被刑，法官有憂；國多水災；有土功，王者築宫室，期不出年。」

白话：客星靠近或停守虚、危，被解释为哭丧、阴谋、雨灾歉收、饥荒与营建；史例记客星出现在危宿，逆行于离宫北、螣蛇南，后附会魏明帝去世。

### 事实、占应、历史按语与平行文

- 天象事实：宋书史例“客星見危，逆行，在離宫北、螣蛇南”；《宋書》现存本作“騰蛇南”，并续有“甲辰犯宗星，己酉滅”（[《宋書》卷23](https://zh.wikisource.org/wiki/%E5%AE%8B%E6%9B%B8/%E5%8D%B723)）。本卷节引省略后两事件并写“螣”，不得用宋书现代标点静默覆盖。
- 占应：哭泣、天下有谋、多雨歉收、土功宫室、水灾、饥荒等。
- 历史按语：魏明帝崩，是验占叙事；不属于“客星犯危”的条件。
- 平行：卷32“熒惑犯守虚有土功之事”、卷95“赤雲氣入危有土功蓋屋之事大作”，显示“虚/危—土功/盖屋”的书内公式族（[卷32](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_032.txt#L154-L172)、[卷95](https://github.com/kanripo/KR3g0018/blob/eb17a11a6a8a40922ccff01f727e2b5df7f3e734/KR3g0018_095.txt#L98-L114)），属于近似公式而非同一条重复。
- 书内来源：石氏、郗萌、陳卓、《宋書·天文志》、《荆州占》、《百二十占》、甘氏。续文的巫咸、《黄帝占》仅作 `context_only`，不参与本案规则。载体为《唐開元占經》。

### 原子规则

| ID | 主体→客体 | 关系/条件 | 占应 | 来源 | Citation scope |
|---|---|---|---|---|---|
| C43-R01 | 客星→虚 | 犯守；应期近1年、远2年 | 哭泣之事 | 石氏；郗萌异说 | expanded_context |
| C43-R02 | 客星→虚 | 犯守 | 天下有谋 | 陳卓 | current_passage |
| C43-R03 | 客星→危 | 犯 | 国有哭泣 | 郗萌 | current_passage |
| C43-R04 | 客星→危/離宫/螣蛇 | 见危、逆行、在離宫北螣蛇南 | 史实；后接帝崩验占 | 宋書按语 | current_passage |
| C43-R05 | 客星→危 | 犯（“一曰”承前） | 多雨、五谷不收、人相食 | 郗萌段异说 | current_passage |
| C43-R06 | 客星→危 | 入 | 有土功、王者筑宫室 | 荆州占 | current_passage |
| C43-R07 | 客星→危 | 入；不出1年/3年 | 大水 / 大饥万人无食 | 荆州占 | current_passage |
| C43-R08 | 他星→危 | 入；色赤/青 | 盖屋；大变/忧（断句待核） | 百二十占 | current_passage |
| C43-R09 | 客星→危 | 出 | 大臣被刑、法官忧；水灾；土功 | 甘氏 | expanded_context |

可操作性：“逆行”原则上需要多夜测位；客星究竟是新星、彗星或其他移动天体会改变算法。“犯/守/入”均无角距/边界/持续时间；R01的近一年、远二年是应期，不是守的观测时长。颜色“赤/青”亦无阈值。故 partially_computable。

字段复核：Celestial=`guest_star, lunar_mansions`；Relation（占辞）=`犯, 守, 入`，按语另有`逆`；删除`离`；Complexity=`cross_passage`（文本跨“犯虚/犯危”两个明确小节）；Computability=`partially_computable`；Risk=`medium`；Special=`[]`。Formal candidate=`YES`；Citation eligible=`YES`；whole_passage_citation=`NO`；Eligibility=`eligible`。R10-R11 及其后续规则已移出原子清单，统一标为 `context_only`。

未决：①《百二十占》“色赤大變青憂”的标点；②“犯守”是两个备选关系还是复合术语；③客星类别与其“逆行”的现代对应；④螣/騰字形仅登记异文。

## 五条最终三项结论

| Case | Formal candidate | Citation eligible | Eligibility |
|---|---|---|---|
| C14 | YES | YES（whole_passage_citation=NO） | eligible |
| C31 | YES | YES（whole_passage_citation=NO） | eligible |
| C33 | YES | YES（whole_passage_citation=NO） | eligible |
| C41 | YES | YES（whole_passage_citation=NO） | eligible |
| C43 | YES | YES（whole_passage_citation=NO） | eligible |

## Fix log

- 修复轮 1：将五案 case-level `Citation eligible` 统一为标量 `YES`，另设 `whole_passage_citation=NO`，并为每个原子添加 `current_passage | expanded_context | not_yet_citable` 范围标记。
- C14：Complexity 改为 `compound`；case-level Special 清空；duplicate 只挂 C14-R08。
- C31：移除 `lunar_mansions`，新增 `target_entity_types=enclosure, asterism`；Complexity 改为 `compound`；Eligibility 改为 `eligible`；“門間/東門”和“殺/弑”降为原子级 `textual_variant`。
- C33：保留 `cross_passage`，明确两小节边界与各原子引用范围。
- C41：移除 `lunar_mansions`，新增 `target_entity_types=enclosure, asterism`；严格分开载体 `carrier_text` 与《漢書》`collated_reading`，不静默补“入”；Risk 改为 `medium`。
- C43：采用最小右边界，删除 C43-R10/R11，将更后续材料标为 `context_only`。
- 五案 `ancient_books` 已在 JSON 中补 `scope`；Complexity、Relation、Special tags 均按现有枚举复核。
