# GeoTrack 设计规约

## 四层架构

```text
React / ECharts / Leaflet
          ↓ JSON REST
FastAPI / job coordinator
          ↓ SQL + spatial index
PostGIS + MobilityDB serving tables
          ↓ Spark submit
HDFS raw + Parquet curated data
```

## 数据流

PLT → parser → cleaned point records → trajectory summaries → stay points → DBSCAN hotspots / temporal clusters → serving tables → REST API → UI.

## 算法参数

- Haversine 地球距离；半径 200m；最短停留 20min；时间断点 30min。
- DBSCAN `eps=500m`, `minPts=3`（小样本演示）；全量运行时由任务参数覆盖。
- 用户模式向量为 24 小时出行频率，KMeans `k=3`, `seed=42`。

## API

核心路由见 `backend/app.py`。所有返回值为 JSON；几何采用 GeoJSON，时间采用 UTC ISO-8601。

## 失败与回退

- 没有处理结果时读取 `data/demo_seed.json`，保证 UI 可演示。
- 没有 FastAPI 依赖时启动命令应给出安装提示。
- Docker/HDFS 不可用时，使用本地 Spark 入口保持同样的输出契约。

