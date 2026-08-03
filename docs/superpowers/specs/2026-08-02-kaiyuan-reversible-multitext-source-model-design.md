# B10 可逆多文本来源模型与自然边界本地化设计

日期：2026-08-02
状态：研究设计已接受；生产多文本 schema 仍未冻结
基线：stable/kaiyuan-v2 at 090f1b95d1c0b798077162408cea3d3bedd975a5
任务：B10-R04

## 设计结论

采用三段式方案：A 为不可变 accession 保存层，B 为可删除并由 A 重建的 Work–TextVersion–Carrier–SourceObject 影子图，C 为延后到 B10-PR-F 之后且必须经过人工批准的规则适配器。

“与《唐開元占經》同等待遇”定义为同等的来源治理、固定版本、原始字节、哈希、卷篇分母、校勘边界和审查可追溯性，不等于把大型正史的全部卷页无差别镜像到仓库。

## 方案比较

| 方案 | 优点 | 主要风险 | 决定 |
|---|---|---|---|
| A：仅使用文件与 manifest | 原始来源最直接、可逆性最高、改动最小 | 版本关系和重复事实依赖自由文本，扩展后审查成本线性增长 | 保留为权威保存层 |
| B：四层来源影子图 | 可区分作品、版本、载体和固定来源对象；适合校勘、同源判断和全书分母 | 前期需要明确事实所有权和未知状态 | 选为研究层 |
| C：直接并入 RuleCandidate/OmenRule | 规则消费表面上最直接 | 会把研究性来源变化传播到 candidate identity、黄金集和正式规则；可能稀释 citable 门禁 | 延后到 PR-F 之后 |

## 1. 使命与非目标

### 使命

当项目新增任何古书页、版本或载体时，系统能够保存不可变原始字节，明确它属于什么作品与版本家族，显示支持证据、异文和未知项，并在人工批准前保证正式候选和规则身份不发生变化。

主要受益者是古籍研究者、Reviewer A/B、规则结构化维护者和后续 B11/B12 消费方。当前时间范围只覆盖 B10 研究来源层和 P0/P1/P2 本地化，不承诺建立通用古籍平台。

系统级成功标准：

- 固定来源对象可重复回放，字节和 SHA-256 一致；
- 同源转录不会被误计为独立见证；
- 研究映射可以无损往返，不改变 OmenRule/v2 或 RuleCandidate/v2；
- 未知、分歧、失效和缺页均进入显式分母；
- 批量扩展可中断、复验、回滚，不覆盖旧 accession；
- 人工工作量和 deferred 项持续可见。

不可接受的伤害：静默改写原文、把辑本冒充古本、把目录冒充正文、把 AI 研究冒充 Reviewer A/B、把相似文本自动合并为独立证据、或让来源补充改变正式规则身份。

非目标：

- 不自动选择“正确异文”；
- 不冻结权威书名、版本谱系或 canonical segment；
- 不完成 PR #54 的两位真人审核；
- 不启动 B10-PR-D；
- 不进入正式 KB、Qdrant 或 local_kb_default；
- 不扩大为四部正史全文镜像。

## 2. 利益相关者与系统边界

| 参与者或系统 | 职责 | 输入 | 输出 | 约束 |
|---|---|---|---|---|
| 来源采集器 | 固定 oldid/commit 并保存原始字节 | 公开来源定位 | accession、raw、hash | no-overwrite；失败不得更新旧对象 |
| 书目影子图 | 表达作品、版本、载体和来源对象关系 | accession 与人工书目观察 | 可重建图和未知关系 | 不拥有 raw；不批准规则 |
| 证据对齐层 | 保存 source span 到 case/atom 的研究关系 | source object、Core14 case/atom | evidence link、alignment hypothesis | atom 不确定时降级到 case |
| 研究审稿人 | 接受、拒绝或 defer 图关系和对齐假设 | 观察与相反证据 | append-only 研究决定 | 不等于 Reviewer A/B |
| Reviewer A/B | 完成 PR #54 正式黄金集审核 | 冻结工作表 | 正式人工标签 | 两个不同真人独立完成 |
| B10 规则流水线 | 管理候选、正式规则和身份历史 | 《唐開元占經》 passage、人工审核 | RuleCandidate/OmenRule | 多文本研究层不得改变其身份 |

变量分类：

