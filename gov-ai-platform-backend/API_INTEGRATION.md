# Backend API Integration Guide (Backend -> Frontend)

这份文档旨在帮助前端开发人员无缝集成后端 API。

## 1. 基础信息 (Base Info)

*   **Base URL**:
    *   Local: `http://localhost:8080/api`
    *   Prod: `http://<server-ip>:8080/api`
*   **Authentication**: 当前版本开放访问 (Public Access)，无需 Bearer Token。
*   **CORS**: 已配置允许 `http://localhost:5173` (Vite 默认端口)。如需新增域名，请联系后端。
*   **Rate Limit**: 单 IP 每分钟 120 次请求。超限返回 `429 Too Many Requests`。

## 2. 核心业务接口 (Public Info)

### 2.1 获取政务信息列表
用于搜索页或首页列表展示。

*   **Endpoint**: `GET /public-info/list`
*   **Query Parameters**:
    *   `page`: 页码，从 0 开始 (Default: 0)
    *   `size`: 每页条数 (Default: 10)
    *   `q`: 搜索关键词 (Optional, 匹配标题或正文)
    *   `region`: 地区筛选 (Optional, e.g., "海口")
    *   `startDate`: 开始日期 (Optional, ISO format `YYYY-MM-DD`)
    *   `endDate`: 结束日期 (Optional, ISO format `YYYY-MM-DD`)

*   **Response Example**:
    ```json
    {
      "data": [
        {
          "id": 1,
          "title": "海南省关于...",
          "publishDate": "2023-10-01",
          "region": "海口",
          "sourceOrg": "省政府",
          ...
        }
      ],
      "page": 0,
      "size": 10,
      "total": 105
    }
    ```

### 2.2 获取详情
用于详情页展示。

*   **Endpoint**: `GET /public-info/detail/{id}`
*   **Response Example**:
    ```json
    {
      "id": 1,
      "title": "政策标题",
      "contentText": "政策全文内容...",
      "attachments": [
        {
          "name": "附件1.pdf",
          "url": "http://.../download/xxx.pdf",   // 下载链接
          "pdf_url": "http://.../preview/xxx.pdf", // 预览链接 (推荐优先使用)
          "original_url": "http://gov.cn/..."      // 原始来源链接
        }
      ],
      ...
    }
    ```
    > **前端注意**: `attachments` 数组可能为空。请优先使用 `pdf_url` 进行内嵌预览；如果不存在，则使用 `url` 提供下载。

### 2.3 热门推荐
用于首页侧边栏或推荐位。

*   **Endpoint**: `GET /public-info/hot`
*   **Query Parameters**:
    *   `region`: 地区筛选 (Optional)
*   **Response**: `List<PublicInfo>` (Top 10 items)

## 3. AI 智能问答 (AI Chat)

### 3.1 发送提问
*   **Endpoint**: `POST /ai/chat`
*   **Request Body**:
    ```json
    {
      "question": "海南的人才引进政策有哪些？"
    }
    ```
*   **Response Example**:
    ```json
    {
      "answer": "根据最新政策，海南省人才引进包括...",
      "references": [
        "http://gov.cn/policy/123.html",
        "http://gov.cn/policy/456.html"
      ]
    }
    ```
    > **前端注意**: `answer` 字段为 Markdown 格式文本，建议使用 Markdown 渲染组件展示。`references` 为参考来源链接列表。

## 4. 文件服务 (File Service)

通常情况下，您直接使用详情接口返回的 `url` 或 `pdf_url` 即可。如果需要手动拼接预览/下载地址，可使用以下接口：

*   **预览**: `GET /file/preview/{objectName}` -> 返回预签名 URL (302 Redirect or Text Body?) *注: 当前实现直接返回 URL 字符串*
*   **下载**: `GET /file/download/{objectName}` -> 返回预签名 URL 字符串

## 5. 常见状态码

*   `200 OK`: 请求成功
*   `404 Not Found`: 资源不存在
*   `429 Too Many Requests`: 请求过于频繁
*   `500 Internal Server Error`: 服务器内部错误

---
*Document created by Backend Team for Frontend Team*
