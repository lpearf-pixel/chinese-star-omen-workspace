# B9–B10 分层测试与黄金数据策略

## 1. 目的

B9 和 B10 同时引入科学计算、传统星官映射、古籍规则标注、内容声明和媒体渲染。仅靠现有单元测试不足以证明科学正确性、引用正确性和研究质量。本策略定义长期稳定的七层门禁、黄金数据管理、验证分工和变更控制。GOV-T03 起，普通任务以本地执行这些门禁为默认；远端/self-hosted Runner 只用于大版本合入 stable 前的最终统一验证。

## 2. 七层门禁

| Gate | 名称 | 主要目标 | 普通任务本地 | Nightly | 大版本最终 Runner |
|---|---|---|---:|---:|---:|
| G0 | Governance | 分支、台账、安全边界、禁止写旧 collection | 必须 | 可选 | 必须 |
| G1 | Contract | Schema、严格 JSON、兼容性、迁移 | 必须 | 可选 | 必须 |
| G2 | Scientific | 星历、坐标、时间、可见性、容差 | smoke | 可选 | 完整 |
| G3 | Corpus/Retrieval | passage、检索、引用与负向黄金集 | 必须 | 可选 | 完整 |
| G4 | Rule Quality | 抽取、审核、去重、冲突、覆盖率 | smoke | 可选 | 完整 |
| G5 | Hermetic E2E | 组件组合、不联网、不写正式系统 | 必须 | 可选 | 必须 |
| G6 | Renderer | Stellarium、截图、FFmpeg、视觉检查 | 按专项契约 | 可选 | 按专项契约 |
| G7 | Release | hash、manifest、审核、离线复验 | 必须 | 可选 | 必须 |

## 3. 普通任务本地门禁

普通任务目标是在本地约十分钟内给出高信号结果：

```text
Development Governance
Contract and unit tests
Hypothesis smoke profile
Scientific golden smoke
Golden retrieval and citation negatives
Rule fixture smoke
Hermetic vertical/package E2E
Release/package verifier
```

原则：

- GUI 和大型模型不得进入普通任务的默认门禁；
- 不访问真实生产服务；
- Qdrant 集成只使用 ephemeral collection；
- 测试失败不能通过吞异常、放宽断言或更新黄金文件解决。
- 不为普通提交或 PR head 调度、重试或等待 Runner；
- 过渡期内既有 GitHub workflow 若被仓库事件自动触发，其结果仅作补充信息，不是普通任务继续、完成或合并的前置条件；
- 自动触发 workflow 的迁移由 GOV-T04 单独实施，不在业务 PR 中静默修改。

## 4. Nightly 门禁

Nightly 执行高成本质量检查：

```text
full Hypothesis profiles
full scientific golden set
full corpus passage inventory
full validation rule extraction
sealed holdout release evaluation when explicitly enabled
mutation testing
long-running ephemeral Qdrant integrations
coverage and determinism scan
```

Nightly 失败不应被普通 PR 绕过。进入 release 前必须处理或正式记录阻塞。

## 5. 本地或自托管 macOS 门禁

Stellarium 和视觉媒体测试放在可控 macOS 环境：

```text
Stellarium version/capability detection
startup-script or Remote Control execution
screenshot output inventory
actual UTC/location/object verification
FFmpeg version detection
1080x1920 preview generation
manual visual review
asset hash recording
```

普通本地门禁只验证 `.ssc` 生成和命令边界，不强行运行 GUI。

## 6. 测试类型

### 6.1 单元测试

每个纯模块覆盖成功、边界、失败和严格序列化。模块不得依赖隐式网络或用户主目录。

### 6.2 属性测试

使用 Hypothesis 覆盖：

- 纬度 `[-90, 90]`、经度 `[-180, 180]`；
- 极区、日期边界、闰日和跨年；
- UTC 与时区表达；
- 非有限数、非法字符串和空值；
- 负时长和重叠字幕；
- 路径穿越、绝对路径和 Unicode 路径；
- ID 唯一性、输入顺序和 canonical JSON；
- 审核状态机非法跃迁。

普通 PR 使用较小 example 数，nightly 使用 full profile。

### 6.3 科学黄金测试

科学黄金值不得由待测实现生成。每个 fixture manifest 必须记录：

```text
authoritative_source
source_retrieved_at
observer
utc_interval
time_scale
reference_frame
ephemeris_logical_name
ephemeris_version
ephemeris_sha256
expected_values
tolerances
fixture_sha256
reviewer
```

至少覆盖：

