# 三方对接确认清单

## 爬虫（数据提供方）
- 推送接口：`POST /api/admin/crawl/ingest?mode={incremental|full}`，Body 为 `CrawlItemDTO[]`
- 必填字段：`title`、`sourceUrl`、`publishDate`、`category`、`columnFlag`
- 增量模式：用于首页热门展示，同时写入 `crawl:data` 与 `crawl:hot:{category}`，并加入 `crawl:pending:ids`
- 全量模式：直接写入 MySQL（按 `id`/`sourceUrl` 去重）
- 附件字段：`attachments[]` 可包含 `name`、`url`、`pdf_url`、`original_url`

## 后端（数据服务方）
- 接收并校验数据，维护 Redis 热门与待同步集合
- 定时同步：`SYNC_INTERVAL` 控制从 Redis 到 MySQL 的频率
- 提供接口：
  - 首页热门：`GET /api/public-info/hot?source=redis&category=...`
  - 分栏列表：`GET /api/public-info/column/{columnFlag}`
  - 综合检索：`GET /api/public-info/list`
  - 详情：`GET /api/public-info/detail/{id}`
  - 运维：`POST /api/admin/sync/db`、`POST /api/admin/sync/cache`

## 前端（展示方）
- 首页：仅展示 Redis 热门数据（`source=redis` + `category`），分页参数 `page/size`
- 分栏页面：从 MySQL 获取（`columnFlag`），或使用搜索页（`list`）
- 文件类型分类：根据 `attachments` 的文件后缀或 `category/columnFlag` 渲染到对应分栏页

## 配置与环境
- 数据库连接：`DB_*` 环境变量
- Redis：`REDIS_*`
- MinIO：`MINIO_*`
- 端口：`SERVER_PORT`（默认 8080）
- 同步频率：`SYNC_INTERVAL`（毫秒）

## 测试用例建议
- 增量推送 3 条不同 `category` 数据，验证首页 Redis 热门分页
- 同步到 MySQL 后，验证分栏接口数据一致性
- 全量推送 2 条，验证查重与更新逻辑

