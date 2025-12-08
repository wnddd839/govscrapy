# 后端对接文档：爬虫数据Redis集成方案

## 1. 概述
本系统已完成爬虫端改造，移除了MySQL直连，改为**全量数据写入Redis**。后端服务需监听Redis特定队列，消费数据并持久化到业务数据库。

**核心变化：**
- 数据源：`Redis` (DB 1)
- 附件存储：`MinIO` (URL已生成)
- 数据分类：已通过 `category` 字段预打标
- 数据格式：`Hash` + `Sorted Set`

---

## 2. Redis 数据结构

### 2.1 待同步队列 (Sorted Set)
用于后端感知新数据的产生。
- **Key**: `gov:data:new`
- **Member**: `dataId` (32位UUID)
- **Score**: `timestamp` (爬取时间戳)
- **用途**: 后端轮询或订阅此Key，获取最新的 `dataId` 列表。

### 2.2 数据详情存储 (Hash)
存储具体的新闻/公告内容。
- **Key**: `gov:data:{dataId}`
- **TTL**: 24小时 (请务必在此时间内完成同步)
- **字段定义**:

| 字段名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| `dataId` | String | 唯一ID (32位UUID) | `5320d15d8a2a4d659785ed0b82caa58d` |
| `title` | String | 标题 | `海南省2025年度公开遴选公务员公告` |
| `content` | String | 清洗后的纯文本正文 | `海南省公务员局...` |
| `publishTime` | String | 发布时间 (YYYY-MM-DD HH:mm:ss) | `2025-01-15 00:00:00` |
| `sourceUrl` | String | 原始链接 | `https://www.hainan.gov.cn/...` |
| `sourceWebsite` | String | 来源网站名称 | `海南省人民政府` |
| `publishDept` | String | 发布单位 | `海南省人民政府` |
| `category` | String | **分类标签 (核心)** | `招考招聘` / `人事任免` / `干部任前公示` |
| `attachments` | JSON | 附件列表 (已存MinIO) | `[{"name":"...","url":"http://minio/..."}]` |
| `crawlTime` | String | 爬取时间 | `2025-12-07 16:00:00` |
| `isNew` | String | 新数据标记 | `1` |

### 2.3 附件数据结构 (JSON)
`attachments` 字段是一个JSON字符串，解析后结构如下：
```json
[
  {
    "name": "附件标题.docx",
    "url": "http://minio-server:9000/gov-attachments/20251207/uuid/file.docx",
    "type": "docx",
    "size": 10240,
    "original_url": "https://gov.cn/file/original.docx"
  }
]
```
> **注意**: `url` 已经是MinIO的永久访问链接，前端可直接使用。

---

## 3. 后端对接流程建议

建议后端开发编写一个定时任务或守护进程（Consumer），按以下逻辑处理：

### 第一步：获取待处理数据
从 `gov:data:new` 获取最早的 N 条数据ID：
```python
# Python Redis 示例
# 获取分数范围内的成员 (0 到 当前时间戳)
data_ids = redis_client.zrangebyscore("gov:data:new", 0, current_timestamp, start=0, num=10)
```

### 第二步：读取详情并入库
遍历 `data_ids`，读取 Hash 数据：
```python
for data_id in data_ids:
    key = f"gov:data:{data_id}"
    data = redis_client.hgetall(key)
    
    if not data:
        continue
        
    # 1. 解析分类
    category = data.get('category') 
    # TODO: 根据 category 映射到后端数据库的 type_id
    # e.g. "招考招聘" -> type_id: 1
    
    # 2. 解析附件
    attachments = json.loads(data.get('attachments', '[]'))
    
    # 3. 写入 MySQL/PostgreSQL
    # INSERT INTO public_info (...) VALUES (...)
    
    # 4. 确认消费成功
    # 从待同步队列中移除
    redis_client.zrem("gov:data:new", data_id)
```

### 第三步：前端展示
- **接口返回**: 直接返回数据库中存储的字段。
- **分类筛选**: 前端请求带上 `category` 或对应的 `type_id`，后端从数据库筛选返回。
- **附件下载**: 直接返回 MinIO 的 `url` 字段给前端。

---

## 4. 注意事项
1. **字符编码**: Redis 读取时请确保使用 `utf-8` 解码（如 Java 的 `StringRedisTemplate`，Python 的 `decode_responses=True`）。
2. **幂等性**: `dataId` 是全局唯一的，建议在数据库 `data_id` 字段建立唯一索引，防止重复插入。
3. **容错**: 如果读取 Hash 为空（可能过期或被误删），应直接从 `gov:data:new` 移除该 ID。
