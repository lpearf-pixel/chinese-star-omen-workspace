# 《唐開元占經》语料与检索核心 v2

## 权威文本策略

- `唐開元占經-全文合併版.md` 是不可变审计基线。
- `分卷/KR3g0018_000.md` 至 `KR3g0018_120.md` 是派生检索视图。
- 原文展示永远使用 raw text；简繁和 Unicode 空白规范化只用于检索。
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
- 卷 31 的“熒惑守心”：24 个连续原文字面命中，另有 2 个仅在去除空白后成立的规范化命中。

运行前先确保正式语料已经同步；monorepo 可能只保留占位文件：

```bash
make sync-kaiyuan-source
make audit-kaiyuan-corpus
make compare-kaiyuan-volumes
make audit-kaiyuan-baseline
```

上述基线数字来自用户提供的全文与本地已同步 121 卷审计结果，不要求把全文重复提交到功能 PR。

重新分卷默认是 dry-run；必须显式指定新的输出目录和 `--write`，已有文件还需要 `--force`：

```bash
python scripts/split_kaiyuan_fulltext.py \
  --out-dir /tmp/kaiyuan-volumes \
  --write
```

## 统一匹配语义

`packages/kb-text-core` 被 filesystem fallback 和 candidate generator 共同使用：

1. `exact_raw`：原文连续字面命中；
2. `exact_normalized`：简繁或 Unicode 空白规范化后命中；
3. `loose_window`：有序词项在限定窗口中共同出现，只作 related candidate；
4. `heading_only`：仅标题命中，只作线索，不进入 exact primary。

搜索规范化保持保守：只桥接明确配置的简繁变体，不把 `臺/台`、`裏/里` 等不同字形无条件折叠。匹配保存原始字符 offset、页码、标题路径、段落索引与原文 excerpt。

## 聚类与排序原则

- 同一页码、同一标题下的邻近重复语句聚合成页级证据簇，避免 top-k 被同页重复短语淹没；
- 单条署名引文的进一步拆分属于研究卡抽取阶段，不改变 filesystem retrieval 的页级返回粒度；
- `fenjuan` 优先于重复的 `fulltext`；
- `exact_raw + fenjuan`、`exact_normalized + fenjuan` 均排在 fulltext 前；
- 同一页码、同一规范化 anchor 的全文与分卷命中只保留分卷，并记录 duplicate source；
- fulltext 页码 `KR3g0018_WYG_031-17a` 的 canonical `source_locator` 是 `KR3g0018_031`；
- `matched_headings` 返回最终证据的真实章节标题，而不是文件名。

对“荧惑守心”，卷 31 的“熒惑犯心五”应优先于卷 5、卷 88 中的旁引文字。

## Candidate 生成

Candidate 不再按“每个文件第一次命中”生成。系统会：

- 找出全部 exact spans；
- 按 page marker、heading 与邻近窗口聚类；
- 优先选择标题语义最匹配的分卷；
- 每个证据簇生成一张 candidate card；
- 保持 `candidate-card/v1` 的 `match_type: exact_phrase`，并额外记录 `source_match_type`。
