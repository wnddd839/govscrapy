# 统一规范对齐说明（依据 UNIFIED_INTEGRATION_SPEC v1.0）

## 已对齐
- 路由与数据源：增量→Redis；全量→MySQL；详情优先 Redis
- 字段：`column`（英文代码）、`columnFlag`（同代码）、`columnRaw`、`category`（中文）、`category_code`（英文）、`file_types`（数组）、`file_type`（单值）、`url/sourceUrl`、`publishDate/publishDateTime`
- Redis 键：
  - 详情：`crawl:data:{YYYYMMDD}:{id}`（TTL=配置，默认 7 天）
  - 热门：`gov:hot_news`、`gov:hot_news:{category_code}`、`crawl:home:hot`、`crawl:home:hot:category:{column}`、`crawl:hot:{category_code}`（score=毫秒时间戳，保留最新 `REDIS_HOME_HOT_MAX`）
  - 待同步：`crawl:pending:ids`
- MySQL 表：默认 `gov_open_data`，可通过 `MYSQL_TABLE` 切换到 `public_info`；启动自动迁移补齐字段
- 设置项：`REDIS_DETAIL_TTL_DAYS`、`REDIS_HOME_HOT_MAX`、`MYSQL_TABLE` 支持环境变量

## 运行示例
- 增量：`scrapy crawl hn_gov -a mode=incremental -a category=zfwj`
- 全量：`scrapy crawl gd_gov -a mode=full -a category=gsgg -a max_pages=50`

## 待你确认
- 已确认结论（后端 AI 已确认）：
  - Redis 热门统一读取 `gov:hot_news*`，兼容 `crawl:home:hot*` 与 `crawl:hot:{category}`，前端按接口即可
  - 主归档表使用 `public_info`（已设置 `MYSQL_TABLE=public_info`），建议为 `source_url` 建唯一索引去重
  - 首页热门保留 Top 200；接口默认 `limit=20`，单次最大 `100`
  - 时间精度统一为 `publishDateTime` 的 `YYYY-MM-DD HH:mm:ss`；若库内只有 `publish_date`，返回时补足 `00:00:00`
  - 返回强制携带 `file_types`（数组）；列表接口支持 `file_type` 筛选，后端标准化扩展名

## 参考文档
- 平台后端：`gov-ai-platform-backend/docs/UNIFIED_INTEGRATION_SPEC.md`
- 我方三方文档：`docs/spider_ai_spec.md`、`docs/backend_ai_spec.md`、`docs/frontend_ai_spec.md`
