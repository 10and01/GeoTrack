# Spec 009 · 全量数据可复现处理路径

**Status**: Implemented  
**Owner**: GeoTrack 小组  
**Dependencies**: Spec 002、003、004、005、008  
**Target commit**: `2925e30`

## Context

GeoLife Trajectories 1.3 的本地发行版包含 182 个用户、18,670 个 PLT 文件和约 2,487 万个原始轨迹点。现有 `demo.json` 为保证浏览器流畅而限制为 60,000 点，不能作为全量处理证明。把全量点、轨迹几何和挖掘结果放进一个 JSON 会造成高内存和服务启动风险。

## Goals

- 提供逐文件、低内存的全量扫描，生成可审计 manifest。
- 保留 HDFS + Spark 的分布式 Parquet ingest 入口，并明确其运行前提。
- 让全量产物与演示子集隔离，避免 API 一次加载数千万点。
- 记录真实计数、质量指标、时间范围和下游输出位置。

## Non-goals

- 不把全量点级数据提交 GitHub。
- 不把本地逐文件扫描描述成多节点 Spark 执行。
- 不在本阶段改变前端默认演示数据或同步全量轨迹到浏览器。
- 不在 HTTP 请求线程中执行全量挖掘。

## Requirements

### R-009-01 有界内存扫描

`jobs/full_summary.py` SHALL 一次只读取一个 PLT 文件，跳过 6 行头部，按 GMT/UTC 解析时间，过滤非法坐标，将 `-777` 海拔设为 `NULL`，删除连续重复点，并累计有效点、非法点、重复点、30 分钟断点、距离和时间范围。

### R-009-02 Manifest 契约

扫描 SHALL 写出 `data/processed/full-manifest.json`，包含数据源、处理时间、处理模式、官方规模、实际计数、质量规则、时间范围、下游 Spark 路径和每个 PLT 文件摘要；不得包含点级数组。

### R-009-03 分布式 ingest

`jobs/spark_distributed.py` SHALL 支持本地 glob 或 `hdfs:///` 输入，输出按 `user_id` 分区的 Parquet，并支持质量摘要输出。Docker/Spark 不可用时，必须使用 R-009-01 的本地回退并在报告中披露。

### R-009-04 产物隔离

全量 manifest、Parquet 和质量目录 SHALL 被 `.gitignore` 忽略；demo API 继续读取 `data/processed/demo.json`，全量数据通过预计算服务表或后续批任务供查询。

### R-009-05 可重复运行

同一输入重复执行 SHALL 覆盖本次 manifest，不修改原始数据，不产生重复的 Git 或服务记录；输入不存在时以非零状态退出并给出中文错误。

## Scenarios

### Scenario: 本机无 Docker 全量扫描

- Given 本地存在 `Geolife Trajectories 1.3/Data`。
- When 执行 `python jobs/full_summary.py --data-root ... --output ...`。
- Then 生成小型 manifest，内存不会随点数线性保留，控制台打印实际计数。

### Scenario: HDFS + Spark ingest

- Given NameNode、DataNode 和 Spark 可用，原始文件已上传到 `hdfs:///geotrack/raw/Data`。
- When 提交 `spark_distributed.py`。
- Then 生成 `hdfs:///geotrack/curated/points` 的按用户分区 Parquet 与 quality 输出。

### Scenario: 输入缺失

- Given data-root 不存在或 glob 无匹配。
- When 执行全量命令。
- Then 返回非零错误；不得生成看似成功的全量统计。

## Contracts

Manifest 的 `counts` 至少包含：`user_count`、`plt_file_count`、`trajectory_count`、`valid_point_count`、`raw_row_count`、`invalid_point_count`、`duplicate_point_count`、`time_gap_segment_count`、`total_distance_m`。`time_range.start/end` 使用 UTC ISO-8601。

## Acceptance

- `python jobs/full_summary.py --data-root "Geolife Trajectories 1.3/Data" --output data/processed/full-manifest.json`
- 真实本地数据应得到 182 用户、18,670 文件/轨迹；官方点数与实际有效点数同时记录。
- `python -m unittest discover -s tests -v`
- `git diff --check`
- `docker compose config` 仅证明配置可解析，不等同于容器已启动。

## Risks and traceability

逐文件扫描适合作为无 Spark 环境的规模证据，但距离计算仍是 CPU 密集型；生产全量挖掘应使用 Spark Parquet 中间层。全量实现对应课程的大数据规模、HDFS/Spark 分布式架构和过程证据要求；演示页面继续使用有界子集以满足交互性能目标。

