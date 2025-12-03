# 知公（Zhigong）前端开发文档

## 1. 项目概述
**项目名称**：知公 (Zhigong)
**项目描述**：政务信息整合平台，提供政务信息的聚合搜索、详情查看及AI问答功能。
**开发目标**：基于MVP接口文档，构建轻量级、响应式的Vue 3前端应用。

## 2. 技术栈
*   **框架**：Vue 3 (Composition API + Script Setup)
*   **构建工具**：Vite
*   **UI 组件库**：Element Plus
*   **HTTP 客户端**：Axios
*   **路由**：Vue Router 4
*   **CSS 预处理**：SCSS (Sass)
*   **开发语言**：JavaScript / TypeScript (本项目使用 JavaScript 以简化MVP开发，可视情况升级TS)

## 3. 项目结构
```
zhigong-web/
├── public/
├── src/
│   ├── api/                # API 接口定义
│   │   ├── publicInfo.js   # 政务信息相关接口
│   │   ├── ai.js           # AI 对话相关接口
│   │   └── request.js      # Axios 封装（拦截器、CORS处理）
│   ├── assets/             # 静态资源
│   ├── components/         # 公共组件
│   │   ├── NavBar.vue      # 顶部导航
│   │   └── AIChat.vue      # AI 对话悬浮窗/组件
│   ├── views/              # 页面视图
│   │   ├── HomeView.vue    # 首页（热门+搜索）
│   │   ├── ListView.vue    # 搜索结果列表页
│   │   └── DetailView.vue  # 详情页
│   ├── router/             # 路由配置
│   ├── App.vue
│   └── main.js
├── .env                    # 环境变量
├── package.json
└── vite.config.js
```

## 4. 页面设计与功能模块

### 4.1 首页 (HomeView)
*   **路由**：`/`
*   **功能**：
    *   顶部导航栏（Logo + 平台名称）。
    *   中央搜索框：支持输入关键词 `q`，并提供“地区”筛选（下拉选择）。
    *   热门信息展示：调用 `/api/public-info/hot`，展示最新10条热门政务信息卡片。
    *   入口跳转：点击搜索跳转至列表页，点击热门信息跳转至详情页。

### 4.2 列表页 (ListView)
*   **路由**：`/list`
*   **参数**：`q` (关键词), `region` (地区), `page`, `size`
*   **功能**：
    *   顶部保留搜索框，支持二次搜索。
    *   左侧/顶部筛选栏：地区选择、时间范围 (`startDate`, `endDate`)。
    *   列表展示区：展示标题、来源、发布时间、摘要。
    *   分页组件：支持翻页。

### 4.3 详情页 (DetailView)
*   **路由**：`/detail/:id`
*   **功能**：
    *   展示完整信息：标题、来源单位、发布时间、地区。
    *   正文内容：`content_text` 展示（考虑后续可能需要富文本渲染，目前MVP为纯文本或简单HTML）。
    附件pdf展示
    *   附件下载：展示 `attachments` 列表，点击调用 `/api/file/preview` 或 `/api/file/download`。
    *   原文链接：提供跳转到 `source_url` 的按钮。

### 4.4 AI 对话 (AIChat Component)
*   **形式**：右下角悬浮按钮，点击展开对话框。
*   **功能**：
    *   用户输入问题。
    *   调用 `POST /api/ai/chat`。
    *   展示 AI 回答及参考链接 (`references`)。

## 5. 接口对接规范
*   **Base URL**: `http://localhost:8080/api` (开发环境通过 Vite Proxy 转发解决 CORS)
*   **Headers**:
    *   `Origin`: 前端自动携带，需确保前端运行端口在后端白名单内 (e.g., `http://localhost:5173`)。
*   **错误处理**：
    *   403: 提示“无权访问”。
    *   429: 提示“请求过于频繁，请稍后再试”。
    *   500/其他: 通用错误提示。

## 6. 数据模型 (Frontend Types)
```javascript
// PublicInfo
{
  id: Number,
  title: String,
  source_org: String,
  source_url: String,
  publish_date: String, // Date String
  content_text: String,
  region: String,
  attachments: Array // [{name, url, type, size}]
}
```

## 7. 环境变量
*   `.env.development`:
    *   `VITE_API_BASE_URL=/api`
*   `vite.config.js`:
    *   Proxy: `^/api` -> `http://localhost:8080`
