# 🧪 Gov AI Platform Backend - 测试验证指南

本文档旨在指导开发与测试人员对后端服务进行全链路功能验证，确保系统在上线前达到稳定标准。

---

## 📋 测试环境准备

在开始测试前，请确保您的本地或测试服务器环境已就绪：

1.  **服务启动**: 确保后端服务已运行 (默认端口 `8080`)。
2.  **依赖组件**:
    *   **MySQL**: `8.138.24.168:3306` (库: `gov_open`)
    *   **Redis**: `8.138.24.168:6379`
    *   **MinIO**: `http://8.138.24.168:19002`

---

## 🛠️ 1. 核心接口功能测试 (API Test)

使用 Postman 或 cURL 进行验证。

### 1.1 政务信息列表 (List)
*   **测试目的**: 验证分页、关键词搜索、地区筛选功能。
*   **请求**:
    ```bash
    GET /api/public-info/list?page=0&size=10&q=政策&region=海南
    ```
*   **预期结果**:
    *   状态码 `200 OK`
    *   返回 JSON 包含 `data` 列表和 `total` 总数。
    *   数据中的 `title` 或 `contentText` 应包含"政策"，`region` 应为"海南"。

### 1.2 政务信息详情 (Detail)
*   **测试目的**: 验证单条数据查询及**附件解析**是否正常。
*   **请求**:
    ```bash
    GET /api/public-info/detail/{id}
    # 请替换 {id} 为列表中存在的实际 ID
    ```
*   **预期结果**:
    *   状态码 `200 OK`
    *   `attachments` 字段应为非空数组（如果该记录有附件）。
    *   重点检查：
        *   `url`: 附件下载链接（爬虫转存后的地址）。
        *   `pdf_url`: PDF 预览链接（由爬虫转换并提供）。
        *   `original_url`: 原始来源链接（可选）。

### 1.3 热门推荐 (Hot)
*   **测试目的**: 验证 Redis 缓存是否生效。
*   **请求**:
    ```bash
    GET /api/public-info/hot
    ```
*   **预期结果**:
    *   首次请求：从数据库查询（耗时稍长）。
    *   二次请求：从 Redis 返回（耗时极短，<20ms）。
    *   返回按 `publishDate` 倒序的前 10 条记录。

### 1.4 AI 智能问答 (RAG)
*   **测试目的**: 验证检索增强生成 (RAG) 流程是否通畅（MySQL检索 -> Prompt构建 -> 通义千问API）。
*   **请求**:
    ```bash
    POST /api/ai/chat
    Content-Type: application/json

    {
      "question": "海南省最近有什么关于人才引进的政策？"
    }
    ```
*   **预期结果**:
    *   状态码 `200 OK`
    *   `answer`: 包含流畅的文本回答。
    *   `references`: 包含参考的来源 URL 列表。

---

## 🔄 2. 数据同步全链路测试 (Data Sync)

此环节验证 **爬虫 -> Redis -> MySQL** 的核心数据流转，是系统稳定性的关键。

### 2. 爬虫数据格式 (Crawler Integration)
- **数据透传验证**:
  - 爬虫需在 `attachments` 字段中返回完整 JSON 结构。
  - **关键**: 必须包含 `url` (原始链接) 和 `pdf_path` (转换后的 PDF 路径)。
  - 后端验证: 检查 `PublicInfo` 表的 `attachments` 字段是否完整保存了爬虫提交的 JSON。
- **PDF 转换责任**:
  - **责任方**: 爬虫 (Crawler)。
  - **要求**: 爬虫在抓取附件时，需自动将非 PDF 格式 (doc, docx, etc.) 转换为 PDF，并上传至 MinIO。
  - **字段**: `pdf_path` 字段应指向 MinIO 中的 PDF 文件位置。
  - **后端处理**: 后端仅负责存储路径和生成预览链接，不进行格式转换。

### 2.1 模拟爬虫数据写入 (Redis)
使用 Redis 客户端 (或 IDEA Database 工具) 写入模拟数据：

1.  **写入数据实体 (JSON)**
    *   **Key**: `crawl:data:2023-12-02:test-verify-001`
    *   **Value**:
        > 注意：附件转换 (Office -> PDF) 由爬虫负责，后端仅负责透传 `pdf_url` 等字段。
        ```json
        {
          "title": "上线前功能验证公告",
          "sourceOrg": "测试中心",
          "sourceUrl": "http://verify.gov.cn/001",
          "publishDate": "2023-12-02",
          "region": "测试区",
          "contentText": "这是一条用于验证上线稳定性的测试数据。",
          "attachments": [
            {
              "name": "验证报告.docx",
              "original_url": "http://verify.gov.cn/files/report.docx",
              "url": "http://8.138.24.168:19000/gov-attachments/test/report.docx",
              "pdf_url": "http://8.138.24.168:19000/gov-attachments/test/report.pdf"
            }
          ]
        }
        ```

2.  **写入待处理任务 (Set)**
    *   **Key**: `crawl:pending:ids`
    *   **Member**: `2023-12-02:test-verify-001`

### 2.2 触发同步
调用管理员接口强制触发同步（或等待 10 分钟自动执行）：
```bash
POST /api/admin/sync/db
```

### 2.3 验证结果
1.  **Redis**: 检查 `crawl:pending:ids` 和 `crawl:data:...` 是否已**消失**。
2.  **MySQL**: 查询 `public_info` 表：
    ```sql
    SELECT * FROM public_info WHERE title = '上线前功能验证公告';
    ```
    *   应能查到该记录。
    *   `attachments` 字段应正确存储为 JSON 字符串，且包含 `pdf_url` 等所有爬虫提供的字段。

---

## 🛡️ 3. 异常与容错测试 (Resilience)

| 测试场景 | 操作步骤 | 预期行为 |
| :--- | :--- | :--- |
| **Redis 宕机** | 暂时断开 Redis 连接或配置错误地址 | 接口不应直接 500 崩溃；热门接口降级为查库；AI 接口正常运行（不依赖 Redis）。 |
| **MySQL 慢查询** | 模拟大量并发查询 `/list` 接口 | 监控日志，确认连接池 (`HikariCP`) 是否正常工作，无连接泄漏。 |
| **非法输入** | 向 AI 接口发送空问题或超长文本 | 接口应返回 `400 Bad Request` 或友好的错误提示，而不是内部报错。 |
| **重复数据** | 多次向 Redis 写入同一 ID 的数据并触发同步 | 同步逻辑应识别并执行 **更新 (Update)** 或 **跳过**，而不是插入重复记录。 |

---

## ✅ 上线签收标准 (Checklist)

- [ ] 所有单元测试通过 (`mvn test`)。
- [ ] 上述核心 API 接口手动验证通过。
- [ ] 数据同步流程验证通过，无数据丢失或格式错误。
- [ ] 敏感配置（DB密码、API Key）已完全环境变量化，无硬编码。
- [ ] 日志记录正常，无频繁 `ERROR` 级别日志。

---
*Document created by Backend AI Team*
