# Gov AI Platform Backend - 部署指南

本项目已配置为支持云原生部署，所有敏感配置均通过环境变量注入。

## 1. 构建项目

在本地环境执行 Maven 构建：

```bash
mvn clean package -DskipTests
```

构建成功后，会在 `target` 目录下生成 `gov-ai-platform-backend-0.1.0.jar`。

## 2. 服务器部署要求

确保服务器已安装：
*   **Java 17 JRE** (推荐 Eclipse Temurin)
*   **MySQL 8.0+** (创建数据库 `gov_platform`)
*   **Redis 6.0+**
*   **MinIO** (用于文件存储)

## 3. 启动命令 (Linux/Shell)

请根据实际服务器环境修改环境变量：

```bash
#!/bin/bash

# === 数据库配置 ===
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_NAME="gov_platform"
export DB_USER="gov_user"
export DB_PASSWORD="YourStrongPassword"

# === Redis 配置 ===
export REDIS_HOST="127.0.0.1"
export REDIS_PORT="6379"
export REDIS_PASSWORD="YourRedisPassword"

# === MinIO 配置 ===
export MINIO_ENDPOINT="http://127.0.0.1:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="YourMinioSecret"
export MINIO_BUCKET="gov-attachments"

# === AI 模型配置 (通义千问) ===
export AI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
export AI_MODEL="qwen3-vl-flash"

# === 服务端口 ===
export SERVER_PORT="8080"

# 启动服务
nohup java -jar gov-ai-platform-backend-0.1.0.jar > app.log 2>&1 &
echo "Service started on port $SERVER_PORT"
```

## 4. Docker 部署 (可选)

如果使用 Docker，可以直接运行：

```bash
docker run -d \
  -p 8080:8080 \
  -e DB_HOST=192.168.1.10 \
  -e DB_PASSWORD=root \
  -e REDIS_HOST=192.168.1.10 \
  -e AI_API_KEY=sk-xxxx \
  --name gov-backend \
  gov-ai-backend:latest
```

## 5. 注意事项

1.  **数据库初始化**: 项目配置了 `ddl-auto: update`，首次启动会自动创建/更新表结构。
2.  **文件存储**: 确保 MinIO Bucket (`gov-attachments`) 已创建，且 Access Key 具有读写权限。
3.  **日志**: 启动日志输出到 `app.log`，可通过 `tail -f app.log` 查看。
