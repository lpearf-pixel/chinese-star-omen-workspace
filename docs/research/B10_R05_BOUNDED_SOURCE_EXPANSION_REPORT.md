# B10-R05 有界来源扩展报告

日期：2026-08-02  
状态：15 个固定版本来源对象已捕获，31 对象研究投影已重建并通过本地闭合验证；生产多文本 schema 仍未冻结

## 1. 范围

本轮只执行 D-026 和 B10-R04 已批准的有界扩展：在既有 7 个文献族和 16 个不可变来源对象上增加恰好 15 个 Wikisource fixed-revision 对象。没有镜像提供方的 631 对象历史，没有推断新的 Core14 关联，也没有修改 PR #54 的 Reviewer A/B 材料。

固定新增分母：

- 《乙巳占》root 与卷 1、3、4、6、7、9、10：8；
- 《漢書》root、《宋書》root、《晉書》root：3；
- 袁宏《後漢紀》（四庫全書本）root：1；
- 《後漢書》root、卷101、卷102：3。

机器可读登记表为 `b10-r05-bounded-expansion.json`。15/15 的 MediaWiki 标题、oldid 和 revision timestamp 均在捕获后重新核对一致。

## 2. Layer A 结果

| 指标 | B10-R04 稳定基线 | B10-R05 当前结果 |
|---|---:|---:|
| 文献族 | 7 | 7 |
| accession/raw 对象 | 16 | 31 |
| raw UTF-8 字节 | 645,044 | 1,050,322 |
| Layer A 文件 | 34 | 50 |
| Layer A 总字节 | 708,406 | 1,168,896 |
| Core14 mapping | 20 | 20 |

当前家族分母为：`yisizhan 11`、`shiji-tianguanshu 2`、`hanshu-tianwenzhi 2`、`songshu-tianwenzhi 5`、`jinshu-tianwenzhi 4`、`houhanji 2`、`houhanshu 5`。

身份绑定：

- 稳定基线 manifest SHA-256：`49dac42d29d8c560e15bf16dc98880b29f5f8287fd16e806d542587533b82c4f`
- 当前 manifest SHA-256：`c5ab46da6bc1ba5126758f1fce10804801572e1509bc364aaba636e4cbf676c5`
- mapping SHA-256（保持不变）：`3a79afb3cd4559236eb9869dc3b0080d6d92ebb3984b6b0c46e9a33edb056250`
- 当前 Layer A 聚合 SHA-256：`6ddb813960b5e1144022b5931cfe307b4cf725097fe439b9b960ee180beda615`

登记表保存稳定基线的 16 份 compact identity；测试逐项证明当前 manifest 中这些对象未变。加载器同时重放 31/31 raw 文件并核对 SHA-256、字节数、路径、家族连接和未登记文件集合。

## 3. Layer B 投影结果

现有 `source-projection-bundle/pilot-v0` schema 和身份规则未改。对当前 Layer A 重建后：

- 76 个节点：7 work candidate、7 text-version candidate、31 carrier、31 source object；
- 69 条书目边；
- 155 条研究断言；
- 20 条 evidence link，ID 与内容仍来自原 `core14-mapping.json`；
- 31 条 independent-witness 状态仍为 deferred；
- title-based merge 0；
- accepted independent-witness assertion 0；
- graph node/edge/assertion/evidence-link orphan 均为 0；
- B→A reverse projection 仍重建完整 manifest 与原 20 条 mapping。

投影 artifact 从 R04 的 141,956 字节、SHA-256
`4ca4bdc211889b07cedf6fe28443944f132e8d9aa3122f46eeff47d527010f8b`
更新为 233,498 字节、SHA-256
`583b00a9d160d7374453ef4ec552acc05fa8faf9841a87978a0183d1bc595468`。
R04 历史 artifact 仍由 stable commit `1a30070d3517d07097fbffe3a8ed43a9a0144c5f` 和 Git 历史固定。

## 4. 新对象的证据边界

所有 15 个新增对象都满足：

- `core14_cases: []`；
- `relevant_excerpt: ""`；
- 明确标记为自然边界对象或完整相关卷页；
- 不因同家族、相似题名或内容相邻而成为独立见证；
- 不产生新的 formal citation、rule identity、reviewer decision 或 threshold 状态。

《後漢書》卷101、102补足已批准的天文志自然边界，但仍不自动解释或批准任何 Core14 原子规则。各史书 root 只是可回放的 work/table-of-contents 边界，不是天文志文本的第二见证。

## 5. 验证

TDD 红灯先在旧 16 对象 manifest 上出现：固定的 15 个 target ID 尚不存在。数据加入后：

- inventory tests：`62 passed`；
- inventory + graph + projector + artifact focused suite：`98 passed`；
- deterministic builder `--check`：通过；
- 31/31 本地 raw SHA-256/byte replay：通过；
- 15/15 MediaWiki title/oldid/timestamp identity：通过。

完整 contract/downstream、治理检查、联网 31/31 回放和 hosted exact-head Actions 在最终验证阶段记录。

## 6. 安全与后续边界

`production_schema_freeze`、`official_kb_ingest`、`qdrant_access`、`local_kb_default_access`、`reviewer_a_b_modification` 均为 `NOT_RUN`。B10-PR-D/E/F 没有启动。PR #54 仍必须等待两名真人独立完成 Reviewer A/B。
