# Serving 表加载阶段提示词

```text
请为 GeoTrack 增加一个幂等的 PostGIS/MobilityDB 服务表加载器。输入是 data/processed/demo.json，按 trajectory_id、seq 作为冲突键写入 trajectories 和 trajectory_points；将轨迹 LineString 写入 geom，将热点中心和半径写成 4326 几何，将 temporal_patterns 的 hourly_profile 写入 JSONB。每次批处理使用 run_id 记录结果版本。提供 --dry-run，只统计待写入的轨迹点、轨迹、热点和模式数量，不连接数据库。
```

对应实现：`jobs/load_serving_tables.py`。
