# 后端 AI API 规范

## 数据源
- 首页热门：Redis（`gov:hot_news`、`gov:hot_news:{category_code}`）
- 分栏归档：MySQL（`gov_open_data`）

## 接口
- `GET /public-info/hot`
  - 参数：`category_code`（可选）、`limit`（默认 20）
  - 行为：从 ZSET 读取 TopN，按键取详情 JSON（`crawl:data:*`），返回数组
- `GET /public-info/list`
  - 参数：`category_code`、`column`、`file_type`、`q`、`start_date`、`end_date`、`page`、`size`
  - 行为：查询 MySQL `gov_open_data`，分页返回 `{total, items}`
- `GET /public-info/{id}`
  - 行为：按主键 `id` 查询 MySQL 返回详情

## MySQL 字段
- `id`（PK，`md5(source_url)`）
- `title`、`source_url`、`source_org`、`publish_date`、`region`、`content_text`、`attachments`
- `column`、`category`（中文）、`category_code`（英文编码）
- `file_types`（多值字符串，逗号分隔）、`file_type`（单值）

## Redis 键
- 热门：`gov:hot_news`、`gov:hot_news:{category_code}`（member=详情键，score=发布时间戳）
- 详情：`crawl:data:{YYYYMMDD}:{id}`（JSON，TTL=3 天）

## 返回数据契约（items/详情）
- 与爬虫输出一致，包含：`title`、`url`、`publishDate`、`publishDateTime`、`sourceOrg`、`region`、`contentText`、`attachments`、`column`、`category`、`category_code`、`file_types`、`file_type`

## 索引建议
- 在 `category_code`、`column`、`publish_date` 上建立索引
- 如需按附件类型筛选，考虑对 `file_type` 建索引

## 安全与配置
- 数据库与 Redis 连接信息通过环境变量注入；不要在仓库内写死凭据
