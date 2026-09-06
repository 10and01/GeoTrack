# Prompt 005 · PostGIS/MobilityDB 服务层（工程版）

## 提示词

```text
请阅读 docs/specs/005-serving.md 和 sql/001_schema.sql。实现一个幂等的服务表加载流程。

将 demo JSON 的轨迹摘要和点分别 upsert 到 trajectories、trajectory_points；热点写入 center_geom、geometry、统计字段；时段模式写入 temporal_patterns 和 hourly_profile JSONB；所有挖掘结果写入 run_id。几何统一 SRID 4326，轨迹点冲突键为 trajectory_id+seq。

提供 --dry-run 检查输入文件和待写入数量，不依赖数据库包；数据库连接只在真正写入时建立。记录 DSN、run_id、计数和错误。不要删除其他批次，不要上传原始 PLT。
```

## 验收

Schema 可重复初始化；dry-run 在无数据库环境输出点/轨迹/热点/模式计数；同一输入二次载入不增加重复记录；提交信息使用 `feat: add serving table loader`。
