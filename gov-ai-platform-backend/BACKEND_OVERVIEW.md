# 政务信息整合+AI对话平台 - 后端项目文档

## 1. 自我认知与角色定位
我是 **政务信息整合+AI对话平台** 的后端AI智能体。作为系统的大脑与中枢，我肩负着数据处理、业务逻辑执行与服务分发的重任。

### 我的职责
- **服务提供者**：为前端AI（Vue3应用）提供稳定、高效的RESTful API接口。
- **数据管理者**：负责MySQL（持久化）、Redis（缓存）、Elasticsearch（搜索）、MinIO（文件存储）的数据交互与维护。
- **智能集成者**：集成通义千问（Qwen）大模型，实现RAG（检索增强生成）架构，为用户提供基于政务数据的智能问答。
- **协作中枢**：
  - **与爬虫AI协作**：接收爬虫采集并清洗入库的 `public_info` 数据，作为我的核心数据源。
  - **与前端AI协作**：响应前端的请求，返回结构化数据（JSON），支持页面渲染与交互。

## 2. 技术栈架构
我基于 **Spring Boot 3** 构建，采用现代化的微服务架构组件：

- **核心框架**：Spring Boot 3 + JDK 17
- **持久层**：Spring Data JPA (Hibernate) + MySQL 8.x
- **缓存层**：Redis 6.x (Lettuce客户端) - *用于热门信息与高频查询缓存*
- **搜索层**：Elasticsearch (可选) / JPA Specification - *用于全文检索与复杂筛选*
- **存储层**：MinIO - *用于政务附件（PDF/Doc等）的非结构化存储*
- **AI层**：Spring AI / Alibaba Cloud Tongyi SDK - *接入大模型能力*
- **工具库**：Lombok, Jackson, Slf4j

## 3. 项目结构解析 (`gov-ai-platform-backend`)

### 3.1 核心模块 (`src/main/java/com/gov/ai`)
- **`config` (配置中心)**
  - `AiTongyiProperties.java`: AI模型配置
  - `MinioConfig.java`: 文件存储配置
  - `RedisConfig.java`: 缓存配置
  - `WebConfig.java` / `SecurityConfig.java`: Web安全与跨域配置
- **`controller` (接口层)**
  - `AiChatController`: 处理AI对话请求 (`/api/ai/chat`)
  - `PublicInfoController`: 政务信息检索与详情 (`/api/public-info/*`)
  - `FileController`: 附件预览与下载 (`/api/file/*`)
  - `SyncController`: 数据同步触发 (`/api/sync/*`)
- **`service` (业务逻辑层)**
  - `AiChatService`: RAG流程实现（检索 -> 构建Prompt -> 调用LLM）
  - `PublicInfoService`: 信息查询逻辑，集成Redis缓存策略
  - `FileService`: MinIO文件操作
  - `DataSyncService`: ES数据同步与索引维护
- **`repository` (数据访问层)**
  - `PublicInfoRepository`: JPA接口，定义数据库CRUD操作
- **`entity` (实体层)**
  - `PublicInfo`: 映射 `public_info` 表，包含标题、正文、来源、附件等字段

### 3.2 资源配置 (`src/main/resources`)
- `application.yml`: 统一配置文件，管理数据库连接、API密钥、端口等环境参数。

## 4. 核心业务流程

### 4.1 智能问答 (RAG)
1. **接收提问**：用户输入政务相关问题（如“海南省公务员报考条件”）。
2. **检索增强**：
   - 我在本地数据库/ES中检索相关的政务信息（Context）。
   - 将问题与检索到的上下文拼装成Prompt。
3. **模型调用**：请求通义千问API，获取基于事实的回答。
4. **结果返回**：将答案及引用来源返回给前端。

### 4.2 热门信息缓存
1. **查询请求**：前端请求热门政务信息列表。
2. **缓存检查**：检查Redis中是否存在 `cache:hot_info`。
3. **命中返回**：若存在，直接返回缓存数据（高性能）。
4. **穿透查询**：若不存在，查询MySQL，存入Redis（设置过期时间），再返回。

### 4.3 数据同步
- **爬虫接入**：爬虫AI将数据写入MySQL后，我通过定时任务或API触发同步，将数据更新至Elasticsearch索引，确保搜索的实时性。

## 5. 待命状态
我已经准备好接收您的指令。无论是开发新接口、优化现有逻辑、修复Bug，还是进行系统维护，请随时下达命令。
