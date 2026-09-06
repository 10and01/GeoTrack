# GeoTrack 分阶段 Spec

本目录采用 OpenSpec / GitHub Spec Kit 风格记录每个里程碑的可审查规格。Spec 是实现前的行为契约，需求规约回答“系统要解决什么问题”，设计规约回答“系统如何组织”，Spec 则把一个阶段拆成可执行、可验证、可追踪的变更。

## 文件约定

每个 Spec 至少包含以下字段：

- `Status`：Draft、Accepted、Implemented 或 Superseded。
- `Owner`、`Dependencies`、`Target commit`：说明责任、依赖和 Git 交付点。
- `Context`、`Goals`、`Non-goals`：限定问题边界。
- `Requirements`：使用 SHALL / SHOULD / MAY 的可测试条款。
- `Scenarios`：用 Given / When / Then 描述正常、空数据和失败路径。
- `Contracts`：写清输入、输出、接口、目录或数据库结构。
- `Acceptance`：对应命令、测试或人工演示步骤。
- `Risks and traceability`：说明风险、课程要求映射和后续变更。

## 阶段索引

| Spec | 阶段 | 主要交付 |
| --- | --- | --- |
| [001-foundation](001-foundation.md) | 项目初始化与四层架构 | 仓库、目录、合规边界 |
| [002-plt-parser](002-plt-parser.md) | GeoLife PLT 解析 | 标准化轨迹点、质量规则 |
| [003-spark-pipeline](003-spark-pipeline.md) | HDFS / Spark 数据链路 | raw、curated、Parquet、质量摘要 |
| [004-mining](004-mining.md) | 停留点、热点、时段模式 | DBSCAN、KMeans、解释字段 |
| [005-serving](005-serving.md) | PostGIS / MobilityDB 服务层 | 表、索引、版本化载入 |
| [006-api-jobs](006-api-jobs.md) | FastAPI 与后台任务 | 查询契约、job_id、错误状态 |
| [007-frontend](007-frontend.md) | React 交互层 | 地图、图表、筛选、响应式状态 |
| [008-acceptance](008-acceptance.md) | 课程验收与交付 | 测试、报告、提示词、演示 |
| [009-full-data](009-full-data.md) | 全量数据可复现处理路径 | 有界内存 manifest、Spark Parquet ingest、全量/演示隔离 |

## 变更流程

1. 开始阶段前先创建或更新对应 Spec，标记为 `Draft`。
2. 实现、测试和人工演示完成后，将状态改为 `Implemented`，填写实际提交号。
3. 若需求改变，保留旧 Spec，新增修订 Spec 或在变更记录中说明原因，避免重写历史。
4. 每个阶段至少产生一个语义化 Git 提交，并在 Prompt 文件中记录实际使用的提示词。

