# 全量数据运行记录（2026-09-06）

## 本地有界内存扫描

命令：

```powershell
python jobs/full_summary.py --data-root "Geolife Trajectories 1.3/Data" --output data/processed/full-manifest.json
```

真实结果：

| 指标 | 数值 |
| --- | ---: |
| 用户数 | 182 |
| PLT 文件/轨迹数 | 18,670 |
| 原始行数 | 24,876,978 |
| 有效点数 | 24,751,613 |
| 非法点数 | 1 |
| 连续重复点数 | 125,364 |
| 30 分钟时间断点 | 11,841 |
| 总距离 | 1,292,668,161.42 m |
| 时间范围 | 2000-01-01T23:12:19Z — 2012-07-27T08:31:20Z |

扫描逐文件处理，不把全量点保留在内存，也不产生点级 JSON。manifest 只作为本地证据，因 `.gitignore` 规则不会上传到 GitHub。

## Spark/HDFS 路径

`jobs/spark_distributed.py` 支持 `hdfs:///geotrack/raw/Data/*/Trajectory/*.plt` 输入，输出按 `user_id` 分区的 Parquet 和 quality 摘要。当前 Windows 会话 Docker daemon 未启动，因此 HDFS/Spark 实际运行仍待目标机验证；不能将本地扫描结果冒充分布式性能证据。

## 与演示数据的口径

网页继续读取 `data/processed/demo.json`（当前 60,000 点、72 条轨迹），以满足地图和详情交互的响应目标。全量结果应通过 Parquet → Spark 挖掘 → PostGIS/MobilityDB 预计算服务表进入 API，不直接加载到浏览器。
