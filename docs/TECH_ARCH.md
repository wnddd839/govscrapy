# 政务信息整合+AI对话平台 项目文档（Redis+JPA+Lombok版）
## 文档目录
1. 项目基础信息
2. 环境准备清单
3. 项目结构细分
4. 核心配置明细
5. 模块开发优先级
6. 联调与测试要点
7. 部署流程简化
8. 后续扩展方向

## 1. 项目基础信息
| 项目项         | 详情                                                                 |
|----------------|----------------------------------------------------------------------|
| 项目名称       | 政务信息整合+AI对话平台                                              |
| 核心目标       | 政务信息检索+AI智能问答（基于RAG架构），快速落地MVP                  |
| 技术栈核心     | 后端：Spring Boot 3 + JPA + Lombok + Redis + Elasticsearch + MinIO   |
|                | 前端：Vue 3 + Vite + Element Plus + TailwindCSS + Axios              |
| 数据来源       | 现有爬虫采集的`public_info`表（MySQL）+ 本地附件                     |
| 核心亮点       | 热门数据Redis缓存（性能优化）、JPA简化数据库操作、AI基于政务数据问答 |
| 开发周期       | 7天（MVP落地）                                                       |

## 2. 环境准备清单（按模块分类）
### 2.1 基础开发环境
| 环境项         | 版本要求                  | 验证方式                                  |
|----------------|---------------------------|-------------------------------------------|
| JDK            | 17+                       | 终端输入`java -version`，显示17+版本       |
| Node.js        | 18+                       | 终端输入`node -v`，显示18+版本             |
| MySQL          | 8.x                       | 连接数据库`gov_platform`，验证表`public_info`存在 |
| Redis          | 6.x+                      | 终端输入`redis-cli ping`，返回`PONG`       |
| IDE工具        | IntelliJ IDEA（后端）+ VS Code（前端） | IDEA安装Lombok插件，VS Code安装Vue插件     |
| Docker（可选） | 最新稳定版                | 启动Docker后，可正常拉取MinIO/ES镜像       |

### 2.2 中间件部署清单
| 中间件         | 部署方式                  | 核心配置/验证点                          |
|----------------|---------------------------|-------------------------------------------|
| MinIO          | Docker/本地安装           | 1. 端口9000（API）+ 9001（控制台）；2. 创建存储桶`gov-attachments`；3. 账号`minioadmin/minioadmin` |
| Elasticsearch  | Docker/本地安装           | 1. 端口9200；2. 关闭安全校验；3. 访问`http://localhost:9200`返回JSON |
| Redis          | 本地安装                  | 1. 端口6379；2. 无密码（开发环境）；3. 启动后可正常读写 |

## 3. 项目结构细分（按前后端+模块）
### 3.1 后端项目结构（`gov-ai-platform-backend`）
```
com.gov.ai
├── 启动类模块
│   └── GovAiPlatformBackendApplication.java  // 主启动类（加@SpringBootApplication）
├── 配置模块（config）
│   ├── JpaConfig.java        // JPA分页/事务配置（可选）
│   ├── RedisConfig.java      // Redis序列化+缓存管理器配置
│   ├── ElasticsearchConfig.java  // ES客户端配置
│   ├── MinioConfig.java      // MinIO客户端配置
│   └── AiClientConfig.java   // 通义千问SDK配置
├── 缓存模块（cache）
│   ├── constant/CacheKeyConstant.java  // 缓存Key常量（热门信息/详情Key）
│   └── util/RedisCacheUtil.java        // Redis操作工具类（set/get/delete）
├── 实体模块（entity）
│   └── PublicInfo.java       // JPA实体（Lombok+JPA注解，映射public_info表）
├── 数据访问模块（repository）
│   └── PublicInfoRepository.java  // JPA Repository（内置CRUD+自定义查询方法）
├── 业务逻辑模块（service）
│   ├── PublicInfoService.java      // 政务信息查询接口（热门/列表/详情）
│   ├── EsSyncService.java          // ES数据同步接口（MySQL→ES）
│   ├── AiChatService.java          // AI对话接口（RAG核心）
│   └── impl/                       // 实现类
│       ├── PublicInfoServiceImpl.java  // 含Redis缓存逻辑+JPA查询
│       ├── EsSyncServiceImpl.java      // ES同步实现
│       └── AiChatServiceImpl.java      // AI+ES检索实现
├── 接口模块（controller）
│   ├── PublicInfoController.java  // 政务信息接口（/api/public-info/*）
│   ├── FileController.java        // 附件接口（预览/下载，/api/file/*）
│   └── AiChatController.java      // AI对话接口（/api/ai/chat）
├── 数据传输模块（dto）
│   ├── request/                   // 请求DTO（如AiChatRequest.java）
│   └── response/                  // 响应DTO（如PublicInfoListResponse.java）
└── 工具模块（util）
    ├── DateUtil.java              // 日期格式化工具
    └── MinioFileUtil.java         // MinIO文件操作工具（可选）
```