- 受控：accession ID、raw path、capture method、hash、byte count、图投影版本、校验器版本；
- 直接观察：页面打印题名、oldid、revision timestamp、raw bytes、页内标题和卷次；
- 间接观察：页面目录、平台元数据、底本说明和同源线索；
- 推断：规范题名、TextVersion 身份、派生关系、是否独立见证、片段对齐；
- 未知：未标底本、失传书的版本谱系、目录红链是否曾有正文、无法复验的古本来源。

## 3. 上下文与反馈闭环

最小闭环：

公开固定来源 → accession 保存与回放 → 四层身份估计 → 对齐假设 → 独立研究复核 → 无损反向投影 → 差异与失败反馈 → 修订研究契约。

每个箭头的责任与失败行为：

- 来源到 accession：网络或 revision 不可得时记录 unavailable，不创建伪快照；
- accession 到图：只引用 accession_id，不复制或改写 raw；无法识别时使用 unknown；
- 图到对齐：必须携带方向、source locator、case/atom scope 和证据摘录；
- 对齐到复核：支持证据和相反证据同时提交，研究分歧进入 deferred；
- 复核到投影：必须能重建现有 manifest/mapping；任何字段丢失即 pilot 失败；
- 反馈到契约：只增加新版本或新关系记录，不覆盖已发布 accession 和决定。

## 4. 子系统与接口契约

| 子系统 | 唯一责任 | 输入契约 | 输出契约 | 失败行为 | 可替换实现 |
|---|---|---|---|---|---|
| Source Preservation | oldid/commit、raw、SHA、byte、capture 状态 | research-accession/v1 | 不可变 accession 及 raw | 隔离新对象，保留旧对象 | GitHub/Wikisource/Kanripo adapter 可替换 |
| Bibliographic Shadow Graph | Work、TextVersion、Carrier、SourceObject 身份与关系 | accession 引用 | research-source-graph/pilot-v0 | 图停止发布，A 层继续可用 | JSON sidecar 后续可替换为数据库 |
| Evidence Alignment | 来源片段与 Core14 的研究联系 | accession_id、locator、case/atom | research-evidence-link/pilot-v0 | atom 不确定则 case-level；target 缺失则 stale | 规则式或人工工具可替换 |
| Round-trip Projector | A 与 B 的无损转换和一致性检查 | manifest、accessions、mapping、graph | canonical projection report | 任一不一致即 fail-closed | Python 实现可替换 |
| Rule Adapter | 经人工批准后的有限投影 | approved alignment | 未来 PR-F adapter | 默认 disabled | 后续版本化实现 |

事实所有权：raw/hash/oldid 只由 Source Preservation 所有；书目关系只由 Shadow Graph 所有；case/atom 映射只由 Evidence Alignment 所有；正式审批只由 B10 规则流水线与真人审核所有。兼容字段可以重复出现，但必须标为 projection，并由一致性门禁校验。

## 5. 观察—假设—决定—结果模型

Observation 保存页面题名、oldid、revision timestamp、raw hash、raw bytes、页内卷篇标题和来源平台。

Hypothesis 保存 normalized title candidate、TextVersion candidate、derived-from、same-family、possibly-independent、alignment 和 variant。每项必须携带支持证据、相反证据、置信说明和验证方法。

Decision 由研究审稿人记录 accepted、rejected 或 deferred，包含理由、审稿身份、时间和回滚目标。研究决定不得写成 citable、approved 或 independent witness 的正式结论，除非专门的人工门禁授权。

Outcome 记录投影是否保留、撤回、降级为 case-level、标 stale 或转交未来 Reviewer A/B。所有改变 append-only。

当前明确属于 hypothesis 而非事实的字段：work_normalized_candidate、version_family、independent_witness_note、canonical alignment、异文正误。

## 6. 最小闭环 pilot

pilot 只使用 PR #57 已合并的 7 个家族、16 个 SourceObject 和 20 条研究映射，不先下载更多原文。

压力样本：

- C45：同一《後漢書》家族的“御坐／帝坐”，验证“存在实质异文但不是两个独立见证”；
- C47：《乙巳占》与《唐開元占經》载体的原子级异文，验证跨书对齐；
- C14：《宋書》《晉書》《後漢紀》多层历史材料，验证 citation_source、historical_note_parallel 和 locator_support 的差异。

