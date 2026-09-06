# GeoTrack 设计规约（SDD Design v2）

**状态**：Accepted  
**版本**：0.2  
**需求基线**：[`requirements-v2.md`](requirements-v2.md)  
**阶段规格**：[`specs/README.md`](specs/README.md)

## 1. 架构

```text
React + ECharts + Leaflet
          │ REST JSON
          ▼
FastAPI + job coordinator
          │ SQL / spatial query
          ▼
PostgreSQL + PostGIS + MobilityDB
          │ batch output
          ▼
HDFS raw/curated + Spark
```

交互层负责筛选、地图和图表；业务层负责参数校验和任务协调；服务层负责空间/时态查询；处理层负责原始文件解析、清洗、特征工程和挖掘。

## 2. 组件和边界

| 组件 | 允许做什么 | 不应做什么 | 主要文件 |
| --- | --- | --- | --- |
| PLT parser | 读取文件、标准化字段、统计质量 | 直接访问浏览器或数据库 | `jobs/geotrack_core.py` |
| Spark job | 分布式读取、清洗、Parquet 分区 | 等待网页 HTTP 请求 | `jobs/spark_distributed.py` |
| Serving loader | upsert 服务表、写入 run_id | 上传原始数据到 Git | `jobs/load_serving_tables.py` |
| FastAPI | 查询、校验、提交和轮询任务 | 在 GET 中执行全量挖掘 | `backend/app.py` |
| React | 调 API、渲染地图/图表、显示状态 | 依赖数据库驱动或执行 DBSCAN | `frontend/src/` |

## 3. 数据契约

### 3.1 标准轨迹点

```json
{
  "user_id": "010",
  "trajectory_id": "010_20081023025304",
  "seq": 0,
  "timestamp": "2008-10-23T02:53:04Z",
  "latitude": 39.9847,
  "longitude": 116.3184,
  "altitude_m": 150.0
}
```

### 3.2 轨迹摘要

列表响应包含 id、用户、起止时间、点数、距离、时长和 GeoJSON LineString；详情响应可以增加点数组。列表必须受 `limit`、`offset` 和空间范围限制。

### 3.3 热点摘要

热点响应包含 id、中心、半径、访问次数、独立用户数、平均停留、峰值小时、工作日比例、算法和批次标识。

### 3.4 任务状态

任务状态为 `queued`、`running`、`completed` 或 `failed`，并包含 `job_id`、类型、创建/开始/结束时间、message、error 和可选 summary。

## 4. 处理数据流

1. 本地或 HDFS 保存 `raw/Data/<user>/Trajectory/*.plt`。
2. Parser 跳过 6 行头部，解析 UTC、坐标、海拔和轨迹 id。
3. 清洗器过滤非法点、去重、排序、计算断点和质量指标。
4. Spark 将标准点写入按用户分区的 Parquet；本地入口写出 demo JSON。
5. 特征任务提取停留点、热点和用户-日期模式。
6. Loader 将摘要和挖掘结果 upsert 到 PostGIS/MobilityDB。
7. FastAPI 读取预计算表或 demo JSON；重算通过 job_id 执行。
8. React 以分页、范围和演示子集渲染地图与图表。

## 5. 数据库原则

- 所有几何为 SRID 4326；空间索引使用 GiST。
- `trajectory_points` 主键为 `(trajectory_id, seq)`。
- `trajectories` 保存 LineString、摘要和可选 MobilityDB `tgeompoint`。
- `stay_points` 保存轨迹外键、时间区间、中心和半径。
- `hotspots`、`temporal_patterns` 保存 `run_id` 和生成时间。
- Schema 初始化可重复运行；加载器使用 upsert，不删除其他批次。

## 6. API 设计

基础路由：`/api/health`、`/api/summary`、`/api/users`、`/api/trajectories`、轨迹详情、`/api/hotspots`、`/api/patterns/time`、`/api/patterns/clusters`、`/api/data-quality`、`POST /api/jobs/run` 和任务状态路由。

轨迹筛选：`user_id`、`start`、`end`、`limit`、`offset`、`west/south/east/north`。热点筛选：上述时间/用户/空间条件、`min_users`、`eps`、`minPts`。范围缺字段、经纬度越界或边界倒置返回 422；不存在的实体返回 404。

## 7. 部署模式

### 本地 demo

FastAPI 优先读取 `data/processed/demo.json`，缺失时使用 `data/demo_seed.json`；前端使用 Vite proxy。该模式用于无 Docker、数据库或 Spark 的答辩备份。

### Docker 分布式

Compose 启动 NameNode、DataNode、Spark Master、Spark Worker、PostgreSQL/MobilityDB、FastAPI 和 React。原始 GeoLife 目录只读挂载到批处理服务，不复制进镜像。Spark 资源不足时允许 local 模式，但报告必须记录实际运行模式。

## 8. 可观测性与性能

每批输出输入路径、参数、计数、质量报告、生成时间和 run_id。首页只绘制演示子集和有限轨迹；列表接口最大 200 条；全量挖掘不在 HTTP 请求线程执行；关键演示查询目标响应不超过 3 秒。

## 9. 设计决策

| 决策 | 理由 | 代价 |
| --- | --- | --- |
| 全量批处理 + 演示子集 | 同时证明规模和保证流畅 | 页面必须标注数据口径 |
| 停留/热点/时段模式优先 | 参数清晰、易解释、标签风险低 | 交通方式识别延期 |
| 预计算服务表 + job_id | 查询快且不阻塞 | 需要任务轮询和批次版本 |
| demo seed 回退 | 无基础设施仍能答辩 | 必须清楚标识 demo 模式 |

## 10. 安全与合规

原始数据、课程 PDF、`.env`、数据库密码和缓存不进入 Git。默认密码仅用于本地课堂演示；对外部署前替换凭据、限制 CORS、增加认证并重新审查数据许可。
