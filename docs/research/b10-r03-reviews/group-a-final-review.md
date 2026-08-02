# Group A 定向复审

## Verdict

- **Spec: PASS**
- **Quality: APPROVED**

## 原三项 finding 闭环

1. **C13：CLOSED。** `GA-YSZ-005-854562` 已改标为 C13，报告与 accession 均逐字引用 `火逆行氐，失地，一曰多火災。`，并准确定位至卷五 `○熒惑入列宿占第二十九`、raw line 11。`一曰` 被限定为同一来源对象内的异说，没有冒充独立见证。原误标的卷二 accession 已清空 `core14_cases` 并明确标为非 C13；原越界 C09 指派已移除。

2. **C47：CLOSED。** `GA-YSZ-008-2623978` 的报告与 accession 已逐字收录 `彗幹犯東井，則大臣誅，其國用兵，期百八十日。` 以及 `彗在井，大人死。見三十日，兵將當之。見五十日，相當之。見七十日，主當之。`，准确定位至卷八 `○彗孛入列宿占第四十八`、raw line 11；不再误指第四十七章开头，也未把同页差异夸大为独立版本家族。

3. **《史记》root 与对象计数：CLOSED。** 新增 `GA-SJ-ROOT-7823731`，固定 URL 为 `https://zh.wikisource.org/w/index.php?title=%E5%8F%B2%E8%A8%98&oldid=7823731`，revision timestamp 为 `2026-06-14T15:57:04Z`。远端 `action=raw` 与本地 `shiji-root-oldid-7823731.wikitext` 逐字节一致，SHA-256 为 `5952550773e4fee59cad263271feba9eb93d24ead950936c1237a9f8ac888b95`，字节数为 `13308`；root raw 明载 `內府刊本` 及三家注信息。报告也已区分四个正文页对象与第五个 root 元数据对象。

## 回放与完整性核验

定向复审对全部五个 accession 重新调用固定 revision 的 Wikisource `action=raw`，并核对 MediaWiki revision API 的 title/timestamp。五个远端对象均与本地快照逐字节一致，JSON 中的 SHA-256 与 byte count 全部匹配：

| Accession | SHA-256 | Bytes |
|---|---|---:|
| `GA-YSZ-002-854559` | `2681f158284b4767ab76a21003e001d7479d0a439065e05890e463ead317bcea` | 37209 |
| `GA-YSZ-008-2623978` | `5f482d92f856eef52452b2b10dd84b4ece887df5bc18bd11fe7d344fcd55acee` | 26328 |
| `GA-YSZ-005-854562` | `15d1774880be1178b7d61bdbcca45bedd9611fd60925e3e9b35c909cae435078` | 31158 |
| `GA-SJ-027-7904116` | `97c9840084005b7a0cb9e29e82be5a333f226a574d5980b5a3914e5f8720e7d1` | 112574 |
| `GA-SJ-ROOT-7823731` | `5952550773e4fee59cad263271feba9eb93d24ead950936c1237a9f8ac888b95` | 13308 |

未发现修正引入的新 Critical 或 Important finding。

## Finding counts

- Critical: 0
- Important: 0
- Minor: 0
- 原 finding closed: 3