### 3.2 前端项目结构（`gov-ai-platform-frontend`）
```
src/
├── 静态资源模块（assets）
│   ├── main.css                 // 全局样式（Tailwind+Element Plus引入）
│   └── images/                  // 图片资源（logo等）
├── 公共组件模块（components）
│   ├── Header.vue               // 头部（导航+搜索框）
│   ├── Footer.vue               // 底部（版权信息）
│   └── AiSidebar.vue            // AI对话侧边栏（详情页用）
├── 路由模块（router）
│   └── index.js                 // 路由配置（首页/搜索结果/详情页）
├── 接口请求模块（api）
│   ├── index.js                 // Axios配置（基础路径+拦截器）
│   ├── publicInfoApi.js         // 政务信息接口请求
│   ├── fileApi.js               // 附件接口请求
│   └── aiChatApi.js             // AI对话接口请求
├── 页面视图模块（views）
│   ├── HomeView.vue             // 首页（热门信息+快捷搜索）
│   ├── SearchResultView.vue     // 搜索结果页（列表+筛选+AI答案）
│   └── DetailView.vue           // 详情页（正文+附件+AI侧边栏）
├── 根组件（App.vue）            // 布局容器（头部+路由视图+底部）
└── 入口文件（main.js）           // Vue初始化+路由+组件注册
```

## 4. 核心配置明细（关键配置项）
### 4.1 后端配置（`application.yml`）
```yaml
# 数据库配置
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/gov_platform?useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true
    username: 你的MySQL用户名
    password: 你的MySQL密码
    driver-class-name: com.mysql.cj.jdbc.Driver
  # JPA核心配置
  jpa:
    hibernate:
      ddl-auto: validate  # 仅校验表结构（不修改）
      naming:
        physical-strategy: org.hibernate.boot.model.naming.PhysicalNamingStrategyStandardImpl
    properties:
      hibernate:
        dialect: org.hibernate.dialect.MySQL8Dialect
        format_sql: true  # 格式化SQL日志
        show_sql: true    # 打印SQL
    open-in-view: false
  # Redis配置
  redis:
    host: localhost
    port: 6379
    password: ""
    timeout: 3000
    lettuce:
      pool:
        max-active: 8
        max-idle: 8
        min-idle: 2
  # ES配置
  elasticsearch:
    rest:
      uris: http://localhost:9200

# MinIO配置
minio:
  endpoint: http://localhost:9000
  access-key: minioadmin
  secret-key: minioadmin
  bucket-name: gov-attachments

# AI配置
ai:
  tongyi:
    api-key: 你的通义千问API密钥
    model: qwen-turbo
    base-url: https://dashscope.aliyuncs.com/api/v1

# 服务器配置
server:
  port: 8080
  servlet:
    context-path: /api

# 缓存过期配置
cache:
  hot-info:
    expire-seconds: 3600  # 热门信息缓存1小时
```

### 4.2 前端核心配置
#### 4.2.1 Axios配置（`src/api/index.js`）
```javascript
import axios from 'axios';
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api',
  timeout: 10000
});
// 请求/响应拦截器（简化版）
service.interceptors.response.use(res => res.data, err => Promise.reject(err));
export default service;
```

#### 4.2.2 路由配置（`src/router/index.js`）
```javascript
import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import SearchResultView from '../views/SearchResultView.vue';
import DetailView from '../views/DetailView.vue';

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/search', name: 'searchResult', component: SearchResultView },
  { path: '/detail/:id', name: 'detail', component: DetailView, props: true }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});
export default router;
```

## 5. 模块开发优先级（按阶段划分）
### 阶段1：基础环境与核心依赖（1天）
| 优先级 | 开发项                     | 关键产出                                  |
|--------|----------------------------|-------------------------------------------|
| P0     | 后端项目初始化（Spring Boot+JPA+Lombok+Redis） | 项目骨架+依赖配置完成                      |
| P0     | 中间件部署（MinIO+ES+Redis） | 中间件启动成功，可正常访问                |
| P1     | 前端项目初始化（Vue 3+Vite+Element Plus） | 前端骨架+路由配置完成                      |

### 阶段2：后端核心功能（2天）
| 优先级 | 开发项                     | 关键产出                                  |
|--------|----------------------------|-------------------------------------------|
| P0     | JPA实体+Repository开发     | PublicInfo实体（映射表）+ 基础查询方法     |
| P0     | Redis配置+缓存工具类       | Redis序列化正常，可读写缓存                |
| P0     | 政务信息服务（热门+详情+列表） | 支持缓存查询，JPA多条件筛选                |
| P1     | ES数据同步服务             | MySQL数据同步到ES索引                      |
| P1     | 附件迁移脚本+文件接口      | 本地附件上传MinIO，支持预览/下载          |
| P0     | AI对话服务（RAG）          | 支持“ES检索→Prompt构建→AI调用”流程         |

### 阶段3：前端核心功能（2天）
| 优先级 | 开发项                     | 关键产出                                  |
|--------|----------------------------|-------------------------------------------|
| P0     | 首页开发（热门信息+搜索框） | 热门信息加载，搜索/AI按钮跳转              |
| P0     | 详情页开发（正文+附件）    | 正文展示，PDF预览/下载功能                |
| P1     | 搜索结果页开发（列表+筛选） | 支持关键词/地区/时间筛选，分页展示        |
| P0     | AI对话组件开发             | 首页AI问答+详情页侧边栏问答                |

