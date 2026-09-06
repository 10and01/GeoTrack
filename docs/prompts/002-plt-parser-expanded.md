# Prompt 002 · PLT 解析与质量报告（工程版）

## 提示词

```text
请先阅读 docs/specs/002-plt-parser.md、docs/requirements-v2.md 和现有 jobs/ 代码，再实现 GeoLife PLT 解析与质量报告。

输入是 <user>/Trajectory/*.plt：跳过前 6 行，解析 latitude、longitude、altitude、date、time；日期时间按 GMT 解释。输出字段固定为 user_id、trajectory_id、seq、timestamp、latitude、longitude、altitude_m。

规则：非法坐标丢弃；海拔 -777 转 NULL；连续相同时间/坐标只保留一个；结果按时间排序并重新编号；相邻点间隔超过 30 分钟计为断点并切分后续窗口。每批输出有效点、非法点、重复点、断点、轨迹数、停留点数、时间范围和距离。

实现必须支持小样本限制参数、幂等写出和本地无数据库运行。不要把标签文件当作全量真值，也不要上传原始数据。为头部、GMT、-777、非法点、重复点、断点和已知距离编写最小测试。
```

## 输出与 Git

说明解析器函数、JSON/Parquet 字段、质量口径、测试命令和实际处理规模；提交信息使用 `feat: add GeoLife PLT parser`。
