# 前端对接反馈 (Backend Response to Frontend)

## 1. 接口变更确认

后端已完成针对“双数据源”架构的适配改造，完全支持前端通过 `source` 参数控制数据来源。

### 1.1 详情页接口 (已更新)
- **接口地址**: `/public-info/detail/data/{dataId}`
- **新增参数**: `source` (可选)
- **逻辑说明**:
  - `source=redis`: 强制查询 Redis。若数据不存在（过期或未命中），返回 `data: null`。**不会**自动降级查询 MySQL。
  - `source=mysql`: 强制查询 MySQL。
  - **不传参数**: 执行自动降级策略（优先查 Redis，未命中则查 MySQL）。

**前端适配注意**:
- 当请求 `source=redis` 且返回 `data: null` 时，前端应在界面提示“数据已更新或不存在”，或引导用户去分类列表查找（因为热门数据有过期时间）。

### 1.2 热门列表接口
- **接口地址**: `/public-info/hot/list`
- **数据源**: 严格来自 Redis。
- **说明**: 仅返回最新的热门数据（Top 20）。

### 1.3 分类数据接口
- **接口地址**: `/public-info/category/data`
- **数据源**: 严格来自 MySQL。
- **参数**: 接口已默认走数据库查询。前端传递 `source=mysql` 参数会被后端忽略（但不会报错），后端保证返回数据库全量归档数据。

## 2. 给前端的建议

1. **详情页 404/Null 处理**:
   由于热门数据（Redis）具有时效性（如7天过期），用户点击旧的热门链接可能会遇到 `source=redis` 但数据已过期的情况。
   - **建议**: 若 `source=redis` 返回 null，前端可选择自动重试（不带 source 参数）或显示友好的“内容已归档”提示。

2. **参数传递**:
   - 确认前端在路由跳转时正确传递了 query 参数 `?source=redis` 或 `?source=mysql`。

## 3. 问题排查
针对 `FRONTEND_REQ_SPEC.md` 中提到的“部分详情页无法加载”问题：
- 后端已修复 `RedisHotDataService` 中的数据转换 bug（之前因字段映射问题导致转换失败返回 null）。
- 现在再次测试 `source=redis` 应能正常获取数据。

请前端同学根据以上信息进行联调验证。
