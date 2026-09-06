# GeoTrack 全量数据接入运行手册

## 处理链路

```text
GeoLife PLT（只读）
  → full_summary.py（质量 manifest）
  → spark_full_pipeline.py（按用户/年份分区 Parquet）
  → load_full_serving.py（COPY 到 staging）
  → 行数与质量校验
  → current_run 发布指针
  → FastAPI PostGIS serving
```

全量点不会在 HTTP 请求或浏览器中一次性加载。轨迹详情默认最多返回 500 个采样点，可通过 `sample_limit` 调整到最多 2000。

## 本地/Spark 批处理

```powershell
python jobs/full_summary.py --data-root "Geolife Trajectories 1.3/Data" --output data/processed/full-manifest.json
spark-submit jobs/spark_full_pipeline.py `
  --input "Geolife Trajectories 1.3/Data/*/Trajectory/*.plt" `
  --output-root data/processed/full-curated `
  --manifest data/processed/full-manifest.json
python jobs/load_full_serving.py --input-root data/processed/full-curated --manifest-uri data/processed/full-manifest.json --dsn "postgresql://geotrack:geotrack@localhost:5432/geotrack"
```

只检查 Parquet 行数而不连接数据库：

```powershell
python jobs/load_full_serving.py --input-root data/processed/full-curated --dry-run
```

## Docker profile

```powershell
docker compose --profile batch run --rm spark-submit
docker compose --profile batch run --rm full-loader
docker compose up -d api frontend
```

生产 API 使用：

```text
GEOTRACK_SERVING_BACKEND=postgres
DATABASE_URL=postgresql://geotrack:geotrack@postgres:5432/geotrack
```

未发布批次不会被 API 读取；加载失败时事务回滚，原 `current_run` 保持不变。`sql/001_schema.sql` 可重复执行，并为旧 demo 表补齐 `run_id` 字段。

## 质量门槛

加载器至少校验 points、trajectories 的 COPY 行数与 Parquet 计数；空产物直接拒绝发布。完整质量计数保存在 `batch_runs.counts/quality`，可通过 `/api/full/summary` 查看当前 `run_id` 和 `/api/full/quality` 查看质量报告。
