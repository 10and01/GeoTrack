# Spec 002 · GeoLife PLT 解析与质量规则

**Status**: Implemented  
**Owner**: GeoTrack 小组  
**Dependencies**: Spec 001  
**Target commit**: `dcda816`

## Context

GeoLife Trajectories 1.3 按用户目录保存 `.plt` 文件。文件前 6 行是头部，数据行包含纬度、经度、未使用字段、海拔英尺、日期、时间和采样标志。后续距离、停留点和聚类都依赖统一、可排序的轨迹点。

## Goals

- 将每个 PLT 文件转换为稳定的标准化点记录。
- 生成轨迹摘要和可解释的数据质量指标。
- 对脏数据、重复点和时间断点给出确定规则。

## Non-goals

- 不在解析阶段推断交通方式。
- 不把标签文件当作所有用户都有的真值数据。

## Requirements

### R-002-01 文件读取

解析器 SHALL 遍历 `<user>/Trajectory/*.plt`，跳过前 6 行，并将文件名与用户目录组合成稳定 `trajectory_id`。

### R-002-02 字段

每个有效点 SHALL 包含 `user_id`、`trajectory_id`、`seq`、`timestamp`、`latitude`、`longitude`、`altitude_m`。日期时间 SHALL 按数据集说明解释为 GMT/UTC。

### R-002-03 清洗

非法经度或纬度 SHALL 被丢弃；海拔 `-777` SHALL 转为 NULL；同一轨迹中连续相同时间、纬度和经度的点 SHALL 只保留一个；结果 SHALL 按时间排序并重新编号。

### R-002-04 断点

相邻有效点时间间隔超过 30 分钟 SHALL 计为时间断点，并在后续轨迹分段或停留点计算中断开窗口。

### R-002-05 质量报告

每批次 SHALL 输出有效点数、非法点数、连续重复点数、时间断点数、轨迹数、停留点数、时间范围和总距离。

## Scenarios

### Scenario: 正常 PLT 行

- Given 行包含合法坐标、日期、时间和海拔。
- When 解析该行。
- Then 时间为带 UTC 时区的 ISO 时间，海拔转换为米，序号连续。

### Scenario: 缺失或非法值

- Given 行列数不足、坐标越界或日期格式错误。
- When 解析该行。
- Then 跳过该行并累计质量计数，批处理继续处理其他文件。

### Scenario: 断点

- Given 相邻点间隔为 31 分钟。
- When 构造停留窗口。
- Then 前后两段不被当成一次连续停留。

## Contracts

本地入口为 `python jobs/run_pipeline.py --data-root <path> --output <path>`；Spark 入口复用同一字段契约。JSON 中 `geometry` 为 `[longitude, latitude]` 顺序，避免与 Leaflet `[latitude, longitude]` 混淆。

## Acceptance

- [x] 解析器跳过 6 行头部。
- [x] GMT、`-777`、非法坐标、重复点和断点规则有单元测试或质量字段。
- [x] 重复运行同一输入产生相同业务字段。

## Risks and traceability

官方点数与当前本地演示子集点数必须同时展示，不能把 60,000 点演示数据描述成全量处理结果。对应 `tests/test_core.py` 和 Spec 003、004。