- 月相或月面照明；
- 月/行星近合；
- 恒星附近经过；
- 地点变化下的站心高度角；
- 不可见和 unknown 可见性；
- 后续 B11 的留、逆、掩等复杂事件。

### 6.4 变形测试

必须建立不依赖单个黄金数值的关系断言：

- 同一 UTC 的不同时区表示结果相同；
- 改变地点不改变地心身份坐标；
- 改变地点应改变站心高度和方位；
- 只改变现代文案不得改变 astronomy/evidence hashes；
- 输入集合顺序变化不改变 canonical 产物；
- 同一输入重复执行结构化产物字节一致。

### 6.5 负向黄金集

古籍检索和规则测试必须包含：

- 仅标题出现；
- 查询词顺序相反；
- 简繁转换后歧义；
- 全文与分卷重复；
- pending candidate；
- 多处相同 anchor；
- 缺页码、段落、标题或 hash；
- source hash 改变；
- 同触发、不同占应；
- 不同传统不可自动合并。

目标是关键引用路径 false positive 为 0。

### 6.6 Mutation testing

优先模块：

```text
citable evidence eligibility
claim classification
RuleAssessment narration eligibility
source-change invalidation
review approval
conflict resolution
path confinement
package/release verifier
```

关键模块 mutation score 目标不低于 80%。未达到时报告 surviving mutants 和风险，不可只追求总分。

### 6.7 Hermetic E2E

E2E 使用固定 fake/in-memory adapters 和真实纯业务模块，证明：

- 不联网；
- 不启动 Stellarium/FFmpeg；
- 不调用 ingest；
- 不连接或修改 `local_kb_default`；
- 输入篡改 fail-closed；
- 没有部分产物；
- 结构化资产确定性。

## 7. 黄金数据目录

固定目录：

```text
tests/fixtures/astronomy/v1/
tests/fixtures/asterisms/v1/
tests/fixtures/evidence/v1/
tests/fixtures/video-package/v1/
tests/fixtures/rules/v2/
eval/rules/v2/development/
eval/rules/v2/validation/
eval/rules/v2/holdout/
eval/rules/v2/manifests/
```

每个目录必须有 manifest，记录 schema version、来源、hash、审核状态和适用测试。

## 8. 黄金文件更新政策

普通测试和普通命令不得重写黄金文件。更新必须：

1. 使用显式 `--approve-golden-update` 或等价专用命令；
2. 生成 before/after diff；
3. 说明更新原因、来源和容差变化；
4. 记录审核人和日期；
5. 更新 fixture manifest/hash；
6. 在 `TASKS.md` 和 `WORK_LOG.md` 记录；
7. 使用独立 PR，不能夹带无关功能。

sealed holdout expected labels 不得在普通开发命令中读取或输出。

## 9. 测试隔离

- 网络默认禁用，只有显式 integration 标记可以访问 allowlisted local service。
- 星历文件由 fixture 或配置注入，不自动下载。
- 时间使用显式输入，不依赖 `now()`。
- 随机测试保存 seed，失败可复现。
- 文件输出限制在 pytest temp 目录或调用方指定目录。
- 环境变量在测试结束后恢复。
- 外部进程通过 adapter 注入；单元测试不执行 GUI 或 shell。

## 10. 需求追踪矩阵

每个 B9/B10 task 必须维护：

```text
requirement_id
design_section
implementation_files
test_ids
fixture_ids
ci_gate
release_artifact
status
```

任务完成前必须证明每个 acceptance requirement 至少有一个直接测试或人工门禁，不接受“由其他测试顺带覆盖”的模糊声明。

## 11. Flaky 测试政策

- 测试失败首先作为真实失败处理；
- 不允许直接 rerun 后忽略；
- 若确认 flaky，立即建立稳定 issue/task，记录 seed、环境、频率和根因假设；
- 隔离仅允许有到期时间和负责人；
- release gate 不允许存在未解释的 flaky 关键测试。

## 12. 完成声明

任何阶段不得只凭测试数量宣称完成。完成证据必须包含：

```text
exact head
focused test commands and totals
related/full gate commands and totals
scientific fixture versions
coverage/evaluation reports
review findings and dispositions
workflow run IDs
merge SHA
remaining risks
```

其中 `workflow run IDs` 只对大版本 stable 最终 Runner、显式 nightly 或任务契约明确要求的专项运行必填。普通任务的 Runner 应记录为 `NOT RUN`，不能沿用旧 head 的 workflow ID 冒充当前证据。

B9 的本地视觉 smoke 和 B10 的 sealed holdout/release verification 是各自完成定义的一部分，不能用普通单元测试替代。
