# 后端接口需求文档 (Frontend to Backend Handover)

本文档列出了前端页面所需的后端接口及数据格式，以便后端开发人员进行解释和告知

## 1. 基础配置

- **Base URL**: `/api` (前端通过 `/api` 代理到后端服务)
- **数据格式**: JSON

## 2. 接口列表

### 2.1 获取分类列表 (可选)

前端目前使用硬编码的分类列表：`['人事任免', '招考招聘', '干部公示']`。
如果后端支持动态配置分类，请实现此接口。

- **URL**: `/gov/category/list`
- **Method**: `GET`
- **Response**: `Array<String>`
  ```json
  ["人事任免", "招考招聘", "干部公示"]
  ```

### 2.2 获取热门政务信息

用于首页展示热门/最新信息。

- **URL**: `/public-info/hot`
- **Method**: `GET`
- **Params**:
    - `source`: `redis` (可选，指定数据源)
- **Response**: `Array<Object>`
  ```json
  [
    {
      "dataId": "123456",
      "title": "关于xxx的通知",
      "category_tag": "人事任免",  // 必须字段，用于显示标签颜色
      "publish_dept": "某某局",
      "publish_time": "2023-10-01 12:00:00", // 必须字段，格式可以是时间戳或字符串
      "publishDate": "2023-10-01", // 兼容字段
      "summary": "摘要信息..."
    }
  ]
  ```
  **注意**: 前端强依赖 `publish_time` 或 `publishDate` 字段来显示时间，依赖 `category_tag` 来显示分类标签。

### 2.3 获取分类数据列表 (分页)

用于点击分类后的列表页展示。

- **URL**: `/public-info/list`
- **Method**: `GET`
- **Params**:
    - `category`: `String` (分类名称，如 "人事任免")
    - `page`: `Integer` (页码，从0开始)
    - `size`: `Integer` (每页条数)
    - `source`: `mysql` (可选)
- **Response**:
  ```json
  {
    "list": [
      {
        "data_id": "123",
        "title": "标题",
        "publish_dept": "发布部门",
        "publish_time": "2023-10-01"
      }
    ],
    "total": 100
  }
  ```

### 2.4 获取信息详情

- **URL**: `/gov/detail`
- **Method**: `GET`
- **Params**:
    - `dataId`: `String`
- **Response**:
  ```json
  {
    "data_id": "123",
    "title": "标题",
    "category_tag": "人事任免",
    "publish_dept": "发布部门",
    "publish_time": "2023-10-01",
    "source_website": "来源网站",
    "source_url": "原文链接",
    "content": "<p>HTML内容</p>",
    "content_text": "纯文本内容",
    "attachments": [
       { "name": "附件1.pdf", "url": "..." }
    ]
  }
  ```

## 3. 待解决问题

1. **首页分类接口 404**: `/api/gov/category/list` 目前返回 404。前端已做兼容处理，若请求失败将使用默认分类。
2. **字段对齐**: 请确保返回的 JSON 对象中包含 `category_tag` 和 `publish_time` 字段，否则前端无法正确展示分类标签和发布时间。
