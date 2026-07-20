# B9 契约先行与证据型天象垂直样片设计

## 1. 决策与目标

B9 采用“契约先行＋垂直样片”方案，不建设完整视频平台。目标是在不扩大正式知识库写入边界、不把候选解释冒充古籍结论的前提下，冻结三个可长期复用的公共契约，并完成一条可复验的 2026-07-21 天象短视频研究包和本地预览样片。

B9 必须交付：

1. `AstronomyEvent/v1`：现代天文学事件与测量事实。
2. `RuleAssessment/v1`：规则引擎面向内容生产的稳定只读投影。
3. `VideoPackage/v1`：证据、口播、镜头、字幕、渲染和审核的版本化产物包。
4. 一条 2026-07-21 垂直样片：研究包、Stellarium `.ssc`、SRT、人工审核记录和最小竖屏预览。

B9 不负责全书规则结构化。全书规则结构化进入 B10；根据 B10 真实规则需求增强执行器进入 B11；批量选题、通用媒体流水线、配音和发布辅助进入 B12。

## 2. 明确非目标

B9 不实现：

- 全书规则自动抽取或批量审核；
- 通用视频模板市场或多风格剪辑系统；
- 自动配音、外部 TTS 服务或声音克隆；
- 未来 30 天批量天象扫描；
- 自动上传或发布抖音；
- 依赖 GUI 的普通 Linux PR CI；
- 将“开口破局”等现代文案解释为《开元占经》原文；
- 在 B9 内扩展所有“犯、入、守、掩、离、留、逆”等完整古籍规则语义。

上述需求默认进入 B10–B12，不得以“顺便优化”为由扩大 B9。

## 3. 公共契约

### 3.1 `AstronomyEvent/v1`

负责表达可重复计算的现代天文学事实，不包含占断和宣传文案。至少包含：

```text
schema_version
calculation_id
event_id
event_type
primary_body
target_body_or_region
start_utc
peak_utc
end_utc
observer
measurements
visibility
calculation_provenance
quality_status
uncertainty_reasons
```

`quality_status` 仅允许：

```text
verified
insufficient_data
invalid
```

缺少必要角距、时刻、观测地点、星历文件或非有限数时不得标记 `verified`。

### 3.2 `RuleAssessment/v1`

这是规则引擎与视频/报告系统之间的反腐层。视频系统不得直接依赖规则引擎内部对象。至少包含：

```text
schema_version
assessment_id
event_id
rule_set_version
matched_rules
condition_states
match_status
conflict_summary
recommended_rule_id
provisional_rule_id
evidence_references
narration_eligibility
uncertainty_reasons
```

`narration_eligibility` 只能由现有 fail-closed evidence resolver 决定。只有 `status=citable` 的 primary passage 才能进入 `classical_quote`。`candidate_only`、`ambiguous`、`missing_evidence`、`insufficient_data` 必须保留并阻止古籍结论口播。

### 3.3 `VideoPackage/v1`

负责组合研究与制作资产，不改变其事实含义。一个包至少包含：

```text
video-package.json
astronomy.json
rule-assessment.json
evidence.json
editorial.json
script.md
shot-list.json
stellarium/show.ssc
subtitles/zh-CN.srt
render/render-manifest.json
review.json
```

所有结构化文件使用严格 canonical JSON、固定 schema version 和 SHA-256 清单。生成失败不得留下部分完成目录，不得覆盖已有包。

## 4. 科学计算约定

B9 在代码实现前冻结以下约定，后续只能通过新版本契约改变语义：

### 4.1 时间

- API 输入和持久化时刻统一使用带 `Z` 的 UTC RFC3339。
- Skyfield 内部按其 timescale 正确转换 TT/TDB；不得把 TT/TDB 字符串冒充 UTC 输出。
- 同一瞬间使用不同时区表达时，计算结果必须等价。
- 所有结果记录 timescale provider 和 leap-second 数据来源。

### 4.2 坐标与观测者

- 恒星与天体身份坐标记录 ICRS/指定参考架；视位置另存，不覆盖身份坐标。
- 黄道坐标必须记录参考平面和历元。
- 站心高度角/方位角必须与地心赤经赤纬分开。
- 观测地点记录纬度、经度、海拔和时区；经度东正西负，纬度北正南负。
- 大气折射是否启用必须显式记录，默认科学事件判断使用无折射几何值；面向观众的可见性可另有带折射展示值。

### 4.3 星历与可重复性

- 正常运行和测试不得在线自动下载星历。
- 星历文件路径由配置提供，产物只记录安全逻辑名、版本、字节数和 SHA-256，不记录机器绝对路径。
- 单元测试使用依赖注入的固定 fixture；科学黄金值不能由待测实现自行生成。

### 4.4 可见性

可见性结论至少记录：

```text
target_altitude_deg
sun_altitude_deg
moon_illumination_optional
magnitude_optional
visibility_threshold_version
visible_boolean_or_unknown
```

阈值不足或数据缺失时为 `unknown`，不得自动视为可见。

### 4.5 误差与容差

每类事件必须在 fixture manifest 中声明：

```text
time_tolerance_seconds
angular_tolerance_arcsec_or_deg
reference_source
reference_frame
ephemeris_version
```

不得为使测试通过而在代码中临时放宽容差。

## 5. 中国星官映射

B9 不采用“离哪个星最近就属于哪个星官”的通用规则。映射使用版本化目录，至少包含：