入口条件：16 个 accession 均可解析，raw/hash/byte 与 merged manifest 一致，20 个 mapping target 均存在。

立即验证：从 A 生成 B，再由 B 重建 accession manifest 和 core14 mapping；canonical JSON 逐字段比较，禁止信息丢失。

延迟验证：新增15个自然边界 accession 后重复同一 round-trip，并比较审查工作量、unknown 数量和 relation reversals。

人工复核点：任何 TextVersion relation、independent witness 候选、跨书 alignment 或 atom-level mapping。

退出规则：出现 raw/hash 不一致、静默 title merge、mapping 丢失、正式 candidate/rule 改变或无法回滚时停止扩展。

## 7. 指标与验证

组件健康：

- 16/16 source object 初始回放与 hash/byte 匹配；
- 20/20 mapping 无 orphan 且可往返；
- canonical projection 与输入逐字段一致；
- schema/JSON/ID/path/duplicate 检查全部通过。

决定质量：

- title-based 自动合并为 0；
- 未经人工确认的 independent witness 为 0；
- ambiguous/deferred/unknown 全部计数；
- atom 误配或无证据扩 scope 为 0；
- 研究映射造成 candidate/rule identity 变化为 0。

系统结果：

- 每个文献族有明确自然边界、总分母、已完成、缺失、不可得和不适用；
- P1/P2 线索不会被误报为传本；
- 审稿人能从任何关系回到固定 raw 和来源定位；
- 新增一批来源后无需重写旧 raw 或正式规则。

系统学习：记录发现失败所需时间、修复时间、关系回撤数量、审查工作量、重复事实冲突和契约版本变化。

## 8. 人工审核与升级

- oldid、raw bytes、hash 和 byte count 可以机器核验；
- Work/TextVersion 身份、独立见证、异文关系和 atom 对齐必须研究复核；
- 研究复核与 PR #54 Reviewer A/B 身份域分离；
- 两位研究审稿人有分歧时保留双方意见并 defer，不以多数或模型置信自动裁决；
- 任何准备进入 OmenRule/RuleCandidate 的关系必须等待 PR-F 接口和正式人工门禁；
- 回滚通过撤回或 supersede 图关系完成，不删除历史决定或 raw。

## 9. 风险、未知与可逆决策

| 风险或假设 | 当前证据 | 错误后果 | 验证 | 可逆响应 |
|---|---|---|---|---|
| Wikisource 题名等同权威作品身份 | 多个页面底本未标 | 错误合并作品或版本 | 根页、版本说明和第二来源核对 | 保留 printed title，Work relation=unknown |
| 同平台不同卷是独立见证 | PR #57 已确认《後漢書》卷83/100同家族 | 夸大证据数量 | version/carrier 关系审查 | 标 same-family，不计独立 |
| 《幽明錄》六卷页是完整古本 | 页面底本空，原三十卷已佚 | 伪造完整传本 | 页面历史和辑佚来源核验 | 仅 P2 carrier excerpt |
| 玉函山房目录等于纬书正文 | 相关项目为红链 | 把书目线索当原文 | 固定页和正文存在性检查 | 目录只作 bibliography clue |
| 全史镜像能提高当前研究价值 | 七族全书方案约需新增631 accession | 审查负担激增并稀释范围 | 自然边界覆盖审查 | 仅扩 standalone work/完整目标篇 |
| 图模型字段过早冻结 | 权威书名和版本谱系尚未核实 | 后续迁移昂贵 | pilot-v0 round-trip | 删除重建影子图，A 层不变 |

## 10. 阶段门禁

| 阶段 | 范围 | 进入条件 | 退出证据 | 禁止扩张 |
|---|---|---|---|---|
| G0 | immutable accession | PR #57 merged | 16/16 replay/hash/byte 通过 | 不改 raw |
| G1 | shadow graph pilot | G0 通过 | C45/C47/C14 无损往返；零静默合并 | 不冻结生产 schema |
| G2 | P0 全量投影 | G1 通过 | 7家族、16对象、20映射无 orphan，unknown 显式 | 不声明未知版本独立 |
| G3 | 自然边界扩展 | G2 通过 | 15个新增 accession 全部固定、回放、分母明确 | 不扩四部正史全文 |
| G4 | P2 书目/引句登记 | G3 通过 | 《幽明錄》、纬书等失传/目录对象身份明确 | 不把目录/辑文冒充古本 |
| G5 | 校勘运行 | 对齐复核流程可用 | variant/same-family/alignment 有审查和回滚 | 不自动选正误 |
| G6 | 规则适配 | PR-C阈值冻结、PR-D稳定、PR-F接口存在 | 人工批准且 identity 影响显式 | 不直接修改 candidate identity |