### 阶段4：联调与优化（1天）
| 优先级 | 开发项                     | 关键产出                                  |
|--------|----------------------------|-------------------------------------------|
| P0     | 前后端接口联调             | 所有接口正常通信，数据展示正确            |
| P1     | 缓存功能验证               | 热门信息/详情缓存命中，性能提升            |
| P1     | 样式优化+响应式适配        | 支持PC/移动端正常显示                      |
| P2     | 异常处理完善               | 空数据/接口报错友好提示                    |

## 6. 联调与测试要点
### 6.1 后端接口测试（Postman/浏览器）
| 接口路径                  | 测试要点                                  | 预期结果                                  |
|---------------------------|-------------------------------------------|-------------------------------------------|
| /api/public-info/hot      | 首次访问/二次访问日志                      | 首次查库，二次查缓存                      |
| /api/public-info/detail/1 | 不存在ID/存在ID                           | 404提示/返回详情数据                      |
| /api/public-info/list     | 传地区/时间参数                           | 筛选结果正确                              |
| /api/file/preview/xxx.pdf | 访问MinIO中存在的PDF                       | 在线预览成功                              |
| /api/ai/chat              | 传政务相关问题（如“海南省公务员招考”）      | 返回AI答案+来源引用                        |

### 6.2 前端功能测试
| 功能点                     | 测试要点                                  | 预期结果                                  |
|----------------------------|-------------------------------------------|-------------------------------------------|
| 首页热门信息加载           | 页面刷新                                  | 3秒内加载完成，显示最新5条                |
| 搜索功能                   | 输入关键词搜索                            | 跳转到结果页，展示匹配数据                |
| AI问答功能                 | 输入政务问题点击AI问答                     | 结果页显示AI答案+来源标签                  |
| 详情页附件预览             | 点击预览按钮                              | 弹窗显示PDF内容                            |
| 响应式适配                 | 缩小浏览器窗口/用手机访问                 | 布局不错乱，功能正常使用                  |

### 6.3 缓存测试
| 测试项                     | 操作步骤                                  | 预期结果                                  |
|----------------------------|-------------------------------------------|-------------------------------------------|
| 热门信息缓存               | 1. 访问/hot；2. 查看Redis缓存；3. 再次访问 | Redis存在缓存Key，二次访问日志显示“查缓存” |
| 详情缓存                   | 1. 访问/detail/1；2. 查看Redis；3. 再次访问 | 缓存存在，响应时间≤10ms                   |
| 缓存刷新                   | 调用/refresh-hot-cache接口后访问/hot       | 重新查库，更新缓存                        |

## 7. 部署流程简化（本地演示/服务器）
### 7.1 本地演示部署（开发环境）
1. 启动中间件：Redis→MySQL→MinIO→Elasticsearch
2. 后端部署：
   - 执行附件迁移脚本（本地附件→MinIO+更新数据库）
   - 启动Spring Boot项目（端口8080）
   - 访问`http://localhost:8080/api/public-info/hot`验证接口
3. 前端部署：
   - 终端执行`npm run dev`
   - 访问前端地址（如`http://127.0.0.1:5173`）

### 7.2 服务器部署（简化版）
1. 服务器安装：MySQL+Redis+Docker（部署MinIO/ES）
2. 后端部署：
   - 打包：`mvn clean package -Dmaven.test.skip=true`
   - 上传jar包，执行`java -jar xxx.jar`（后台运行）
3. 前端部署：
   - 打包：`npm run build`
   - 上传dist目录到Nginx静态资源目录
   - 配置Nginx反向代理（前端→后端接口）

## 8. 后续扩展方向（按优先级）
### 8.1 功能扩展
| 优先级 | 扩展项                     | 实现思路                                  |
|--------|----------------------------|-------------------------------------------|
| P1     | AI多轮对话                 | Redis存储对话上下文，Prompt携带历史记录    |
| P1     | 用户系统（登录/收藏）      | Spring Security+JWT，收藏数据存MySQL+Redis缓存 |
| P2     | 政策标签分类               | 爬虫新增标签字段，前端支持标签筛选        |

### 8.2 技术优化
| 优先级 | 优化项                     | 实现思路                                  |
|--------|----------------------------|-------------------------------------------|
| P1     | AI答案缓存                 | Redis缓存高频问题答案，减少API调用成本     |
| P1     | 接口限流                   | Redis实现接口限流，防止恶意请求            |
| P2     | 分布式部署支持             | 配置中心（Nacos）管理多环境配置            |

### 8.3 体验优化
| 优先级 | 优化项                     | 实现思路                                  |
|--------|----------------------------|-------------------------------------------|
| P1     | 搜索联想功能               | ES前缀匹配，前端输入时实时返回联想关键词  |
| P2     | 多格式附件预览             | 集成LibreOffice转换，支持Word/Excel预览    |
| P2     | 政策对比功能               | 前端支持多选政策，展示差异点              |