```text
modern_object_id
traditional_star_id
asterism_id
canonical_chinese_name
aliases
catalog_epoch
reference_coordinates
source
mapping_method
confidence
editorial_status
```

映射状态：

```text
verified_identity
verified_membership
region_only
ambiguous
unresolved
```

只有 `verified_identity` 或经审核的 `verified_membership` 可以进入明确星名口播。`region_only` 必须使用“位于某星官区域附近”等受限措辞；`ambiguous` 和 `unresolved` 只能作为研究候选。

## 6. 古籍检索与规则评估

继续复用现有正式顺序：

```text
official Qdrant structured_recall
→ official Qdrant primary_evidence
→ 仅当官方 primary 健康且为空时 filesystem fallback
```

所有原文引用继续验证：source、book、locator、page、paragraph、heading、anchor 和 hash。Pending candidate overlay 只能进入研究线索，不得成为 `classical_quote`。

B9 只为垂直样片查询和评估必要规则。若 2026-07-21 主题没有经过审核的古籍规则，样片仍可讲述天文学事实和历史背景，但必须省略古籍占断，并在 `RuleAssessment/v1` 中保持 `candidate_only` 或 `insufficient_data`。

## 7. 声明分类与编辑边界

每个口播片段必须且只能属于一种类型：

```text
astronomy_fact
classical_quote
historical_context
modern_interpretation
production_instruction
```

规则：

- `astronomy_fact` 必须引用 `AstronomyEvent/v1` 字段。
- `classical_quote` 必须绑定 `RuleAssessment/v1` 中的 citable evidence。
- `historical_context` 必须注明来源类型，不能伪装成逐字引文。
- `modern_interpretation` 必须显示“现代文化转译”披露。
- “开口破局”固定属于 `modern_interpretation`，`classical_quote=false`。
- 禁止确定性命运承诺、恐吓性表达和把现代行动建议归因于天体强制作用。

## 8. 垂直样片数据流

```text
固定输入日期、地点和候选主题
→ Skyfield 计算 AstronomyEvent/v1
→ 版本化中国星官目录映射
→ 两阶段 KB 检索与 fail-closed 引用解析
→ 现有规则引擎执行并投影 RuleAssessment/v1
→ 约束模板编译声明分类口播
→ 生成最小 shot list 和 Stellarium .ssc
→ 生成 SRT 与最小 FFmpeg 预览命令
→ 原子写入 VideoPackage/v1
→ 人工审核四个维度
```

人工审核维度：

```text
astronomy
classical_evidence
editorial
render
```

B9 的 `preview.mp4` 可以无配音；`final.mp4` 不属于 B9 完成条件。

## 9. Stellarium 和媒体边界

Stellarium 只负责可视化，不能作为科学事实唯一来源。`.ssc` 必须使用与 `AstronomyEvent/v1` 相同的 UTC、地点和天体 ID，并记录 Stellarium 版本和脚本 hash。

普通 CI 只验证：

- `.ssc` 语法模板和允许命令；
- 目标、时间、地点一致性；
- 路径约束；
- 截图清单完整性。

实际启动 Stellarium、截图和视觉检查只在本地或自托管 macOS 门禁执行。FFmpeg 在 B9 只提供一条固定 `1080x1920` 最小预览路径，不建设通用媒体编排框架。

## 10. 测试分层

B9 使用以下门禁：

```text
G0 Governance
G1 Contract/schema
G2 Scientific golden/property/metamorphic
G3 Corpus/retrieval/citation
G4 RuleAssessment projection
G5 Hermetic vertical E2E
G6 Local Stellarium/FFmpeg smoke
G7 Package/review/release verification
```

重点测试：

- 属性测试覆盖经纬度边界、UTC、闰日、非有限数、负时长、路径穿越和字幕时间单调。
- 科学黄金 fixture 记录独立来源、参考架、星历版本、预期值、容差和 hash。
- 变形测试证明时区等价、地点变化只影响站心量、重复执行结构化产物字节一致。
- 负向黄金集覆盖标题命中、词序反向、重复全文、候选卡、多处 anchor 和缺失 hash。
- mutation testing 优先覆盖 citation、claim classification、publish gate、path confinement 和 RuleAssessment 状态。

## 11. 变更控制

B9 进入实现后：

1. 三个 v1 契约语义冻结；变化通过 `/v2`，不原地重解释。
2. 新发现的全书规则需求进入 B10/B11 backlog。
3. 只有 Critical 或 Important 设计缺陷允许修改 B9 scope。
4. 不追加自动配音、批量扫描、通用模板或自动发布。
5. 黄金 fixture 只能通过显式批准流程更新，并保留 before/after、原因和审核记录。
6. 规划 PR 与实现 PR 分离；规划 PR 合并后从新的 stable HEAD 创建实现分支。

## 12. 完成标准

B9 完成必须同时满足：

- 三个 v1 契约有严格 schema、兼容策略和测试；
- 2026-07-21 研究包可重复生成；
- 天文学、星官映射、证据和现代转译边界可审计；
- `.ssc` 和 SRT 生成且通过 hermetic 测试；
- 本地 Stellarium/FFmpeg 生成一个可查看的竖屏预览；
- 未审核或候选证据不进入古籍结论口播；
- 所有结构化资产有确定性 hash；
- 所有 required CI 和独立 review 通过；
- 没有自动发布行为。