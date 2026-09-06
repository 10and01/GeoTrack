# Spec 007 · React 地图与图表交互层

**Status**: Implemented
**Owner**: GeoTrack 小组
**Dependencies**: Spec 001、Spec 004、Spec 006
**Target commit**: `WORKTREE` (query filter integration)

## Context

课程演示需要在五分钟内说明数据规模、轨迹清洗、热点算法、模式聚类和任务状态。地图一次加载全部点会卡顿，因此首页使用北京高密度演示子集，轨迹明细使用分页和选中轨迹。

## Goals

- 提供总览、轨迹探索、热点分析、出行模式、任务质量五个视图。
- 让地图点击、列表选择、滑块筛选和图表联动可直接演示。
- 覆盖加载中、空数据、API 错误、窄屏和后端回退。

## Non-goals

- 不在浏览器执行全量 DBSCAN 或 KMeans。
- 不同时渲染全部 GeoLife 轨迹点。

## Requirements

### R-007-01 总览

首页 SHALL 展示官方用户数、轨迹数、点数、时间范围、累计距离、质量摘要和北京地图。

### R-007-02 轨迹探索

用户选择、日期过滤、轨迹列表和选中详情 SHALL 更新地图线、点数、距离和持续时间。

### R-007-03 热点分析

页面 SHALL 展示 DBSCAN 热点、最少用户筛选、热点排名、点击详情、峰值小时和停留时长。

### R-007-04 模式分析

页面 SHALL 展示 24 小时分布、工作日/周末说明、聚类中心特征和用户钻取入口。

### R-007-05 状态

所有页面 SHALL 具备 loading、empty、error、窄屏状态；API 失败时 SHALL 显示 demo 模式而不是静默使用错误数据。

## Scenarios

### Scenario: 地图选择热点

- Given 热点列表和地图均已加载。
- When 点击列表行或地图热点。
- Then 两处高亮同步，右侧详情显示用户数、访问次数、峰值小时和停留时长。

### Scenario: 移动端

- Given viewport 宽度约 390px。
- When 打开任一视图。
- Then 侧边栏可折叠，表格可横向滚动，卡片不溢出视口。

### Scenario: API 不可用

- Given FastAPI 关闭。
- When 刷新页面。
- Then 使用种子数据并展示可识别的 demo 数据模式。

## Contracts

实现位于 `frontend/src/`，地图使用 Leaflet，图表使用 ECharts，API 入口为 `frontend/src/lib/api.js`。前端不依赖数据库驱动。

## Acceptance

- [x] `npm run build` 成功。
- [x] 已验证桌面端、390×844 窄屏、热点筛选、图表和任务提交。`/api/query/trajectories` 与 `/api/query/hotspots` 已接入轨迹/热点页面。
- [ ] 课程现场网络断开时使用备份视频完成演示。

## Risks and traceability

地图底图网络不可用时应准备截图或离线演示说明；图表包较大时保留 Vite 分包配置。对应 Spec 006 和 Spec 008。
