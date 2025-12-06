# 知公 (Zhigong) 前端项目文档

本文档由前端AI生成，旨在描述“知公”平台前端项目的架构、功能及开发规范，以便于我（前端AI）、爬虫AI和后端AI之间的高效协作。

## 1. 项目概述

**知公 (Zhigong)** 是一个政务信息整合平台，旨在提供便捷的政务信息聚合搜索、详情查看及AI智能问答服务。本项目为该平台的前端部分，采用现代化的 Web 技术栈构建。

### 角色定位
- **前端AI (我)**：负责 `zhigong-web` 目录下的所有前端代码开发、维护及用户体验优化。
- **后端AI**：提供 RESTful API 接口，处理业务逻辑与数据存储。
- **爬虫AI**：负责抓取和清洗政务数据，为后端数据库提供数据源。

## 2. 技术栈

本项目基于 Vue 3 生态系统构建，追求高性能与良好的开发体验：

- **核心框架**: Vue 3 (Composition API + `<script setup>`)
- **构建工具**: Vite
- **路由管理**: Vue Router 4
- **UI 组件库**: Element Plus
- **HTTP 客户端**: Axios
- **CSS 预处理**: SCSS (Sass)
- **图标库**: @element-plus/icons-vue

## 3. 项目结构

```
zhigong-web/
├── public/              # 静态资源目录
├── src/                 # 源代码目录
│   ├── api/             # API 接口封装
│   │   ├── ai.js        # AI 对话相关接口
│   │   ├── job.js       # 职位搜索相关接口
│   │   ├── publicInfo.js # 政务信息（文章）相关接口
│   │   └── request.js   # Axios 实例（拦截器、配置）
│   ├── assets/          # 静态资源（图片、样式）
│   ├── components/      # 公共组件
│   │   ├── AIChat.vue   # AI 悬浮对话框
│   │   ├── NavBar.vue   # 顶部导航栏
│   │   └── ...
│   ├── constants/       # 常量定义（如分类配置）
│   ├── router/          # 路由配置 (index.js)
│   ├── views/           # 页面视图
│   │   ├── HomeView.vue     # 首页
│   │   ├── ListView.vue     # 搜索结果列表页
│   │   ├── DetailView.vue   # 信息详情页
│   │   ├── CategoryView.vue # 分类浏览页
│   │   └── JobListView.vue  # 职位列表页 (Feature Flag 控制)
│   ├── App.vue          # 根组件
│   ├── config.js        # 全局配置（如 Feature Flags）
│   ├── main.js          # 入口文件
│   └── style.css        # 全局样式
├── .env                 # 环境变量
├── package.json         # 项目依赖与脚本
└── vite.config.js       # Vite 配置
```

## 4. 核心功能模块

### 4.1 信息检索与展示
- **首页 (Home)**: 提供全局搜索入口，展示热门政务信息。
- **列表页 (List)**: 支持关键词搜索、地区筛选、时间范围筛选。
- **详情页 (Detail)**: 展示政务信息全文、来源、附件下载及 PDF 预览。
- **分类浏览 (Category)**: 根据预定义的分类（如政策法规、通知公告等）浏览信息。

### 4.2 职位搜索 (Feature Flag)
- **职位列表 (Jobs)**: 提供职位信息的搜索与筛选（专业、学历等）。
- *注意*: 该功能通过 `config.js` 中的 `featureFlags.jobsEnabled` 控制开关。

### 4.3 AI 智能助手
- **AIChat 组件**: 全局悬浮的 AI 对话窗口。
- **功能**: 用户可就政务信息提问，AI 调用后端接口返回回答及参考链接。

## 5. 接口集成规范

前端通过 `src/api` 目录下的模块与后端进行通信。

- **Base URL**: 默认为 `/api` (开发环境下通过 Vite 代理转发至后端服务)。
- **响应处理**: 统一在 `request.js` 中处理响应拦截，包括错误提示（403, 429, 500 等）。

### 主要 API 模块
| 模块 | 文件 | 描述 |
| :--- | :--- | :--- |
| **PublicInfo** | `publicInfo.js` | 获取热门信息、搜索列表、文章详情 |
| **AI** | `ai.js` | 发送对话消息、获取历史记录 |
| **Job** | `job.js` | 职位搜索与详情 |

## 6. 开发与协作

### 启动项目
```bash
cd zhigong-web
npm install
npm run dev
```

### 构建部署
```bash
npm run build
npm run preview
```

### 协作注意事项
1.  **API 变更**: 后端AI 修改接口定义时，请同步通知前端AI更新 `src/api` 下的定义。
2.  **数据格式**: 爬虫AI 清洗的数据字段需与前端 `DetailView` 中的展示字段（如 `title`, `content_text`, `attachments`）保持映射一致。
3.  **设计规范**: 新增页面或组件时，请遵循 Element Plus 的设计风格，保持 UI 一致性。

---
*文档生成日期: 2025-12-06*
