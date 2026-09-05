# API 与容器化阶段提示词

## 目标

在已有 GeoTrack 四层架构 MVP 上补齐课程验收所需的查询契约，并让 React 前端可以通过 Docker Compose 启动。

## Vibe Coding 提示词

```text
请继续完善 GeoTrack 课程项目。保持 React + ECharts + Leaflet、FastAPI、PostgreSQL/PostGIS/MobilityDB、HDFS + Spark 四层架构和本地 demo 回退机制。

1. 检查 docker-compose.yml 中每个服务是否都有可构建或可拉取的入口。前端使用 node:20-alpine，依据 package-lock.json 执行 npm ci，并监听 0.0.0.0:5173。原始 GeoLife 数据只能以只读挂载提供给批处理，不能 COPY 进镜像。
2. 轨迹查询支持 user_id、start、end、limit、offset 和 west/south/east/north 边界框；边界框经度纬度范围非法时返回 422。
3. 热点查询支持 user_id、start、end、west/south/east/north、eps、minPts、min_users 和 limit。默认参数读取预计算服务结果；调整 eps、minPts 或筛选条件时，对当前演示子集重新执行停留点提取和 DBSCAN，保持响应 JSON 与预计算结果一致。
4. 为新增过滤和参数添加 API 回归测试，同时保持原有健康检查、聚类结构和异步任务测试通过。
5. 更新 docs/design.md、README.md 或对应提示词，说明默认参数、坐标系、分页语义和 Docker 运行方式。
```

## 验收记录

- 前端生产构建：`npm run build`。
- Python 回归测试：`python -m unittest discover -s tests -v`。
- Compose 配置检查：`docker compose config`。
- Git 提交应包含提示词、测试和容器入口，原始数据继续由 `.gitignore` 排除。
