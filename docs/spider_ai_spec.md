# 爬虫 AI 交付与输出规范

## 采集模式
- `mode=incremental`：增量，写入 Redis，用于首页热门
- `mode=full`：全量，写入 MySQL，用于分栏归档

## 调用参数
- `category`：分栏标识（如 `zfwj`、`gwyzk`、`gsgg`）
- `max_pages`：全量分页上限（增量忽略）

## 输出字段（统一 JSON 契约）
- `title`：标题
- `sourceUrl` / `url`：原始链接
- `publishDate`：`YYYY-MM-DD`
- `publishDateTime`：`YYYY-MM-DD HH:mm:ss`
- `region`：地区
- `sourceOrg`：来源机构
- `contentText`：正文纯文本
- `attachments`：数组（`name`、`url`、`type`、`size`、`pdf_url`）
- `column`：分栏参数
- `category`：中文分类（政策法规/人事信息/规划计划/招标采购/其他）
- `category_code`：平台编码（policy/personnel/planning/tender/exam/other）
- `file_types`：附件类型列表（去重）
- `file_type`：主附件类型（优先级：pdf>docx>doc>xlsx>xls>ofd>zip>rar）
- `is_hot`：增量为 `true`，全量为 `false`

## Redis（增量）
- 详情键：`crawl:data:{YYYYMMDD}:{id}`，TTL=3 天
- 待处理集合：`crawl:pending:ids`（成员 `{YYYYMMDD}:{id}`）
- 首页热门：
  - 兼容键：`crawl:home:hot`、`crawl:home:hot:category:{column}`
  - 平台键：`gov:hot_news`、`gov:hot_news:{category_code}`（ZSET，按发布时间戳；保留最新 200）

## MySQL（全量）
- 表：`gov_open_data`
- 字段：`id`、`title`、`source_url`、`source_org`、`publish_date`、`region`、`content_text`、`attachments`、`column`、`category`、`category_code`、`file_types`、`file_type`
- 迁移：爬虫启动自动 `ALTER TABLE` 补齐缺失列

## 分类映射
- 政策法规→`policy`；人事信息→`personnel`；规划计划→`planning`；招标采购→`tender`；`gwyzk/exam`→`exam`；其他→`other`

## 示例运行
- 增量：`scrapy crawl hn_gov -a mode=incremental -a category=zfwj`
- 全量：`scrapy crawl gd_gov -a mode=full -a category=gsgg -a max_pages=50`
