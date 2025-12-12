# 前端对接需求说明书 (Frontend Requirement Specification)

## 1. 背景与目标
根据最新的业务需求，前端页面需要严格区分**热门板块**和**分类板块**的数据来源。系统需要支持“双数据源”架构，即前端需具备明确指定从 Redis 或 MySQL 获取数据的能力，以确保业务逻辑的准确性和系统性能的分层测试。

## 2. 核心需求分析
系统需划分为两个明确的数据流向：

### 2.1 热门板块 (Hot Section)
*   **列表来源**: 必须强制从 **Redis** 获取数据。
*   **详情来源**: 用户从热门列表点击进入详情页时，**详情数据也必须从 Redis 获取**。
*   **业务逻辑**: 热门数据代表高频访问内容，必须通过缓存层（Redis）承载，严禁穿透到 MySQL，以保证高并发下的响应速度。

### 2.2 分类板块 (Category Section)
*   **列表来源**: 必须强制从 **MySQL** 获取数据。
*   **详情来源**: 用户从分类列表点击进入详情页时，**详情数据必须从 MySQL 获取**。
*   **业务逻辑**: 分类数据代表全量归档数据，通过数据库（MySQL）查询，确保数据的完整性和实时一致性。

## 3. 接口对接要求 (API Requirements)

虽然之前的反馈文档 (`FRONTEND_INTERFACE_FEEDBACK.md`) 提到后端已做自动降级，但为了满足上述严格的业务隔离需求，前端**必须**能够显式控制数据源。请后端配合支持以下参数：

### 3.1 详情页接口 (Detail API)
前端将根据用户入口（热门 vs 分类）传递 `source` 参数，请后端务必处理该参数。

*   **接口地址**: `/public-info/detail/data/{dataId}`
*   **请求方式**: `GET`
*   **新增参数**: `source` (Query Param)
    *   `source=redis`: 强制从 Redis 读取详情。如果 Redis 中不存在，应返回错误或 null（不应自动降级查 MySQL，以便前端排查缓存同步问题）。
    *   `source=mysql`: 强制从 MySQL 读取详情。
    *   *不传参数*: 保持原有逻辑（自动降级）。

**前端调用示例**:
```javascript
// 从热门进入
GET /public-info/detail/data/10086?source=redis

// 从分类进入
GET /public-info/detail/data/10086?source=mysql
```

### 3.2 热门列表接口 (Hot List API)
*   **接口地址**: `/public-info/hot/list`
*   **请求方式**: `GET`
*   **建议**: 建议后端确认此接口仅返回 Redis 中的数据。

### 3.3 分类数据接口 (Category Data API)
*   **接口地址**: `/public-info/category/data`
*   **请求方式**: `GET`
*   **参数**: `source=mysql` (前端将显式传递此参数)
*   **建议**: 请确保此接口直接查询数据库。

## 4. 前端实现方案 (Frontend Implementation)

前端已完成以下改造，等待后端接口支持：

1.  **HomeView (热门)**: 点击卡片时，路由跳转携带 `query: { source: 'redis' }`。
2.  **CategoryView (分类)**: 
    *   获取列表时传递 `params: { source: 'mysql' }`。
    *   点击列表项时，路由跳转携带 `query: { source: 'mysql' }`。
3.  **DetailView (详情)**: 页面加载时优先读取 URL 参数中的 `source`，并将其透传给详情 API。

## 5. 待解决问题 (Pending Issues)
*   目前前端传递 `source` 参数后，部分详情页仍然无法正常加载（可能是 404 或 500，或数据为空）。
*   请后端开发人员检查 `/public-info/detail/data/{dataId}` 接口：
    1.  是否正确接收并处理了 `source` 参数？
    2.  当 `source=redis` 时，如果 Redis Key 规则与 ID 不匹配，是否导致查不到数据？

请尽快确认以上对接标准，确保双数据源逻辑闭环。
