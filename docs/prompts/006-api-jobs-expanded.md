# Prompt 006 · FastAPI 查询与后台任务（工程版）

## 提示词

```text
请阅读 docs/specs/006-api-jobs.md、docs/design-v2.md 和现有 API。保持旧接口兼容，在边界增加稳定查询契约。

轨迹接口支持 user_id、start、end、limit、offset、west/south/east/north；热点接口支持 user_id、start、end、min_users、eps、minPts 和相同边界框。limit 最大 200，offset 从 0 开始，范围缺字段或倒置返回 422，不存在实体返回 404。

默认参数读取预计算结果；自定义 DBSCAN 参数或全量挖掘通过后台 job_id 执行。任务状态至少 queued/running/completed/failed，返回创建、开始、结束时间、message、error 和结果摘要。HTTP 请求不得等待全量计算。

为正常查询、时间筛选、bbox、分页、非法范围、任务失败和 demo 回退编写 API 测试。完成后说明当前是 JSON demo、PostGIS 查询还是 Spark 任务，并记录未挂载能力。
```

## 提交

提交信息使用 `feat: add filtered query and async job contract`，附上测试命令和响应样例。


## Follow-up: frontend query integration

Connect the React filters to /api/query/trajectories and /api/query/hotspots; preserve demo seed fallback, debounce hotspot parameter changes, expose loading/error/empty states, and paginate trajectory results. Record the actual commit in Spec 006 and Spec 007 after verification.
