# Spark 分布式摄取阶段提示词

```text
请为 GeoTrack 增加真实的 HDFS + Spark 摄取入口，同时保留无 PySpark 时可运行的本地演示入口。

Spark 作业读取本地 glob 或 hdfs:/// URI 下的 GeoLife PLT 文件，跳过 6 行头部，解析 GMT 时间、经纬度、海拔，将 -777 海拔转为 NULL，过滤非法坐标和连续重复点，并写入按 user_id 分区的 Parquet。输出字段为 user_id、trajectory_id、seq、timestamp、latitude、longitude、altitude_m。

增加质量摘要 JSON，至少包括 valid_points、trajectory_count、user_count 和输出路径；增加 Hadoop 客户端脚本将原始目录上传到 hdfs:///geotrack/raw/Data。脚本必须延迟导入 PySpark，让本地测试环境可以给出清晰提示而不是导入崩溃。
```

对应实现：`jobs/spark_distributed.py`、`scripts/hdfs_ingest.ps1`。