## 11. 自然研究边界与下一批分母

| 文献族 | 当前自然边界 | PR #57 状态 | 下一批 |
|---|---|---|---|
| 《乙巳占》 | 独立占书十卷 | 已有卷2、5、8 | 补卷1、3、4、6、7、9、10和固定根页：8项 |
| 《史記·天官書》 | 卷27完整篇 | 卷27加根页已完成 | 0项 |
| 《漢書·天文志》 | 卷26完整篇 | 正文完成 | 补固定根页：1项 |
| 《宋書·天文志》 | 卷23–26完整篇 | 正文完成 | 补固定根页：1项 |
| 《晉書·天文志》 | 卷11–13完整篇 | 正文完成 | 补固定根页：1项 |
| 袁宏《後漢紀》 | 当前只需要C14相关卷；全书为独立30卷后续项目 | 卷16完成 | 补固定根页：1项；其余29卷不在本阶段 |
| 《後漢書·天文志》 | 卷100–102 | 已有卷100；另有C45卷83 | 补卷101、102和固定根页：3项 |

下一批总分母固定为15项。扩大到七族全部约640卷页、再新增约631 accession 的方案不进入本任务。

## 12. 研究契约冻结边界

现在可以冻结为 research-accession/v1 的不变量：

- accession_id 唯一且绑定固定 title/revision；
- page_title、oldid 或固定 commit、permanent_url、revision_timestamp；
- accessed_on、capture_status 和失败原因；
- raw_path、raw_sha256、raw_byte_count；
- raw 使用声明捕获方法保存且不可变；
- family_id 只作为本地采集分组键，不等于权威 Work ID；
- mapping 的 identity、source accession、case/atom target、locator 和 excerpt；
- 整行引用资格与原子级研究资格分离；
- 同家族文本不得自动成为独立见证；
- 研究层不得 approve、promote 或替代 Reviewer A/B。

必须延后：权威 Work ID、规范题名、作者/时代权威控制、版本类型穷举、版本谱系、独立见证结论、canonical segment/alignment ID、正字选择、完整校勘本体、OmenRule/RuleCandidate 多文本字段、正式 KB/Qdrant/发布接口。

## 13. 数据流与错误处理

SourceObject 以 accession_id 引用，不在图中复制 raw hash 事实。兼容 manifest 中的重复字段由 projector 生成并校验。

错误处理：

- raw/hash mismatch：拒绝新图投影，保留旧 accession；
- floating URL 漂移：新建 revision accession，不覆盖旧对象；
- work/version 无法确定：保留 printed title，关系 unknown；
- 相似但独立性未知：不得进入 independent witness 计数；
- atom target 不确定：降级为 case-level；
- case/atom 删除或变化：mapping 标 stale，raw 不变；
- graph schema 无法解析：停止 B 层，A 层继续独立可用；
- 任何 official KB、Qdrant、local_kb_default 调用：硬失败。

## 14. 测试策略

- 单元测试：strict schema、ID、unknown/deferred、关系方向、duplicate、orphan、循环派生和 forbidden field；
- 属性测试：输入顺序改变不改变 canonical bytes；
- round-trip fixture：16 accession、20 mapping 完整往返，逐字段一致；
- 负向 fixture：同题名不同 oldid 不自动合并，同 hash 不自动判独立，同家族异文不自动冲突升级；
- no-overwrite：已存在输出、并发发布、损坏 checkpoint 和 source change 全部 fail-closed；
- 网络回放：作为显式研究 QA，不作为 hermetic 单元测试依赖；
- 治理扫描：禁止机器路径、secret、Reviewer A/B 修改、正式 KB/Qdrant/local_kb_default 访问和 main 目标。

## 15. 完成条件

B10-R04 只有在设计、研究契约、影子图 pilot、无损 projector、现有16/20门禁、独立审查和完整工作日志均完成后才能标 DONE。15项来源扩展必须在 pilot 通过后单独进入 VERIFYING；下载数量本身不能替代身份、边界、哈希和审查证据。
