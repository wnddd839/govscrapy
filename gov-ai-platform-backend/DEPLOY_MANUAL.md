# Gov AI Platform Backend - 部署手册

本手册指导如何将后端服务部署到 Linux 服务器。

## 1. 准备工作

确保服务器已安装以下环境：
*   **JDK 17**: 必须是 Java 17 版本。
    *   验证：`java -version`
*   **MySQL 8.0+**: 数据库服务。
    *   操作：创建空数据库 `create database gov_platform;`
*   **Redis**: 缓存服务。
*   **MinIO**: 文件存储服务（用于存储附件）。

## 2. 编译构建 (本地执行)

在本地开发机上打包项目：

```bash
# 在项目根目录执行 (Windows/Mac)
mvn clean package -DskipTests
```

成功后，会在 `target` 目录下生成文件：`gov-ai-platform-backend-0.1.0.jar`。

## 3. 上传文件

将生成的 `.jar` 包上传到服务器指定目录（例如 `/opt/gov-ai/`）。

## 4. 启动脚本 (关键)

**这是您唯一需要配置的地方**。请在服务器同级目录下创建一个启动脚本 `start.sh`，并填入您的真实密码。

```bash
#!/bin/bash

# ==========================================
# 配置区域 (请修改为您的真实信息)
# ==========================================

# 1. 数据库配置
export DB_HOST="127.0.0.1"           # 数据库IP
export DB_PORT="3306"                # 数据库端口
export DB_NAME="gov_platform"        # 数据库名
export DB_USER="root"                # 数据库账号
export DB_PASSWORD="YOUR_DB_PASSWORD" # 数据库密码 (必填!)

# 2. Redis 配置
export REDIS_HOST="127.0.0.1"
export REDIS_PORT="6379"
export REDIS_PASSWORD="YOUR_REDIS_PASSWORD" # Redis密码 (如有)

# 3. MinIO 配置 (文件存储)
export MINIO_ENDPOINT="http://127.0.0.1:9000"
export MINIO_ACCESS_KEY="minioadmin"
export MINIO_SECRET_KEY="YOUR_MINIO_SECRET"
export MINIO_BUCKET="gov-attachments"

# 4. AI 模型配置 (通义千问)
export AI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxx" # 您的阿里云 API Key

# 5. 其他配置
export SERVER_PORT="8080"            # 服务端口
export SYNC_INTERVAL="60000"         # 爬虫数据同步间隔 (毫秒)，默认1分钟

# ==========================================
# 启动逻辑 (无需修改)
# ==========================================

# 停止旧进程
PID=$(ps -ef | grep gov-ai-platform-backend | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "Stopping existing process $PID..."
    kill -9 $PID
fi

# 启动新进程
echo "Starting service..."
nohup java -jar gov-ai-platform-backend-0.1.0.jar > app.log 2>&1 &

echo "Service started! Log file: app.log"
```

## 5. 操作命令

1.  **赋予脚本权限**：
    ```bash
    chmod +x start.sh
    ```

2.  **启动服务**：
    ```bash
    ./start.sh
    ```

3.  **查看日志**：
    ```bash
    tail -f app.log
    ```

## 6. 验证部署

当日志中出现 `Started GovAiPlatformBackendApplication in ... seconds` 时，表示启动成功。

您可以在浏览器或 Postman 中访问：
`http://<服务器IP>:8080/api/public-info/hot`

如果能看到数据返回，说明部署成功！
