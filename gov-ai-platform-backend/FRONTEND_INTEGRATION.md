# 前端对接指南 (Frontend Integration Guide)

本文档说明政务数据平台(Gov AI Platform)的前端对接策略，特别是 Redis 和 MySQL 混合架构下的数据读取流程。

## 1. 数据架构概览

系统采用 **冷热数据分离** 架构：
- **热点数据 (Hot Data)**: 存储在 **Redis** 中，提供极速访问。包括最新的政务信息、高频访问的详情等。
- **全量数据 (Archive Data)**: 持久化存储在 **MySQL** (`public_info` 表) 中，用于历史归档、复杂检索和兜底查询。

## 2. 对接策略

### 2.1 列表/最新数据查询
前端在展示首页、最新动态或特定分类的最新列表时，应优先使用相关 API 从 Redis 读取。

* **场景**: 首页推荐、分类最新列表
* **数据源**: Redis (`gov:data:hot`, `gov:data:new`)
* **API 接口**: `/api/public-info/list` (示例)
* **注意**: 后端 `DataSyncService` 会自动将 Redis 中的新数据同步到 MySQL，但会有短暂延迟（默认 5 分钟）。

### 2.2 历史数据/搜索/分页查询
当用户进行搜索、筛选或查看历史分页数据时，应查询 MySQL。

* **场景**: 搜索关键词、按时间筛选、翻页查看旧数据
* **数据源**: MySQL (`public_info` 表)
* **API 接口**: `/api/public-info/category/data` (带 `source=mysql` 参数或默认逻辑)
* **对接建议**: 
    - 默认情况下，API 可能会混合查询或优先查 DB。
    - 确保传参 `category` 与后端定义的分类一致（如 "人事任免", "招考招聘"）。

### 2.3 详情查询
详情页应优先尝试从缓存获取，未命中则查库。

* **数据源**: Redis (`gov:data:{id}`) -> MySQL
* **逻辑**: 后端 `PublicInfoService.getDetail` 已封装此逻辑。前端只需调用详情接口。

## 3. 常见问题排查

### Q: 为什么列表有数据，但按分类筛选为空？
**A**: 
1. 检查 Redis 中的数据是否包含正确的 `category` 字段。
2. 检查 MySQL 同步是否延迟。
3. **关键点**: 如果 Redis 数据缺少 `category` 字段，同步到 MySQL 后 `category` 也会为空，导致筛选失败。后端已增加校验逻辑，强制从 Redis 同步并修复分类信息。

### Q: 接口返回 200 但 list 为空 `[]`？
**A**:
1. 确认请求参数 `categoryTag` 是否与数据库中的 `category` 完全匹配（注意空格、特殊字符）。
2. 确认 `page` 参数是从 0 开始还是 1 开始（Spring Data JPA 默认从 0 开始）。

## 4. 调试工具

后端提供了 Redis 数据调试接口 (仅限开发环境)：
- 查看 Key 类型: `/debug/redis/type?key=gov:data:{id}`
- 查看 Key 内容: `/debug/redis/hgetall?key=gov:data:{id}` (需最新代码)
- 查看热门列表: `/debug/redis/zrange?key=gov:data:hot`
