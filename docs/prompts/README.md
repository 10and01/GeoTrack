# GeoTrack 分阶段 Vibe Coding Prompts

早期 `001-scaffold.md` 和 `002-mining.md` 是首次探索时使用的短提示词。本目录新增的 `*-expanded.md` 是可复用的工程版提示词，补充了上下文、输入输出、约束、验收、测试、偏差记录和 Git 要求。提交课程材料时两类文件都保留，以展示提示词逐步成熟的过程。

| 阶段 | 短版 | 工程版 |
| --- | --- | --- |
| 初始化 | `001-scaffold.md` | `001-foundation-expanded.md` |
| PLT 与质量 | `002-mining.md` | `002-plt-parser-expanded.md` |
| Spark/HDFS | — | `003-spark-pipeline-expanded.md` |
| 挖掘算法 | `002-mining.md` | `004-mining-expanded.md` |
| 服务数据库 | `005-serving-loader.md` | `005-serving-expanded.md` |
| API 与任务 | `003-api-and-container.md` | `006-api-jobs-expanded.md` |
| 前端 | — | `007-frontend-expanded.md` |
| 最终验收 | — | `008-acceptance-expanded.md` |

每个工程版 Prompt 都要求模型先阅读对应 Spec，再修改代码；完成后必须运行该阶段的最小验证并创建语义化提交。
