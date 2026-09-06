# Prompt 003 · HDFS 与 Spark 数据链路（工程版）

## 提示词

```text
请阅读 docs/specs/003-spark-pipeline.md。为 GeoTrack 增加可在 Docker/Spark 集群运行的 PLT 摄取入口，同时保留无 PySpark 时的本地入口。

Spark 作业必须支持本地 glob 和 hdfs:/// URI，延迟导入 PySpark；读取 PLT 时复用 Spec 002 的清洗规则，输出按 user_id 分区的 Parquet，字段为 user_id、trajectory_id、seq、timestamp、latitude、longitude、altitude_m。输出质量摘要至少包含 valid_points、trajectory_count、user_count、输入和输出路径。

增加 hdfs 客户端上传脚本，约定 hdfs:///geotrack/raw/Data 和 hdfs:///geotrack/curated/points。不要把 local 适配器描述成多节点性能结果；README 和报告要区分架构实现与实际运行证据。
```

## 验收与提交

运行 `python -m py_compile`、Spark image 中的 `spark-submit` 或本地备用入口，检查 Parquet 字段和分区；提交信息使用 `feat: add distributed spark ingestion`。
