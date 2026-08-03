# B10-R04 可逆多文本来源图 Pilot 报告

日期：2026-08-02  
状态：研究层 pilot 已生成并验证；生产多文本 schema 未冻结

## 1. 范围与非目标

本轮只把 B10-R03 已固定的 7 个文献族、16 个 Wikisource revision 和 20 条 Core14 研究映射投影为可删除、可重建的研究影子图。它不选择正误异文，不声明独立见证，不改变 Reviewer A/B 结论，不建立正式引用资格，也不进入 OmenRule、RuleCandidate、正式 KB、Qdrant 或 `local_kb_default`。

## 2. 不可变 Layer A 分母

Layer A 仍以 accession、固定 oldid、raw path、SHA-256 和字节数为权威保存记录。加载器逐项连接中央 manifest 与 7 份家族 accession 记录，并重放 16/16 raw 文件；总 raw 字节数为 645,044。

输入文档身份：

- `accession-manifest.json`: `49dac42d29d8c560e15bf16dc98880b29f5f8287fd16e806d542587533b82c4f`
- `core14-mapping.json`: `3a79afb3cd4559236eb9869dc3b0080d6d92ebb3984b6b0c46e9a33edb056250`
- Layer A 包快照：34 文件、708,406 字节，聚合 SHA-256 `b8322d8a7a631b925ed6dde0afc01e03fb4d81882f4897c92c8efd96a7f24b74`

构建前后 Layer A 快照完全相同。生成器排除自身输出文件后计算快照，不改写任何 accession、metadata 或 raw 文件。

## 3. A 保存层与 B 研究层；C 继续延后

Layer B 生成 46 个节点、39 条书目边、80 条研究断言和 20 条 evidence link：

- 7 个 `work_candidate`
- 7 个 `text_version_candidate`
- 16 个 carrier
- 16 个固定 SourceObject
- 7 条 Work → TextVersion 候选关系
- 16 条 TextVersion → Carrier 延期关系
- 16 条 Carrier → SourceObject 观察关系

节点只拥有图内身份；页面题名是观察，规范题名候选是假设，版本身份、谱系和独立见证均保持 deferred。Layer C 规则适配器未实现，仍等待 B10-PR-F 及正式人工门禁。

## 4. C14 压力样本

C14 保留 5 条独立 case-level link，并区分 `material_variant`、`historical_note_parallel`、`locator_support` 和 `citation_source`。空 atom 数组保持为空，不因相似文本自动扩大到原子级；《宋書》《晉書》《後漢紀》材料未被折叠成同一证据类型。

## 5. C45 压力样本

《後漢書》卷83与卷100保留为两个固定 SourceObject；“御坐”和“帝坐”均原样保存。二者仍属于同一 received-history 家族，pilot 没有把它们提升为两个独立见证。相关 `independent_witness` 断言保持 deferred。

## 6. C47 压力样本

《乙巳占》材料保留“誅／謀”和“時／無時”的来源差异。M03、M04 继续指向原子级目标，M15、M17 继续作为 case-level locator；没有通过规范化文本静默选择某一异文。

## 7. 真正的 B → A 回投与哈希证据

兼容回投函数只接受内存中的 bundle，禁止读取路径、manifest 或 mapping。它依靠冻结的 ordinal 恢复原数组顺序，并剥离图层附加字段。回投结果与原始两个 JSON 在值、类型、递归键集合和数组顺序上完全一致：16/16 accession、20/20 mapping。

Core14 index 固定到 manifest SHA-256 `a038dcd684990810f89cd9b84f9e30ad7464505ce6bef81ad02da5e00785f968`，并重放三份 audit：

- early: `28ff207c6424f7de1ed12b9422d5d489bc69aafe9d89fda4c65f50f472695cb4`
- middle: `30d90f31852f5010c9d39c96507a279c09f59e3cd0d51011b69359ec55810121`
- late: `54d18e61f81f8be32213320ed54781e37d6565126dac88b5cb2cc905066b8ff3`

## 8. 显式未知与延期决定

本轮有 16 条 `independent_witness` 断言，全部为 deferred；accepted/rejected 研究决定为 0。title-based merge 为 0。版本身份、作者或编者的权威控制、carrier 到版本的书目关系、版本谱系和异文正误均未批准。

当前 stable 基线没有可版本化的 RuleCandidate/OmenRule v2 JSON fixture，因此 validation report 明确记录 `NO_VERSIONED_RULE_FIXTURE_IN_STABLE_BASELINE`，其 before/after 分母均为 0；没有用不存在的 fixture 伪造“哈希通过”。候选/规则身份不变由本分支 changed-path 门禁和最终独立审查另行验证。

## 9. 阶段门禁结果

G0–G2 pilot 门禁通过：

- 16/16 source replay
- 20/20 true reverse projection
- 46/46 节点、39/39 书目边、80/80 断言、20/20 evidence link 无 orphan
- C14、C45、C47 三个压力样本通过
- title-based merge 0
- accepted independent witness 0；deferred 16
- Layer A 构建前后快照一致
- production schema freeze、official KB ingest、Qdrant、`local_kb_default`、Reviewer A/B modification 均为 `NOT_RUN`

结论仅为研究层 pilot 可进入独立分支终审，不等于生产 schema 或人工批准。

## 10. 下一批有界采集

待本 pilot 审查并由项目流程授权后，下一批仍固定为 15 个自然边界 accession：

- 《乙巳占》卷1、3、4、6、7、9、10与根页：8项
- 《漢書》《宋書》《晉書》与袁宏《後漢紀》根页：4项
- 《後漢書》卷101、102与根页：3项

该批次不得扩张为七族全文约 631 个新对象；下载数量不能替代书目身份、来源分母、哈希和人工审查。
