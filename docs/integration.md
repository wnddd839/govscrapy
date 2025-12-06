# 三方AI数据流与对接规范

## 概述
- 爬虫按 `mode` 决定写入位置：`incremental`→Redis；`full`→MySQL。
- 所有数据统一携带分栏字段 `column` 与自动分类 `category`、附件类型聚合 `file_types`。
- 首页数据从 Redis 获取；分栏页从 MySQL 查询，前端根据 `file_types` 分类展示。

## 运行参数
- `category`：分栏标识（如 `zfwj`、`gwyzk`、`gsgg`），由前端/调度传入。
- `mode`：`incremental`（增量，首页）或 `full`（全量，库表）。
- `max_pages`：全量分页上限。

## Redis 数据契约（增量）
- 详情键：`crawl:data:{YYYYMMDD}:{id}` → 值为 JSON，TTL 3 天。
- 待处理集合：`crawl:pending:ids` → 成员 `{YYYYMMDD}:{id}`。
- 首页热门：
  - 全局：`crawl:home:hot`（ZSET，member 为详情键，score 为发布时间戳，保留最新 200）
  - 分类：`crawl:home:hot:category:{column}`（同上）
- JSON结构：
  - `title`、`sourceOrg`、`sourceUrl`、`publishDate`（`YYYY-MM-DD`）、`region`
  - `contentText`（纯文本）
  - `attachments`：数组，元素含 `name`、`url`（MinIO 链接）、`type`（扩展名）、`size`、`pdf_url`（可空）
  - `column`（分栏参数原样传递）
  - `category`（自动分类：人事信息/招标采购/规划计划/财政预决算/政策法规/其他）
  - `file_types`（去重后的扩展名列表：如 `['pdf','docx','xlsx']`）

## MySQL 表结构（全量）
- 数据库：`MYSQL_DATABASE`（默认 `gov_web`）
- 表：`gov_open_data`
- 必备字段：
  - `id`（PK，`md5(source_url)`）
  - `title`、`source_url`、`source_org`、`publish_date`、`region`
  - `content_text`（TEXT）、`attachments`（JSON/TEXT）
  - `column`（VARCHAR(64)）
  - `category`（VARCHAR(64)）
  - `file_types`（VARCHAR(128)，逗号分隔）
- 迁移策略：爬虫在启动时自动检测并按需 `ALTER TABLE` 添加 `column`、`category`、`file_types`。

## 前端获取与展示
- 首页：
  - 读 `crawl:home:hot` 或按需读 `crawl:home:hot:category:{column}`，再 `GET` 详情键取 JSON。
  - 展示分栏与 `file_types` 标签；跳转详情/下载使用 `attachments[].url`。
- 分栏页：
  - 后端提供 MySQL 查询接口，支持条件：`column`、`category`、`file_types`、`publish_date` 范围、分页。
  - 前端根据返回的 `file_types` 分发到不同分栏页面（PDF/Word/Excel/压缩等）。

## 后端查询接口建议
- `GET /api/open-data`：列表查询
  - 参数：`column`、`category`、`file_type`、`q`（关键词）、`start_date`、`end_date`、`page`、`size`
  - 返回：`items`、`total`
- `GET /api/open-data/{id}`：详情
- `GET /api/open-data/hot`：首页热门（可直接透传 Redis `crawl:home:hot` TopN）

## 调度与环境
- Scrapy 设置支持环境变量覆盖：`MYSQL_*`、`REDIS_*`、`MINIO_*`。
- 运行示例：
  - 增量：`scrapy crawl hn_gov -a mode=incremental -a category=zfwj`
  - 全量：`scrapy crawl gd_gov -a mode=full -a category=gsgg -a max_pages=50`

## 待确认事项（由你转交）
- 前端：
  - 首页 TopN 数量与排序规则（目前按发布时间戳，保留 200）。
  - 分栏页面的 `file_types` 映射与优先级（如合并 `doc/docx` 为 Word）。
  - 详情页是否展示 `pdf_url` 转换链接。
- 后端：
  - MySQL 字段类型偏好（`attachments` 是否使用 JSON 类型）。
  - 查询接口路径与参数命名是否采纳上述建议。
  - 是否需要按 `category` 与 `column` 的联合过滤。
- 运维：
  - Redis/MinIO/MySQL 的实际主机与凭据通过环境变量下发。
  - 是否需要 Scrapyd 托管与发布流程。

