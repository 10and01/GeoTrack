# Spec 004 · 停留点、热点与时段模式挖掘

**Status**: Implemented  
**Owner**: GeoTrack 小组  
**Dependencies**: Spec 002、Spec 003  
**Target commit**: `6bc21a1`

## Context

第一版需要可解释、可答辩的挖掘结果。停留点是热点分析的中间实体，热点使用米制 Haversine 距离的 DBSCAN，用户模式使用按用户聚合的 24 小时出行向量。交通方式标签覆盖不完整，因此不纳入第一版验收。

## Goals

- 以固定参数生成可解释的停留点和热点摘要。
- 输出用户模式的中心特征、样本数和命名依据。
- 让参数可由批处理或后续 API 覆盖。

## Non-goals

- 不把聚类标签武断解释成“通勤型”等未经验证的语义。
- 不用经纬度欧氏度量替代米制距离。

## Requirements

### R-004-01 停留点

默认停留半径 SHALL 为 200m，最短持续时间 SHALL 为 20 分钟，时间断点 SHALL 为 30 分钟。输出 SHALL 包含用户、轨迹、起止时间、持续秒数、中心坐标和覆盖半径。

### R-004-02 DBSCAN

热点默认 `eps=500m`、`minPts=3`。每个热点 SHALL 输出中心、覆盖范围、访问次数、独立用户数、平均停留时间、峰值小时、工作日比例和算法名。

### R-004-03 时段模式

模式特征 SHALL 至少包括轨迹数、总距离、总持续时间、平均速度、停留次数、早晚高峰比例、夜间比例、工作日/周末比例和 24 小时分布。KMeans 默认 `k=3`、`seed=42`。

### R-004-04 解释

聚类标签 SHALL 根据中心特征自动生成，并在报告中说明峰值小时、距离、时长和工作日比例等命名依据；结果 SHALL 允许显示原始 `cluster_id`。

## Scenarios

### Scenario: 固定区域停留

- Given 多个点在 200m 内持续 20 分钟。
- When 执行停留点提取。
- Then 输出一个停留点，中心为点集均值，半径覆盖所有点。

### Scenario: 两个热点

- Given 两组相距超过 `eps` 的人工停留点。
- When 执行 DBSCAN。
- Then 识别两个聚类，不把两组连接成一个热点。

### Scenario: 小样本 KMeans

- Given 输入用户数少于 3。
- When 执行 KMeans。
- Then 实际 k 自动限制为样本数，输出样本数与输入一致。

## Contracts

算法实现位于 `jobs/geotrack_core.py`。距离单位为米，输出 JSON 时间为 UTC，热点几何为 GeoJSON Point，前端可使用 `radius_m` 绘制演示范围。

## Acceptance

- [x] Haversine、停留点、DBSCAN 和轨迹几何测试通过。
- [x] 默认演示结果显示热点与模式中心字段。
- [ ] 全量 Spark MLlib KMeans 运行记录待在课程机器补充。

## Risks and traceability

当前本地演示核心 KMeans 适配器为轻量实现，正式报告需明确 Spark MLlib 是目标分布式实现，不能把本地小样本运行时间外推为全量性能。对应 Spec 003、005、007。
