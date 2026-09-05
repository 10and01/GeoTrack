# GeoTrack

基于 GPS 轨迹的用户出行模式挖掘与热点区域分析系统。

本项目按“大数据综合实践”课程的四层架构实现：

```text
React + ECharts + Leaflet
        ↓
FastAPI 业务服务
        ↓
PostgreSQL / PostGIS / MobilityDB
        ↓
HDFS + Spark 批处理
```

## 数据集

项目使用 Microsoft Research Asia 的 GeoLife Trajectories 1.3。当前发行版包含 182 个用户、18,670 条轨迹，官方统计约 24,876,978 个轨迹点。数据仅用于课程学习、非商业研究与演示，不应提交到 Git 仓库或重新分发。

将本地数据集放置在：

```text
./Geolife Trajectories 1.3/Data
```

也可以通过 `GEOTRACK_DATA_ROOT` 指定路径。

## 本地快速启动

后端不依赖数据库也可以启动：它会优先读取 `data/processed/demo.json`，不存在时使用内置演示数据。安装依赖后运行：

```powershell
uv pip install -r requirements.txt
& .\scripts\run_backend.ps1
```

另开终端运行前端：

```powershell
cd frontend
npm install
npm run dev
```

访问 <http://localhost:5173>。

## 数据流水线

```powershell
python jobs/run_pipeline.py --data-root ".\Geolife Trajectories 1.3\Data" --max-trajectories 120 --max-points 60000
```

完整数据处理时移除两个限制参数。Spark 版本的提交入口为 `jobs/spark_pipeline.py`，Docker 环境入口为：

```powershell
docker compose up -d
docker compose run --rm spark-submit
```

## 课程交付物

- `docs/requirements.md`：需求规约
- `docs/design.md`：设计规约
- `docs/prompts/`：Vibe Coding 提示词记录
- `sql/001_schema.sql`：PostGIS/MobilityDB 服务表
- `docker-compose.yml`：四层本地演示环境

课程要求 2–4 人分组；如果以单人形式提交，请先取得教师书面确认。

