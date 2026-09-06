# Spec 003 · HDFS 与 Spark 数据链路

**Status**: Implemented  
**Owner**: GeoTrack 小组  
**Dependencies**: Spec 001、Spec 002  
**Target commit**: `df576ea`

## Context

课程要求体现大数据处理层。全量 GeoLife 数据用于证明规模，网页使用北京和高密度轨迹子集保证演示流畅。系统需要同时支持真实 Spark/HDFS 路径和无 PySpark 时的本地替代路径。

## Goals

- 约定 HDFS raw、curated Parquet 和服务结果的目录。
- 提供延迟导入 PySpark 的分布式入口，便于本机测试。
- 让批处理输出可重复、可追踪并可导入数据库。

## Non-goals

- 不在网页请求线程中执行 Spark 作业。
- 不把本地 Spark 适配器宣称为已经完成的多节点性能验证。

## Requirements

### R-003-01 HDFS 布局

原始 PLT SHALL 放在 `hdfs:///geotrack/raw/Data`；清洗后的点 SHALL 写入 `hdfs:///geotrack/curated/points`，按 `user_id` 分区；质量摘要 SHALL 单独保存。

### R-003-02 Spark 输入输出

`jobs/spark_distributed.py` SHALL 支持本地 glob 或 `hdfs:///` URI，读取 PLT，输出字段为 `user_id`、`trajectory_id`、`seq`、`timestamp`、`latitude`、`longitude`、`altitude_m` 的 Parquet。

### R-003-03 质量与幂等

输出 SHALL 使用 overwrite 或明确的批次目录，避免重复运行产生重复分区；质量摘要至少包含 `valid_points`、`trajectory_count`、`user_count` 和输出路径。

### R-003-04 备用路径

没有 PySpark 时，`jobs/run_pipeline.py` SHALL 继续生成相同业务数据契约；分布式脚本 SHALL 给出清晰安装/运行提示。

## Scenarios

### Scenario: Docker/Spark 批处理

- Given HDFS、Spark Master 和 Worker 已启动。
- When 执行 Spark submit。
- Then raw PLT 被读取，Parquet 按用户分区写入，质量摘要可被后续加载器读取。

### Scenario: 本地备用

- Given 本机没有 PySpark。
- When 执行 `python jobs/run_pipeline.py`。
- Then 本地 JSON 演示结果生成，且前端可以刷新读取。

## Contracts

相关入口为 `scripts/hdfs_ingest.ps1`、`jobs/spark_distributed.py`、`jobs/spark_pipeline.py` 和 `docker-compose.yml` 的 `spark-submit` profile。

## Acceptance

- [x] 分布式脚本延迟导入 PySpark。
- [x] `python -m py_compile jobs/spark_distributed.py` 通过。
- [ ] 在教师指定机器上完成 HDFS/Spark 实际启动记录并填入报告。

## Risks and traceability

不同 Hadoop 镜像的 Java、权限和路径约定可能不一致；报告必须区分“架构已实现”和“本机实际跑通”的证据。对应 Spec 005 和 Spec 008。
