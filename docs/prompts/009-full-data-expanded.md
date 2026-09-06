# Prompt 009 · 全量数据路径（工程版）

## 提示词

```text
你正在维护 GeoTrack 课程项目。请先阅读 docs/specs/009-full-data.md、docs/requirements-v2.md、docs/design-v2.md、jobs/geotrack_core.py 和 jobs/spark_distributed.py。

目标：把 GeoLife Trajectories 1.3 的全量处理做成与 demo JSON 隔离的可复现路径。全量数据约 1.55 GiB、18,670 个 PLT 文件、约 2,487 万个原始点，禁止将原始数据或点级大 JSON 提交 GitHub。

请实现逐文件有界内存扫描、真实质量 manifest、Spark/HDFS Parquet ingest、full-summary/full-ingest/full-spark 命令和对应测试。遵守 PLT 跳过 6 行头、UTC/GMT、-777 海拔、非法坐标、连续重复点和 30 分钟断点规则。

不要把本地扫描冒充多节点 Spark；不要伪造 Docker/HDFS/MobilityDB 实际运行证据；全量产物必须与 demo.json 隔离。完成后运行 unittest、全量小样本、git diff --check 和 docker compose config，并创建 feat: add reproducible full data path 提交。
```

## 实际使用与偏差

- 本阶段先实现标准库全量扫描并在本地 GeoLife 目录真实运行；Spark 入口保留为 HDFS/集群执行路径。
- Docker daemon 不可用时，不宣称 HDFS、Spark Worker 或 MobilityDB 已启动。
- manifest 和 Parquet 目录被 `.gitignore` 忽略，只提交脚本、Spec、Prompt 和运行说明。
