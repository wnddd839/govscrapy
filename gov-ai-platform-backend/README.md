# 后端本地开发与测试

- 启动依赖：Redis、MySQL、MinIO、Elasticsearch
- 运行：`mvn clean package -DskipTests` 后 `java -jar target/gov-ai-platform-backend-0.1.0.jar`
- Swagger UI：`http://localhost:8080/api/swagger-ui/index.html`
- 接口验证：
  - `GET http://localhost:8080/api/public-info/hot`
  - `GET http://localhost:8080/api/public-info/detail/{id}`
  - `GET http://localhost:8080/api/public-info/list?q=xxx&region=xxx&page=0&size=10`
  - `GET http://localhost:8080/api/file/preview/{object}`
  - `POST http://localhost:8080/api/ai/chat` body: `{ "question": "海南省公务员招考" }`
  - `GET http://localhost:8080/api/_health/db`

PowerShell 调用示例：
- 热门：`Invoke-RestMethod -Uri "http://localhost:8080/api/public-info/hot" -Method Get -Headers @{ Origin="http://localhost:5173" }`
- 列表：`Invoke-RestMethod -Uri "http://localhost:8080/api/public-info/list?q=就业&region=海南&page=0&size=10" -Method Get -Headers @{ Origin="http://localhost:5173" }`
- 详情：`Invoke-RestMethod -Uri "http://localhost:8080/api/public-info/detail/1" -Method Get -Headers @{ Origin="http://localhost:5173" }`
- 健康：`Invoke-RestMethod -Uri "http://localhost:8080/api/_health/db" -Method Get -Headers @{ Origin="http://localhost:5173" }`

安全配置：
- 允许来源：`security.allowed-origins`，示例 `http://localhost:5173,https://your-frontend-domain.com`
- 限流：`security.rate-limit.per-minute`，示例 `120`
