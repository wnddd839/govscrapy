# 分栏标记功能使用要求文档

## 1. 功能概述

为了解决人事分栏等栏目数据展示问题，后端添加了分栏标记功能。该功能允许爬虫在爬取数据时，根据数据来源的分栏信息，为每条数据打上分栏标记，前端则可以直接根据分栏标记查询对应栏目的数据，无需进行复杂的搜索或筛选。

## 2. 数据结构变更

### 2.1 新增字段

在`public_info`表中新增了`column_flag`字段，用于存储分栏标记：

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| column_flag | VARCHAR | NOT NULL, DEFAULT '' | 分栏标记，用于标识数据属于哪个分栏，例如："人事"、"政策"、"通知"等 |

### 2.2 实体类变更

在`PublicInfo`实体类中新增了`columnFlag`属性：

```java
/**
 * 分栏标记字段，用于标识数据属于哪个分栏
 * 例如："人事"、"政策"、"通知"等
 */
@Column(name = "column_flag", nullable = false, defaultValue = "")
private String columnFlag;
```

## 3. 爬虫端要求

### 3.1 数据爬取要求

1. **分栏标记规则**：
   - 爬虫在爬取数据时，必须根据数据来源的分栏信息，为每条数据设置`columnFlag`字段
   - 分栏标记必须与前端展示的栏目名称保持一致，例如："人事"、"政策"、"通知"等
   - 建议使用中文作为分栏标记，便于前端展示和理解

2. **数据存储要求**：
   - 爬虫在将数据存入Redis或直接写入数据库时，必须包含`columnFlag`字段
   - 对于已有数据，建议进行批量更新，添加适当的分栏标记

3. **分栏标记示例**：
   - 从人事栏目爬取的数据：`columnFlag = "人事"`
   - 从政策栏目爬取的数据：`columnFlag = "政策"`
   - 从通知栏目爬取的数据：`columnFlag = "通知"`

### 3.2 数据同步要求

1. **Redis数据格式**：
   - 爬虫存入Redis的数据必须包含`columnFlag`字段
   - 示例：
     ```json
     {
       "title": "关于2024年事业单位公开招聘工作人员的公告",
       "contentText": "根据工作需要，决定面向社会公开招聘事业单位工作人员...",
       "columnFlag": "人事",
       "publishDate": "2024-01-01"
     }
     ```

2. **数据库写入要求**：
   - 爬虫直接写入数据库时，必须设置`column_flag`字段的值
   - 建议使用SQL语句：
     ```sql
     INSERT INTO public_info (title, content_text, column_flag, publish_date) VALUES (?, ?, ?, ?);
     ```

## 4. 前端端要求

### 4.1 分栏数据查询

1. **新增API接口**：
   - 专门用于分栏查询的接口：`GET /api/public-info/column/{columnFlag}`
   - 支持分页查询，返回格式统一

2. **API使用示例**：
   - 查询人事分栏数据：`GET /api/public-info/column/人事?source=mysql&page=0&size=20`
   - 查询政策分栏数据：`GET /api/public-info/column/政策?source=mysql&page=0&size=20`
   - 查询通知分栏数据：`GET /api/public-info/column/通知?source=mysql&page=0&size=20`

3. **API响应格式**：
   ```json
   {
     "data": [...],     // 数据列表
     "total": 100,      // 总条数
     "page": 0,         // 当前页码
     "size": 20         // 每页条数
   }
   ```

### 4.2 现有API增强

1. **list接口增强**：
   - 原有`GET /api/public-info/list`接口添加了`columnFlag`参数支持
   - 可以通过`columnFlag`参数筛选特定分栏的数据
   - 示例：`GET /api/public-info/list?columnFlag=人事&source=mysql&page=0&size=20`

2. **hot接口**：
   - 保持原有功能不变
   - 可以通过扩展支持按分栏标记获取热门数据

### 4.3 前端展示要求

1. **分栏展示逻辑**：
   - 各分栏页面直接调用`/api/public-info/column/{columnFlag}`接口获取对应栏目的数据
   - 无需进行复杂的搜索或筛选，直接根据分栏标记查询
   - 示例：人事分栏页面调用`/api/public-info/column/人事`接口

2. **分页处理**：
   - 各分栏页面必须支持分页功能
   - 建议默认每页显示20条数据
   - 提供分页控件，允许用户切换页码

3. **数据刷新机制**：
   - 建议定期刷新数据，或提供手动刷新功能
   - 对于热门数据，可以考虑使用Redis缓存，提升加载速度

## 5. API使用示例

### 5.1 分栏查询示例

```bash
# 查询人事分栏数据，第1页，每页20条
curl -X GET "http://localhost:8080/api/public-info/column/人事?source=mysql&page=0&size=20"

# 查询政策分栏数据，第2页，每页50条
curl -X GET "http://localhost:8080/api/public-info/column/政策?source=mysql&page=1&size=50"

# 查询通知分栏数据，使用Redis数据源
curl -X GET "http://localhost:8080/api/public-info/column/通知?source=redis&page=0&size=20"
```

### 5.2 列表查询示例

```bash
# 查询人事分栏中包含"招聘"关键词的数据
curl -X GET "http://localhost:8080/api/public-info/list?columnFlag=人事&q=招聘&source=mysql&page=0&size=20"

# 查询政策分栏中2024年发布的数据
curl -X GET "http://localhost:8080/api/public-info/list?columnFlag=政策&startDate=2024-01-01&endDate=2024-12-31&source=mysql&page=0&size=20"
```

## 6. 注意事项

1. **分栏标记一致性**：
   - 爬虫设置的分栏标记必须与前端查询时使用的分栏标记保持一致
   - 建议建立分栏标记的统一管理机制，避免标记不一致导致数据查询错误

2. **数据更新机制**：
   - 对于已有数据，建议进行批量更新，添加适当的分栏标记
   - 新爬取的数据必须包含分栏标记

3. **性能考虑**：
   - 对于访问频繁的分栏，可以考虑使用Redis缓存，提升查询速度
   - 建议为`column_flag`字段添加索引，提升查询性能

4. **扩展性**：
   - 该设计支持后续添加更多分栏，只需在爬虫中添加对应的分栏标记即可
   - 前端可以根据需要动态添加新的分栏页面

## 7. 后续扩展建议

1. **分栏管理功能**：
   - 建议添加分栏管理功能，允许管理员动态添加、修改和删除分栏
   - 可以考虑在数据库中新增`column`表，存储分栏信息

2. **分栏统计功能**：
   - 建议添加分栏统计功能，统计各分栏的数据数量、更新频率等
   - 可以为管理员提供数据统计报表

3. **智能分栏功能**：
   - 后续可以考虑添加智能分栏功能，根据数据内容自动判断分栏
   - 可以使用AI技术，对数据进行分类和标记

## 8. 总结

分栏标记功能的添加，将大大简化前端分栏数据的查询和展示逻辑，提高系统性能和用户体验。爬虫端和前端需要按照上述要求进行相应的调整，确保功能的正常使用。

如有任何疑问或建议，欢迎随时与后端团队沟通。