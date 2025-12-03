# 系统集成与部署指南 (INTEGRATION_GUIDE)

本文档旨在指导后端、爬虫与前端团队进行系统集成、部署及联调。

## 1. 部署架构概览

- **服务器 IP**: `8.138.24.168`
- **基础中间件**:
    - **MySQL**: 端口 3306, 数据库 `gov_platform`
    - **Redis**: 端口 6379, 密码 `123456`
    - **MinIO**: 端口 9000 (API) / 19003 (Console), Bucket `gov-attachments`
- **后端服务**: 运行于服务器本地 (Port 8080)
- **爬虫服务**: 计划独立部署，通过 Redis 与后端交互
- **前端服务**: Nginx 托管静态资源，反向代理到后端

---

## 2. 爬虫团队对接指南 (Crawler)

爬虫服务通过 **Redis** 将采集的数据推送给后端，后端通过异步任务入库。

### 2.1 Redis 连接信息
- **Host**: `8.138.24.168`
- **Port**: `6379`
- **Password**: `123456`
- **DB**: `0` (默认)

### 2.2 数据写入协议
爬虫需完成两个步骤来提交数据：

**步骤 1: 写入数据详情 (String JSON)**
- **Key 格式**: `crawl:data:{date}:{id}`
    - `{date}`: 采集日期，格式 `yyyyMMdd` (如 `20231027`)
    - `{id}`: 数据唯一标识 (如 UUID 或 原网站 ID)
- **Value**: JSON 字符串，结构如下：
```json
{
  "title": "海南省2024年公务员招考公告",
  "sourceOrg": "海南省人力资源和社会保障厅",
  "sourceUrl": "http://hrss.hainan.gov.cn/...",
  "publishDate": "2024-01-15",
  "region": "海南",
  "contentText": "公告正文内容...",
  "attachments": [
    {
      "name": "职位表.xls",
      "url": "http://.../file.xls", 
      "type": "xls" 
    },
    {
      "name": "报名指南.pdf",
      "url": "http://.../guide.pdf",
      "type": "pdf"
    }
  ]
}
```
> **注意**: `attachments` 必须是一个 JSON 数组。如果是上传到 MinIO 的文件，`url` 请填写 MinIO 的访问地址或对象名。

**步骤 2: 加入待同步队列 (Set)**
- **Key**: `crawl:pending:ids`
- **Member**: `{date}:{id}` (即步骤 1 Key 的后缀)
    - 示例: `20231027:abc-123`

**示例流程**:
1. SET `crawl:data:20231027:1001` `{"title":...}`
2. SADD `crawl:pending:ids` `20231027:1001`

---

## 3. 前端团队对接指南 (Frontend)

### 3.1 接口基础信息
- **Base URL**: `http://8.138.24.168:8080/api` (开发调试) / 生产环境通常通过 Nginx 转发 `/api`
- **CORS**: 后端已开启跨域支持 `*`

### 3.2 核心接口清单

| 功能 | 方法 | 路径 | 参数说明 |
| --- | --- | --- | --- |
| **热门信息** | GET | `/public-info/hot` | `region` (可选，地区筛选) |
| **搜索列表** | GET | `/public-info/list` | `q` (关键词), `region`, `page` (从0开始), `size` |
| **详情查询** | GET | `/public-info/detail/{id}` | `id` (主键ID) |
| **AI 问答** | POST | `/ai/chat` | Body: `{ "question": "..." }` |
| **文件预览** | GET | `/file/preview/{objectName}` | `objectName` (附件路径), 返回内联预览 URL |

### 3.3 附件预览特别说明 (PDF)
为了支持浏览器内直接预览 PDF（而非下载），请遵循以下逻辑：
1. 获取详情接口返回的 `attachments` 数组。
2. 如果 `type` 为 `pdf`，调用 `/file/preview/{objectName}` 接口获取一个 **预签名 URL**。
3. 使用该 URL 在 `<iframe>` 或 `pdf.js` 中加载。
    - 后端已配置 `Content-Disposition: inline` 和正确的 `Content-Type`。

---

## 4. 后端部署与运维 (Backend)

### 4.1 打包
在本地开发环境执行：
```bash
mvn clean package -DskipTests
```
生成 `target/gov-ai-platform-backend-0.1.0.jar`。

### 4.2 服务器部署
将 Jar 包上传至服务器 `/www/wwwroot/gov-backend/` (或其他目录)。

**启动命令 (生产环境)**:
```bash
# 确保服务器已安装 Java 17+
# 使用 application-prod.yml 配置
nohup java -jar -Dspring.profiles.active=prod gov-ai-platform-backend-0.1.0.jar > app.log 2>&1 &
```

**环境验证**:
- 查看日志: `tail -f app.log`
- 检查端口: `netstat -tlnp | grep 8080`
- 触发同步: `curl -X POST http://localhost:8080/api/admin/sync/db` (手动触发 Redis->MySQL 同步)

### 4.3 常见问题
- **数据库连接失败**: 检查 `application-prod.yml` 中的 MySQL 密码及 Host (默认 `127.0.0.1`)。
- **Redis 连接失败**: 确保 Redis 密码正确且未开启仅本地访问模式（如果爬虫在远程）。
