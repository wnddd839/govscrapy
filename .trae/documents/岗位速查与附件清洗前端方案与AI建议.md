## 目标概述

* 处理公务员招聘公告附件（xls/xlsx/csv/pdf/doc），清洗入库，前端提供按专业/学历筛选的岗位速查独立页面。

* 前端负责页面与交互、状态管理、接口契约、错误与空态处理；后端与爬虫负责附件抓取、解析、清洗与标准化。

## 前端实现

* 页面：在路由 `/jobs` 提供独立页面（现有 JobListView 可复用/增强）。

* 筛选区：

  * 专业（支持搜索+多选）、学历（本科/硕士/博士/大专等，单选或多选）、地区/机构（可选）、关键字搜索。

  * 快速清空与状态标签（chip），支持“仅显示可报考”和“含专业相近”切换。

* 列表区：

  * 卡片或表格展示：岗位名称、机构、专业要求、学历要求、报名起止、招录人数、附件来源链接。

  * 分页与排序（按报名截止、招录人数、相关度）。

* 交互与体验：

  * 骨架屏/加载态、空态与错误态；支持收藏与导出（CSV）。

  * 详情弹窗或独立路由，展示岗位完整要求与原附件链接。

* 前端数据模型：

  * Job：`id, agency, title, major_codes[], major_text, edu_level, degree, quota, city, deadline, source_url, attachment_url, normalized_score`。

  * 词表：`majors[]`（码+名）、`edu_levels[]`；服务端提供。

* API 契约：

  * `GET /api/majors?q=...` 返回专业词表，含别名与码。

  * `GET /api/edu-levels` 返回学历枚举。

  * `GET /api/jobs?major_codes=...&edu_level=...&city=...&q=...&page=1&page_size=20&sort=deadline_desc&similar=true` 返回岗位与分页信息；`similar=true` 表示纳入相近专业。

  * `GET /api/jobs/{id}` 返回岗位详情。

  * 管理端（可选）：`POST /api/ingest/upload` 上传附件，`GET /api/ingest/status/{task_id}` 查询解析进度与日志。

* 状态管理与缓存：

  * 使用查询参数驱动页面状态；对词表与最近一次搜索结果做缓存；异常与重试策略。

* 组件库与实现细节：

  * 采用 Element Plus：`el-form/el-select/el-table/el-card/el-pagination/el-skeleton/el-empty/el-alert`。

  * 无障碍与移动端适配（栅格与断点）。

## 后端 AI 建议

* 解析与标准化：

  * xls/xlsx/csv：优先用 Pandas+openpyxl（Python）或 SheetJS（Node）解析；统一列头映射（多源多式列名映射表）。

  * pdf/doc：OCR/版式解析（PyMuPDF/Apache Tika/textract），提取表格与段落；保留原文片段用于审计。

* 结构化抽取：

  * 规则+模型混合：先正则/规则提取（机构/岗位/人数/时间/地区），对“专业/学历”用 LLM/NER 强化。

  * 专业标准化：对照教育部学科与专业目录，建立专业码表与别名词典；LLM 做别名归并，低置信回退到规则或人工复核。

  * 学历枚举统一：`primary > junior > high > junior_college > bachelor > master > doctor`，生成统一枚举。

* 相近专业匹配：

  * 术语词向量/句向量（SimCSE/Instructor or bge），构建专业嵌入库；以阈值匹配相近专业，输出相似度分数供前端 `similar=true` 使用。

* 质量保障：

  * 字段完整性/范围校验、重复检测（岗位+机构+时间+hash）、 lineage 记录（源附件→解析→清洗→入库）。

  * 人工复核工作台：低置信样本入队待审；审后写回训练集与词典。

* 性能与可用性：

  * 队列化批处理（Celery/RQ），分片并发；缓存词典与嵌入索引；断点续跑与失败重试。

## 爬虫 AI 建议

* 发现与抓取：

  * 源站清单与调度周期；增量更新（Last-Modified/ETag/快照 diff）。

  * 动态站点用 Playwright 渲染；统一附件下载器（支持重定向/鉴权/断点）。

* 附件管线：

  * 下载→指纹（MD5+规范化文件名）→去重与版本化→解析器路由（xls/xlsx/csv/pdf/doc）→结构化→清洗。

* 反爬与稳健：

  * 速率限制、指数退避重试、代理池与 UA 轮换、IP/验证码策略。

* 监控与告警：

  * 任务/站点级指标（成功率、延迟、变更量），异常日志与告警（含附件格式异常）。

## 数据库与索引

* 表设计：`jobs`（主表）、`attachments`（源文件）、`majors_dict`（码表与别名）、`agencies`、`job_facets`（聚合与缓存）。

* 索引：`(major_code, edu_level, city, deadline)` 组合索引；全文检索（关键词）可用 Postgres FTS 或 Elastic 索引。

* 预计算：每日构建 facets（计数/范围），供前端快速筛选与展示。

## 风险与缓解

* 多源格式不一致：列头映射与样本库；低置信人工复核。

* OCR/LLM误差：阈值与回退规则；危险字段（时间/数量）双重校验。

* 法规与合规：尊重 robots 与版权声明；对外展示保留来源与链接。

## 交付步骤

* 第1步：确认 API 契约与词表结构。

* 第2步：前端实现页面骨架与筛选交互（对接 mock）。

* 第3步：接入真实接口，完善分页与排序、空态/错误态。

* 第4步：优化相近专业匹配展示与收藏/导出。

* 第5步：联调附件管线与管理端（如需）。

