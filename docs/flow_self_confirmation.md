# 自我确认（依据 FLOW_CONFIRMATION_CHECKLIST）

## 环境与配置
- 表：`public_info`（已设为默认表） gov_data/settings.py:87
- 可配项：`REDIS_DETAIL_TTL_DAYS`、`REDIS_HOME_HOT_MAX` gov_data/settings.py:114-115

## 数据契约
- 返回字段齐全：`column/columnFlag/columnRaw/category/category_code/file_types/file_type/url/publishDate/publishDateTime` gov_data/pipelines.py:336-351
- 时间精度：补齐 `publishDateTime` 为 `YYYY-MM-DD HH:mm:ss` gov_data/pipelines.py:342-344

## Redis 写入
- 详情 JSON：`crawl:data:{YYYYMMDD}:{id}`（TTL 可配，默认 7 天） gov_data/pipelines.py:376
- 待同步集合：`crawl:pending:ids` gov_data/pipelines.py:343
- 热门 ZSet（全部兼容写入）：
  - `gov:hot_news`、`gov:hot_news:{category_code}` gov_data/pipelines.py:397-399
  - `crawl:home:hot`、`crawl:home:hot:category:{column}` gov_data/pipelines.py:389,393
  - `crawl:hot:{category_code}` gov_data/pipelines.py:402
- 评分：毫秒时间戳 gov_data/pipelines.py:384-386
- 保留上限：可配，默认 200 gov_data/pipelines.py:389,393,397,399,402

## MySQL 写入
- 表名可配，默认 `public_info` gov_data/settings.py:87
- 启动时自动建表与迁移缺失列，`source_url` 唯一索引尝试创建 gov_data/pipelines.py:458-494
- 去重更新：按 `source_url` 检查后更新或插入 gov_data/pipelines.py:624-660

## 自检结论（爬虫端）
- 增量→首页热门：OK（直接写 Redis，无需等待后端同步）
- 详情 TTL：OK（3–7 天范围，默认 7 天，可调）
- 热门前缀：OK（首选 `gov:hot_news:{category_code}`，并写兼容前缀）
- 全量→分栏列表：OK（写 `public_info`，重复 `source_url` 更新而非新增）

## 需协同与确认
- 前端/后端接口限流参数：默认 `limit=20`，最大 `100`（后端实现约束）
- 后端别名标准化（`word/excel/pdf`→扩展名集合）由后端执行；爬虫已提供 `file_types` 
- 若需要按 `id=md5(source_url)` 严格主键，需后端确认主键策略（当前按 `source_url` 去重兼容）

## 验收建议
- 增量推送 3 条不同 `category_code`，检查热门接口分栏展示
- 手动触发 `POST /api/admin/sync/db` 验证 Redis→MySQL 同步
- 全量推送 2 条并更新其中 1 条 `source_url`，确认列表显示更新
- 详情优先策略：Redis 命中与过期回退 MySQL 均正确
