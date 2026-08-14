# Core14 四项争议条目第二轮证据裁决

任务：`B10-R06`。对象：`C03`、`C24`、`C33`、`C47`。本文件是
append-only 研究裁决，不覆盖 B10-R02 既有审计，不是 Reviewer B 人工
标注，也不授权阈值冻结或启动 B10-PR-D/E/F。

结构化记录：
`corpus/research_sources/b10-core14/disputed-case-second-review.json`。

## 总结

| 条目 | Reviewer A 当前值 | 第二轮研究处理 | 当前引用资格 | Reviewer B 要点 |
|---|---|---|---|---|
| C03 | `needs_review` | 保持；撤销“逻辑冲突”解释，按来源与关系拆分 | NO | 独立判断 source divergence 是否需要特殊标签 |
| C24 | `ambiguous` | 保持；S8/S9 分节，`㑹客環守` 不校改 | NO | 独立判断是否继续 ambiguous，不选择猜测性句读 |
| C33 | `needs_review` | 右边界已补齐；研究建议分节后可转 eligible | NO，待真人确认 | 排除上一节 `其留守也`，确认新节完整范围 |
| C47 | `eligible` | 保持；无 `duplicate_of`，不得标 duplicate | YES，限原子与异文披露 | 独立确认异文不等于重复候选 |

四条仍都是研究／正式候选；但“有候选价值”与“当前可引用”是不同字段。
Reviewer B 未开始，双真人门禁仍未满足。

## C03：多来源异占不等于逻辑矛盾

固定定位：`卷12 / KR3g0018_WYG_012-5b`；Wikisource fixed revision
`655898`；Kanripo commit
`eb17a11a6a8a40922ccff01f727e2b5df7f3e734`，blob
`4b4450e953bd528ab22bf9f70d88e618338f71b2`。

边界复核：左端“法令散”回接“春秋緯元命包曰歲星逆犯月”；岁星段止于
“荆州占曰月吞歲星其國十二歲而敗”，随后“熒惑入月中”已经换为火星
主体。因此 frozen row 不能整体引用。

当前段依次列出 `逆犯、犯、乘、貫、蝕、吞`，并分别引《元命包》、
《河圖帝覽嬉》《荆州占》《天官书》等。它们的占应不同，只能说明
来源并列和占应分歧，不能推出逻辑互斥，也不能拼成一个联合预测。
《史记·天官书》fixed accession
`zhws-shiji-027-r7904116` 直接支持其中“月蝕歲星”原子，但不能替其他
来源裁决。

处理：case 保持 `needs_review`，`Formal candidate=YES`、当前
`Citation eligible=NO`；保留逐原子资格。`一年二年乘之` 与 `邦主無`
继续 defer。

## C24：同书平行不能唯一恢复 `㑹客環守`

固定定位：`卷38 / KR3g0018_WYG_038-13b`；Wikisource fixed revision
`655950`；Kanripo blob `0e632ebfa0ab9659fc9b9424063c3a08a970dbf9`。

必须保留两节：

- `填星流動與列星鬭八`：运动、变色、逆行、凌斗与列星关系；
- `填星穰氣暈彗九`：珥鱼、狗状云、黄穰、四丈穰气、自晕、出彗。

同书卷23作“舍合留舍環守”，卷30作“㑹舍還”，卷38作
“㑹客環守”。三者能证明句式骨架相近，却不能证明卷38应改成哪一种。
因此 `守` 不能从未决串中提升为正式关系，原字串也不能被静默覆盖。

本段引《洛书》《黄帝占》，但本项目迄今未找到可独立核验的完整传本；
《黄帝占》与目录中的《黄帝五星占》是否同一文本也仍是书目假说。现阶段
只能把《唐开元占经》记为这些引文的现存载体，不能把书名本身当成另一份
独立证据。

固定《开元占经》载“雲如狗狀……期一月”。后出《欽定天文正義》
电子文本见“獨雲／期一年”，属于后世汇编的 reception variant；在没有
固定影印页、版本说明和独立校勘前，只作研究线索，不反改 primary
carrier。

处理：保持 `ambiguous`；whole row 不可引用；S8/S9 各原子另判。形状、
颜色、亮度、角距、四丈单位和缺测策略仍没有可执行阈值。

## C33：右边界已补齐，但上一节关系必须剥离

固定定位：`卷45 / KR3g0018_WYG_045-8b`；Wikisource fixed revision
`655964`；Kanripo blob `722732bd1bb856685ef869ff5cd31a48bc2d3297`。

第二轮确认两件事：

1. “其留守也野獸食人”仍属于上一节 `太白王相休囚死三`；不能把
   `守/留` 带入下一规则。
2. 新节 `太白光色芒角四` 的荆州占句跨到 045-9a，完整止于
   “警邊境脩邊地”；随后“甘氏曰候太白以秋庚辛”才是下一来源单元。

因此“缺下一页”的证据缺口已经关闭。新节的正式关系只应保留 `逆`；
陨星坠石属于关联观测／占应内容，不是上一节 `守/留` 关系的延续。
仍需把“見此二者”指代单独隔离。

处理：为了不越过真人门禁，Reviewer A 当前仍保持 `needs_review` 和
`Citation eligible=NO`；第二轮研究建议 Reviewer B 独立确认分节后，可
将其裁决为 `eligible_after_split`。

## C47：平行文本是异文来源，不是重复候选

固定定位：`卷89 / KR3g0018_WYG_089-18a`；Wikisource fixed revision
`656052`；Kanripo blob `a2df04268d4e5b6b13fc58628f151cd578ae3cc8`。

右边界跨至 089-19a，止于“日相當之時見七十日主當之”；随后
`鬼彗孛犯輿鬼` 另起。现有 R02、related-source mapping 和 Core14 集合中
均没有一个可写入 `duplicate_of` 的 passage/candidate ID。

《乙巳占》fixed accession `zhws-yisizhan-8-r2623978` 提供实质平行，且有
`謀／誅`、`東井／井`、`相當之時／相當之` 等异文。这是需要保留
provenance 的 material variant，不等于同一数据集中存在重复候选。

处理：保持 `eligible`、`duplicate_of=null`、special tags 为空；只允许
原子级引用并强制披露上述异文。若以后发现真实重复对象，必须提交具体
ID 与同一性证据，再单独改判。

## 结论与门禁

- Reviewer A：已由用户确认，14/14 READY；本任务不改其文件字节。
- Reviewer B：`UNLABELLED · HUMAN REVIEW NOT STARTED`。
- PR #54：继续 Draft/BLOCKED。
- canonical `threshold-freeze.json`：未授权、未生成。
- B10-PR-D/E/F、B11/B12：不得启动。
- runtime、主规则、主数据、Qdrant、`local_kb_default`、`main`：均不触碰。
