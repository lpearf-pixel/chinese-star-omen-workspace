# 《唐開元占經》语料与检索核心 v2

## 权威文本策略

- `唐開元占經-全文合併版.md` 是不可变审计基线。
- `分卷/KR3g0018_000.md` 至 `KR3g0018_120.md` 是派生检索视图。
- 原文展示永远使用 raw text；简繁和空白规范化只用于检索。
- `&KRxxxx;` 字形实体保持原样，未提供映射表前不猜测替换。

## 当前基线审计

- 全文 SHA-256：`071ce775343c2f5fb8080c15ca0f5d980330232afe87aa89d64f18b3b3319503`
- 顶层部分：121（目录/议语 + 卷 1—120）
- 分卷文件：121
- 缺卷：0
- 去除首尾空白后的正文差异：0
- `<pb:...>` 页码标记：3435
- `&KRxxxx;` 实体：29
- Unicode replacement character：0

运行：

```bash
make audit-kaiyuan-corpus
```

## 统一匹配语义

`packages/kb-text-core` 被 filesystem fallback 和 candidate generator 共同使用：

1. `exact_raw`：原文连续字面命中；
2. `exact_normalized`：简繁或 Unicode 空白规范化后命中；
3. `loose_window`：词项在限定窗口中共同出现，只作 related candidate；
4. `heading_only`：仅标题命中，只作线索。

匹配保存原始字符 offset、页码、标题路径、段落索引与原文 excerpt。

## 排序原则

- `exact_raw` 优先于 `exact_normalized`；
- `fenjuan` 优先于重复的 `fulltext`；
- 标题与查询实体重合度高的章节优先；
- 同一页码、同一规范化 anchor 的全文与分卷命中只保留分卷。

对“荧惑守心”，卷 31 的“熒惑犯心五”应优先于卷 5、卷 88 中的旁引文字。

## Candidate 生成

Candidate 不再按“每个文件第一次命中”生成。系统会：

- 找出全部 exact spans；
- 按 page marker、heading 与邻近窗口聚类；
- 优先选择标题语义最匹配的分卷；
- 每个证据簇生成一张 candidate card；
- 保持 `candidate-card/v1` 的 `match_type: exact_phrase`，并额外记录 `source_match_type`。
