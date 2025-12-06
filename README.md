# Government Data Crawler Project (gov_data)

## 1. 项目简介
本项目是一个基于 Scrapy 框架的政府数据采集系统，主要用于抓取海南省及其他地区的政府公开数据（如政策法规、人事信息、招标采购等）。作为爬虫端（Crawler AI），我负责数据的采集、清洗、分类，并将数据存储到 Redis（增量）和 MySQL（全量），同时将附件上传至 MinIO 对象存储。

## 2. 系统架构
整个系统由三个 AI 角色协同工作：
- **Crawler AI (我)**: 负责数据抓取、解析、清洗、存储。
- **Backend AI**: 负责后端 API 服务，处理数据查询、同步等逻辑。
- **Frontend AI**: 负责前端展示，提供用户界面。

### 数据流向
1. **采集**: Scrapy Spiders 从目标网站抓取数据。
2. **处理**: Pipelines 处理数据清洗、分类映射、附件下载与转换。
3. **存储**:
   - **Redis**: 用于增量数据存储（热门推荐、最新消息），TTL 7天。
   - **MySQL**: 用于全量历史数据归档。
   - **MinIO**: 用于存储附件文件（PDF, Doc, Xls 等）。

## 3. 核心组件

### 3.1 Spiders (`gov_data/spiders/`)
- `hainanlist.py` (`gov_list`): 抓取海南省公务员招考等列表数据。
- `gd_gov.py`: 广东政府数据抓取（示例）。
- `hn_gov.py`: 海南政府通用抓取。

### 3.2 Pipelines (`gov_data/pipelines.py`)
- **RedisPipeline**: 核心管道，处理以下任务：
  - 连接 Redis 和 MinIO。
  - 数据清洗 (`_clean_html`)。
  - 自动分类 (`_classify_category`)。
  - 附件上传 (`_upload_to_minio`)。
  - 触发后端同步 (`POST /api/admin/sync/db`)。

### 3.3 Items (`gov_data/items.py`)
定义了标准的数据结构 `GovDataItem`，包含字段：
- `title`, `sourceOrg`, `sourceUrl`, `publishDate`, `region`
- `contentText`, `attachments`, `column`

## 4. 运行指南

### 环境依赖
请参考 `requirements.txt` 安装依赖：
```bash
pip install -r requirements.txt
```

### 启动爬虫
支持两种模式：`incremental` (增量) 和 `full` (全量)。

**示例 1: 增量抓取 (写入 Redis)**
```bash
scrapy crawl hn_gov -a mode=incremental -a category=zfwj
```

**示例 2: 全量抓取 (写入 MySQL)**
```bash
scrapy crawl gd_gov -a mode=full -a category=gsgg -a max_pages=50
```

## 5. 目录结构
```
gov_data/
├── docs/                 # 项目文档 (规范说明)
├── gov_data/             # Scrapy 项目源码
│   ├── spiders/          # 爬虫代码
│   ├── items.py          # 数据模型
│   ├── pipelines.py      # 数据处理管道
│   └── settings.py       # 项目配置
├── crawl.log             # 爬虫日志
├── scrapy.cfg            # Scrapy 配置文件
└── requirements.txt      # 依赖列表
```

## 6. 协作规范
我作为 Crawler AI，严格遵守 `docs/spider_ai_spec.md` 中的规范。
- **输出字段**: 统一 JSON 契约。
- **分类映射**: 政策法规 -> `policy`, 人事信息 -> `personnel` 等。
- **存储策略**: 区分增量与全量存储逻辑。

如有指令，请直接下达，我将全力配合 Backend 和 Frontend AI 完成任务。
