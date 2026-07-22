# B9-PR-A 契约冻结决策

## D-022 — B9 公共契约采用版本化、严格、附加兼容边界

- **Status:** Accepted
- **Applies to:** `AstronomyEvent/v1`, `RuleAssessment/v1`, `VideoPackage/v1`。

## 决策

1. 公共契约同时由 Pydantic模型、Draft 2020-12 JSON Schema、schema registry和canonical fixture表达。
2. 稳定ID只允许小写ASCII、数字及 `._:/-`；中文名称和古籍原文属于显示/内容字段，不嵌入稳定ID。
3. 数值字段拒绝布尔值、数值字符串、NaN和Infinity；时刻必须携带UTC零偏移。
4. `RuleAssessment/v1` 的正式推荐只能指向 `status=matched` 的规则；candidate、partial和insufficient结果不能成为正式推荐或可口播结论。
5. `classical_quote` 只能引用同一package inventory中的 `citable_passage`；悬空、跨包、错误类型和重复引用fail-closed。
6. v1兼容政策为 `additive-optional-only`：允许新增非必填字段或未被旧字段引用的新定义；禁止删除/新增required字段、移除既有字段、改变enum/const/type/format/pattern/范围、修改嵌套 `$defs` 语义或改变additional-properties政策。
7. Python模型负责跨字段语义；JSON Schema负责可表达的结构与键空间。两者对已表达约束不得相互矛盾。
8. canonical fixture必须逐字节稳定，manifest记录每个fixture SHA-256，registry再绑定manifest SHA-256。普通测试不得自动更新fixture。

## 理由

B9之后的规则结构化、科学计算、内容编辑和媒体生成都会消费这些契约。如果只冻结Python内部对象，后续模块容易直接依赖内部实现；如果只提交JSON Schema，又无法表达可引用证据、推荐状态和跨引用等语义。四层资产共同冻结，可以让B10/B11改变内部规则结构而不迫使内容层重写，也能在CI中发现Schema、fixture和模型漂移。

## 后果

- 破坏性变化必须创建新版本，不得原地重解释v1字段。
- 任何fixture更新必须使用独立审查，记录before/after与来源。
- B9-PR-B及后续任务只能消费本PR导出的公共接口，不得导入内部validator实现。
- Stellarium、Skyfield、检索、规则执行和媒体字段不得反向塞入本次v1契约范围；需要新增时按optional-additive或新版本处理。
