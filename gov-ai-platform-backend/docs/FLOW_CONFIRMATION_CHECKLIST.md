# 前端与爬虫全流程确认文档（自检版）

## 目标
- 自助完成首页热门（Redis）、分栏归档（MySQL）、详情展示的端到端打通与验收
- 统一规范基于 `UNIFIED_INTEGRATION_SPEC.md v1.0`，此文档为操作与确认清单

## 角色与职责
- 爬虫：按 `mode` 推送数据，增量写 Redis 热门与详情，加入待同步集合；全量写 MySQL
- 后端：提供统一接口与兼容读取，定时同步 Redis→MySQL，标准化返回字段
- 前端：首页读取 Redis 热门，分栏与搜索读取 MySQL，详情优先 Redis 命中

## 环境准备
- 必备变量：`DB_*`、`REDIS_*`、`MINIO_*`、`SERVER_PORT`、`SYNC_INTERVAL`
- 表配置：`MYSQL_TABLE=public_info`（主归档表）
- 路由兼容：建议优先 `/api/open-data/*`，保留 `/api/public-info/*`

## 数据契约要点
- 统一返回字段：`id/title/source_url/sourceOrg/publish_date/publishDateTime/region/contentText/attachments/column/category/category_code/file_types`
- `file_types` 为数组；后端支持 `file_type` 别名筛选（word→doc|docx，excel→xls|xlsx）
- 时间精度：`publishDateTime` 统一 `YYYY-MM-DD HH:mm:ss`（仅日期时补 `00:00:00`）

## Redis 键规范（写入/读取）
- 详情 JSON：`crawl:data:{YYYYMMDD}:{id}`，TTL 3–7 天
- 热门 ZSet 读取优先级：`gov:hot_news:{category_code}` → `crawl:home:hot:category:{column}` → `crawl:hot:{category}` → `gov:hot_news`
- 待同步集合：`crawl:pending:ids`，成员 `{YYYYMMDD}:{id}`

## 接口清单
- 推送：`POST /api/admin/crawl/ingest?mode=incremental|full`（Body: `CrawlItemDTO[]`）
- 热门：`GET /api/open-data/hot?category_code=&limit=`（默认 limit=20，最大 100）
- 列表：`GET /api/open-data?column=&file_type=&q=&page=&size=`（默认 page=0，size=20）
- 详情：`GET /api/open-data/{id}`（先 Redis 后 MySQL）
- 兼容：`/api/public-info/*`

## 操作步骤（爬虫）
1. 增量推送
   - 写入详情键与待同步集合；热门写 `gov:hot_news:{category_code}`（推荐）
   - 示例 Body：
   ```json
   [{
     "id": "md5(source_url)",
     "title": "示例标题",
     "sourceOrg": "某某市政府",
     "sourceUrl": "http://gov.cn/...",
     "publishDate": "2025-12-01",
     "contentText": "正文...",
     "region": "海口",
     "category": "政策法规",
     "category_code": "policy",
     "column": "policy",
     "attachments": [{ "name": "文件.pdf", "url": "http://...", "pdf_url": "http://..." }]
   }]
   ```
2. 全量推送
   - 直接写 MySQL（后端接口会按 `id/source_url` 去重更新）
3. 键检查
   - 确认 `crawl:data:*`、`crawl:pending:ids`、`gov:hot_news:*` 写入成功

## 操作步骤（前端）
1. 首页热门
   - 请求：`GET /api/open-data/hot?category_code=policy&limit=20`
   - 展示：渲染 `title/publish_date/file_types` 标签；点击跳详情
2. 分栏列表
   - 请求：`GET /api/open-data?column=policy&file_type=word&page=0&size=20`
   - 别名生效：word→doc|docx，excel→xls|xlsx
3. 详情页
   - 请求：`GET /api/open-data/{id}`；无 `pdf_url` 则回退 `url` 下载

## 自检清单（爬虫）
- [ ] 增量推送后，首页热门能在 1 分钟内展示最新数据
- [ ] 详情 JSON 键 TTL 正常（3–7 天），内容包含必填字段
- [ ] 热门 ZSet 使用 `gov:hot_news:{category_code}`；如需兼容，额外写 `crawl:home:hot:category:{column}`/`crawl:hot:{category}`
- [ ] 全量推送后，分栏列表能分页返回，且重复 `source_url` 被更新而非新增

## 自检清单（前端）
- [ ] 热门接口默认 `limit=20`，滚动加载不超过最大 `100`
- [ ] 别名筛选生效：`file_type=word` 返回 doc|docx，`excel` 返回 xls|xlsx
- [ ] `file_types` 数组渲染标签无误；无 `pdf_url` 时回退下载链接
- [ ] 详情页能在 Redis 命中与过期后回退 MySQL 两种情况展示

## 验收步骤（联合）
- [ ] 增量推送 3 条不同 `category_code`，前端首页各栏目展示正确且分页正常
- [ ] 手动触发同步 `POST /api/admin/sync/db` 后，分栏列表可查询到对应数据
- [ ] 全量推送 2 条并更新其中 1 条 `source_url`，列表显示更新效果
- [ ] 详情优先策略验证：Redis命中与过期回退均正确

## 约束与默认值
- 热门窗口：Top 200
- `limit` 默认 20，最大 100
- 时间精度：`publishDateTime` 统一 `YYYY-MM-DD HH:mm:ss`
- 表：`public_info`（主归档），建议 `source_url` 唯一索引

## 常见问题
- 未显示热门：检查是否写入了 `gov:hot_news:{category_code}` 或兼容前缀，member 是否为详情键
- 详情为空：检查 `crawl:data:*` TTL 是否过期；过期后由 MySQL 返回
- 别名筛选无效：确认前端使用 `file_type=word|excel|pdf`；或改用 `file_types=["docx","pdf"]`

## 结论（后端已确认）
- 热门读取统一以 `gov:hot_news*` 为首选；兼容其他前缀
- 主归档表为 `public_info`；字段与契约兼容
- 返回强制携带 `file_types`（数组）；支持 `file_type` 别名筛选
- 时间统一 `publishDateTime` 精度；仅日期时补 `00:00:00`

