# 前端 AI 适配规范

## 数据来源
- 首页：Redis 热门（通过后端 `GET /public-info/hot`）
- 分栏页：MySQL 列表（通过后端 `GET /public-info/list`）

## 分类与路由
- 路由参数使用 `category_code`（英文编码）：
  - `policy`、`personnel`、`planning`、`tender`、`exam`、`other`
- 展示时使用中文 `category` 做标签

## 展示与分发
- 依据 `file_types` 或主类型 `file_type` 进行页面分发：
  - PDF 页面：`file_type=pdf`
  - Word 页面：`file_type in [doc, docx]`
  - Excel 页面：`file_type in [xls, xlsx]`
  - 其他与压缩：`file_type in [zip, rar, ofd]` 或无匹配
- 下载链接使用 `attachments[].url`；如存在 `pdf_url` 可展示“转为 PDF”按钮

## 接口调用
- 首页：`GET /public-info/hot?category_code={code}&limit=20`
- 分栏页：`GET /public-info/list?category_code={code}&file_type={type}&page=1&size=20`
- 详情：`GET /public-info/{id}`（用于详情页）

## 参数与字段
- 需使用并展示：`title`、`url`、`publishDate`、`sourceOrg`、`region`、`category`、`file_types`、`file_type`
- 时间显示优先使用 `publishDate`；如有 `publishDateTime` 则显示更精确

## 辅助逻辑
- 首页只展示 Redis 返回的热门数据；不直接访问 Redis
- 分栏页支持关键词 `q` 与日期范围筛选（后端参数）

## 错误处理
- 对无附件或空 `file_type` 的数据，归为“其他”列表
