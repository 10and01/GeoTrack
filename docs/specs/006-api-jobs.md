# Spec 006 · FastAPI 查询与后台任务

**Status**: Implemented (local serving payload; database query performance pending)
**Owner**: GeoTrack 小组
**Dependencies**: Spec 005
**Target commit**: `0b5cb39` (filter routes mounted); frontend integration `WORKTREE`

## Context

前端需要稳定的 JSON 查询契约，重计算不能阻塞 HTTP 请求。默认演示读取本地预计算 JSON，数据库可用后切换到服务表。参数校验必须在 API 边界完成，错误响应要能被前端展示。

## Goals

- 固化健康、总览、用户、轨迹、热点、模式、质量和任务接口。
- 支持时间、用户、边界框、分页以及热点 `eps`/`minPts` 参数。
- 用 `job_id` 查询异步批处理状态。

## Non-goals

- 不在 GET 请求中执行全量 Spark 作业。
- 不把临时演示字段伪装成数据库已写入的真实结果。

## Requirements

### R-006-01 基础接口

API SHALL 提供 `/api/health`、`/api/summary`、`/api/users`、`/api/trajectories`、`/api/trajectories/{trajectory_id}`、`/api/hotspots`、`/api/patterns/time`、`/api/patterns/clusters`、`/api/data-quality`、`POST /api/jobs/run` 和 `/api/jobs/{job_id}`。

### R-006-02 轨迹筛选

轨迹查询 SHALL 支持 `user_id`、`start`、`end`、`limit`、`offset` 和 `west/south/east/north`。`limit` 最大 200，边界框缺字段或 west/east、south/north 倒置 SHALL 返回 422。

### R-006-03 热点筛选

热点查询 SHALL 支持时间、用户、边界框、`min_users`、`eps` 和 `minPts`。默认 500m/3 使用预计算服务结果；自定义参数 SHALL 走可控的小样本重算或后台任务。

### R-006-04 任务状态

任务状态 SHALL 至少包括 `queued`、`running`、`completed`、`failed`，并返回创建、开始、结束时间、提示信息和错误详情。HTTP 请求 SHALL 在提交任务后立即返回 job_id。

## Scenarios

### Scenario: 正常查询

- Given demo JSON 或服务表可用。
- When 请求 `/api/hotspots?limit=10&min_users=20`。
- Then 返回不超过 10 条按访问量排序的热点 JSON。

### Scenario: 非法空间范围

- Given `west=117&east=116`。
- When 请求轨迹或热点接口。
- Then 返回 422 和可读错误，不执行查询。

### Scenario: 批处理失败

- Given数据目录不存在。
- When POST `/api/jobs/run` 后轮询 job_id。
- Then 状态转为 `failed`，错误字段说明目录问题，前端仍可保留旧结果。

## Contracts

时间为 UTC ISO-8601；轨迹几何为 GeoJSON LineString；响应不得把完整全量点集一次性返回，详情接口和分页负责控制负载。

## Acceptance

- [x] 健康、总览、热点、模式、质量和任务结构测试通过。
- [x] 过滤路由挂载后补充边界框、分页和自定义 DBSCAN API 测试。
- [ ] 数据库模式下补充 SQL 查询性能记录。

## Risks and traceability

自定义热点重算对演示子集可接受，对全量数据必须转为后台 Spark 作业；报告要展示预计算查询和重计算任务的边界。对应 Spec 005、007。
