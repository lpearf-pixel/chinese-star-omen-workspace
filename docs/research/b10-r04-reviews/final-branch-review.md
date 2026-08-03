# B10-R04 独立整分支终审

日期：2026-08-02  
结论：`Critical 0 / Important 0 / Minor 1`  
Ready：`YES`，仅允许进入 docs-only 收尾；不得据此合并

## 1. 审查对象

- 仓库：`lpearf-pixel/chinese-star-omen-workspace`
- base：`090f1b95d1c0b798077162408cea3d3bedd975a5`
- reviewed implementation head：`df424128a5cbd530daa5dd23f7232f2da23c92f4`
- Draft PR：#58，`draft=true`、`mergeable=true`
- formal reviews：0；review threads：0

本记录绑定上述 implementation head。它之后只允许提交本记录与四份治理文档；任何源码、测试、artifact 或研究报告改动都必须重新执行全套门禁与独立终审。

## 2. 来源与可逆性分母

- 16/16 raw SHA-256 与字节数通过，总 raw 645,044 bytes。
- 16/16 compact/detailed accession join 通过，字段值与 JSON 类型一致。
- 完整 Layer A：34 files、708,406 bytes、聚合 SHA-256 `b8322d8a7a631b925ed6dde0afc01e03fb4d81882f4897c92c8efd96a7f24b74`。
- Layer A 34 个权威文件相对 stable 零修改；来源包在本分支只新增可删除、可重建的投影 artifact。
- B→A 真回投不读取原 manifest/mapping：16/16 accession 与 20/20 mapping 深度、类型和数组顺序一致。
- Core14：14 cases、130 atoms；三份 audit 与 manifest 声明哈希一致。

## 3. 图闭包与压力案例

- 46 nodes：7 WorkCandidate、7 TextVersionCandidate、16 Carrier、16 SourceObject。
- 39 bibliographic edges、80 assertions、20 evidence links；节点、边、断言、source、case、atom orphan 均为 0。
- 16 个 Carrier ID 均不含 oldid；title-based merge 为 0。
- independent witness：accepted 0、deferred 16。
- C14：精确保留 M07/M09/M12/M16/M18 五条 case-level link，四类关系不折叠，atom scope 不膨胀。
- C45：M19/M20 分属两个 SourceObject、共同指向 `C45-H2`，保留“御坐／帝坐”，同家族材料未冒充独立见证。
- C47：M03→`C47-R3`、M04→`C47-R7`；M15/M17 保持 case-level；“謀／誅”和“時／無時”边界未被规范化覆盖。

## 4. Artifact 与门禁

- Artifact：141,956 bytes，SHA-256 `4ca4bdc211889b07cedf6fe28443944f132e8d9aa3122f46eeff47d527010f8b`。
- Builder `--check`：exit 0；本地 Task 1–4 合同/清单/图/artifact 联合套件：`166 passed`；`compileall`：exit 0。
- Development Governance `30749422233`：success。
- Kaiyuan Stable Core `30749422195`：success；contracts 93、text-core 26（Python 3.9/3.12）、downstream 591。
- Kaiyuan Upstream Runtime `30749422194`：success；workspace regression 93/26/591，upstream unit 188 passed / 3 skipped，其他 release contract、Qdrant 与 candidate-roundtrip jobs 全部成功。

## 5. 安全边界

- RuleCandidate/OmenRule 路径零修改；stable 无对应版本化 JSON fixture，因此报告明确用空分母记录“无夹具”，没有伪造相等哈希。
- production schema freeze、official KB ingest、Qdrant access、`local_kb_default` access、Reviewer A/B modification 均为 `NOT_RUN`。
- B10-PR-D/E/F 仍为 `BACKLOG`；PR #54 仍等待两位真人独立审核。
- 无 `main`、B11/B12 或正式引用资格变更。

## 6. 失败闭环与发现

首次预审 head `83adfe9d…` 的两项仓库工作流因测试误用协调夹具路径而失败；第二个 head `ae760553…` 随后暴露本地夹具漏收已合并的 README 与 accession working contract，使 Layer A 分母错误地从 34 缩成 32。两项问题均由 CI fail-closed 捕获，未通过放宽断言处理；当前 reviewed head 已在完整 34 文件分母上重生成 artifact 并通过三项 Actions。

唯一 Minor：PR #58 说明仍引用旧 head `83adfe9d…` 和旧 artifact `abec414a…`。处置要求是：产生本记录所在的最终 docs-only head 后，用新 head、reviewed implementation head、当前 artifact、run IDs 和本结论更新 PR 元数据；再让三项 Actions 对最终 head 全部通过，并添加不可变顶层评论。该 Minor 不影响 implementation Ready，但在处置完成前 PR 不得合并。
