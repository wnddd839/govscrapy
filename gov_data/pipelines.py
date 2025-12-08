import json
import redis
import hashlib
import requests
import io
import os
import re
import yaml
import uuid
from datetime import datetime
from itemadapter import ItemAdapter
from minio import Minio
from minio.error import S3Error

# Attempt to import libraries for conversion
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class RedisPipeline:
    """
    Redis数据处理管道
    实现与后端Redis的标准化对接
    使用Hash+Sorted Set结构
    """
    def __init__(self, redis_host, redis_port, redis_password, redis_db, 
                 minio_endpoint, minio_access_key, minio_secret_key, minio_bucket, minio_secure,
                 category_config_path):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_password = redis_password
        self.redis_db = redis_db
        self.redis_client = None
        
        self.minio_endpoint = minio_endpoint
        self.minio_access_key = minio_access_key
        self.minio_secret_key = minio_secret_key
        self.minio_bucket = minio_bucket
        self.minio_secure = minio_secure
        self.minio_client = None
        
        # Load category config
        self.category_config_path = category_config_path
        self.categories = self._load_category_config()
        
        # Redis key constants (与后端CacheKeyConstant一致)
        self.HASH_KEY_PREFIX = "gov:data:"  # Hash存储前缀
        self.NEW_DATA_SET = "gov:data:new"  # 待同步集合
        self.HOT_DATA_SET = "gov:data:hot"  # 热门数据集合
        self.HOT_DATA_LIMIT = 100  # 热门数据保留数量
        self.DATA_TTL = 60 * 60 * 24  # 24小时TTL

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_host=crawler.settings.get('REDIS_HOST'),
            redis_port=crawler.settings.get('REDIS_PORT'),
            redis_password=crawler.settings.get('REDIS_PASSWORD'),
            redis_db=crawler.settings.get('REDIS_DB'),
            minio_endpoint=crawler.settings.get('MINIO_ENDPOINT'),
            minio_access_key=crawler.settings.get('MINIO_ACCESS_KEY'),
            minio_secret_key=crawler.settings.get('MINIO_SECRET_KEY'),
            minio_bucket=crawler.settings.get('MINIO_BUCKET'),
            minio_secure=crawler.settings.get('MINIO_SECURE', False),
            category_config_path=crawler.settings.get('CATEGORY_CONFIG_PATH')
        )

    def _load_category_config(self):
        """加载分类配置"""
        try:
            with open(self.category_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('categories', [])
        except Exception as e:
            print(f"Failed to load category config: {e}")
            return []

    def open_spider(self, spider):
        # Redis Connection
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=True,
                socket_timeout=10,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            spider.logger.info("✅ Redis connection established.")
        except Exception as e:
             spider.logger.error(f"❌ Redis Connection Failed: {e}")

        
        # MinIO Connection
        if self.minio_endpoint:
            try:
                self.minio_client = Minio(
                    self.minio_endpoint,
                    access_key=self.minio_access_key,
                    secret_key=self.minio_secret_key,
                    secure=self.minio_secure
                )
                # Ensure bucket exists
                if not self.minio_client.bucket_exists(self.minio_bucket):
                    self.minio_client.make_bucket(self.minio_bucket)
                    spider.logger.info(f"Created MinIO bucket: {self.minio_bucket}")
            except Exception as e:
                spider.logger.error(f"MinIO Connection Failed: {e}")

    def close_spider(self, spider):
        # Trigger Backend Sync removed as requested
        if self.redis_client:
            self.redis_client.close()

    def _clean_html(self, html_content):
        if not html_content:
            return ""
        # Basic cleaning: strip HTML tags
        # Using re is fast for simple cases, but lxml/BeautifulSoup is more robust.
        # Given we have lxml installed (via Scrapy), let's use w3lib.html.remove_tags
        from w3lib.html import remove_tags
        text = remove_tags(html_content)
        
        # Normalize whitespace
        text = " ".join(text.split())
        return text

    def _upload_to_minio(self, data, size, content_type, object_name, spider):
        try:
            self.minio_client.put_object(
                self.minio_bucket,
                object_name,
                data,
                size,
                content_type=content_type
            )
            spider.logger.info(f"Uploaded to MinIO: {object_name}")
            return True
        except Exception as e:
            spider.logger.error(f"Error uploading {object_name}: {e}")
            return False

    def _minio_object_url(self, object_name):
        scheme = 'https' if self.minio_secure else 'http'
        return f"{scheme}://{self.minio_endpoint}/{self.minio_bucket}/{object_name}"

    def _convert_office_to_pdf(self, in_bytes, in_name, spider):
        try:
            import tempfile
            import subprocess
            suffix = os.path.splitext(in_name)[1].lower()
            if suffix not in ('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'):
                return None
            with tempfile.TemporaryDirectory() as tmpdir:
                in_path = os.path.join(tmpdir, in_name)
                with open(in_path, 'wb') as f:
                    f.write(in_bytes)
                soffice = os.environ.get('LIBREOFFICE_PATH', 'soffice')
                cmd = [
                    soffice, '--headless', '--nologo', '--nofirststartwizard',
                    '--convert-to', 'pdf', '--outdir', tmpdir, in_path
                ]
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
                except Exception as e:
                    spider.logger.warning(f"Office->PDF conversion failed for {in_name}: {e}")
                    return None
                base = os.path.splitext(os.path.basename(in_name))[0]
                pdf_path = os.path.join(tmpdir, base + '.pdf')
                if not os.path.exists(pdf_path):
                    return None
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                return io.BytesIO(pdf_bytes)
        except Exception as e:
            spider.logger.warning(f"Conversion error: {e}")
            return None

    def _convert_to_pdf(self, file_data, filename, spider):
        """
        Simple conversion logic. 
        Note: Real-world doc/docx to PDF in Linux/Windows environment usually requires libreoffice or pandoc.
        Here we implement a placeholder or basic text-to-pdf for demonstration if it's a text file.
        For binary files like doc/docx, we can't easily convert without external tools installed in the environment.
        
        Given the constraints, we will:
        1. If it's already PDF, return None.
        2. For this environment, we will skip complex conversion unless libraries are present.
        """
        # For now, since we cannot easily install LibreOffice in this environment,
        # we will skip actual conversion logic for DOC/DOCX and log a warning.
        # If it were a text file, we could use ReportLab.
        
        spider.logger.warning(f"PDF conversion for {filename} is not fully supported in this environment without LibreOffice.")
        return None

    def _classify_category(self, title, content, source_url):
        """
        自动分类标记
        URL规则优先，关键词兜底
        与后端gov_category_config表一致
        """
        t = title or ""
        c = content or ""
        s = (t + c).lower()
        u = (source_url or "").lower()
        
        # 1. URL规则匹配（优先）
        for category in self.categories:
            if not category.get('is_active', True):
                continue
            
            url_patterns = category.get('url_patterns', [])
            for pattern in url_patterns:
                if pattern in u:
                    return category['category_tag']
        
        # 2. 关键词匹配
        for category in self.categories:
            if not category.get('is_active', True):
                continue
            
            keywords = category.get('keywords', [])
            for keyword in keywords:
                if keyword.lower() in s:
                    return category['category_tag']
        
        # 3. 默认分类
        return "其他"

    def _generate_data_id(self):
        """生成UUID，32位无横线"""
        return uuid.uuid4().hex

    def _generate_fingerprint(self, title, publish_time):
        """生成数据指纹，用于去重"""
        return hashlib.md5(f"{title}_{publish_time}".encode('utf-8')).hexdigest()

    def _is_duplicate(self, fingerprint):
        """检查数据是否重复"""
        # 使用Redis集合存储指纹
        fingerprint_key = "gov:data:fingerprints"
        # 检查指纹是否存在
        if self.redis_client.sismember(fingerprint_key, fingerprint):
            return True
        # 添加指纹，设置TTL为30天
        self.redis_client.sadd(fingerprint_key, fingerprint)
        self.redis_client.expire(fingerprint_key, 60 * 60 * 24 * 30)
        return False

    def _format_publish_time(self, publish_date_str):
        """格式化发布时间为YYYY-MM-DD HH:mm:ss"""
        if not publish_date_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        publish_time = publish_date_str
        try:
            # Try to parse various date formats
            if len(publish_date_str) == 10:  # YYYY-MM-DD
                dt = datetime.strptime(publish_date_str, '%Y-%m-%d')
                publish_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            elif len(publish_date_str) > 10:  # YYYY-MM-DD HH:MM:SS or similar
                # Try multiple formats
                formats = [
                    '%Y-%m-%d %H:%M:%S', 
                    '%Y-%m-%d %H:%M', 
                    '%Y/%m/%d %H:%M:%S', 
                    '%Y.%m.%d %H:%M:%S',
                    '%Y年%m月%d日 %H:%M:%S',
                    '%Y年%m月%d日'
                ]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(publish_date_str[:19], fmt)
                        publish_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        break
                    except:
                        continue
        except Exception as e:
            print(f"Failed to parse publish_date: {publish_date_str}, using current time")
            publish_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return publish_time

    def process_item(self, item, spider):
        """处理爬虫数据，写入Redis"""
        adapter = ItemAdapter(item)
        
        # 1. 准备数据
        title = adapter.get('title')
        if title and len(title) > 255:
            spider.logger.warning(f"⚠️ Title too long ({len(title)}). Truncating to 255 chars.")
            title = title[:252] + "..."
            
        source_url = adapter.get('sourceUrl') or adapter.get('source_url')
        if source_url and len(source_url) > 512:
            spider.logger.warning(f"⚠️ SourceUrl too long ({len(source_url)}). Truncating to 512 chars.")
            source_url = source_url[:512]

        publish_date_str = adapter.get('publishDate') or adapter.get('publish_time')
        
        source_org = adapter.get('sourceOrg') or adapter.get('publish_dept')
        if source_org and len(source_org) > 100:
            spider.logger.warning(f"⚠️ SourceOrg too long ({len(source_org)}). Truncating to 100 chars.")
            source_org = source_org[:97] + "..."
            
        raw_content = adapter.get('contentText') or adapter.get('content')
        
        if not source_url:
            spider.logger.warning(f"⚠️ Skipped item without source_url: {title}")
            return item
            
        # 2. 生成数据ID和时间
        data_id = self._generate_data_id()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        current_timestamp = int(datetime.now().timestamp())
        
        # 3. 格式化发布时间
        publish_time = self._format_publish_time(publish_date_str)
        
        # 4. 数据去重
        fingerprint = self._generate_fingerprint(title, publish_time)
        if self._is_duplicate(fingerprint):
            spider.logger.info(f"🔄 Duplicate item skipped: {title[:50]}...")
            return item
        
        # 5. 处理附件
        attachments = adapter.get('attachments') or []
        processed_attachments = []
        
        for att in attachments:
            att_url = att.get('url')
            att_name = att.get('name')
            
            if att_url and self.minio_client:
                try:
                    # Download file
                    resp = requests.get(att_url, timeout=30)
                    if resp.status_code == 200:
                        content_type = resp.headers.get('Content-Type', 'application/octet-stream')
                        original_data = io.BytesIO(resp.content)
                        original_size = len(resp.content)
                        
                        # Upload Original File
                        safe_name = os.path.basename(att_name) if att_name else f"file_{hashlib.md5(att_url.encode()).hexdigest()}"
                        object_name_original = f"{datetime.now().strftime('%Y%m%d')}/{data_id}/{safe_name}"
                        
                        self._upload_to_minio(original_data, original_size, content_type, object_name_original, spider)
                        
                        # Standardized fields
                        minio_url = self._minio_object_url(object_name_original)
                        att['original_url'] = att_url
                        att['url'] = minio_url
                        att['size'] = original_size
                        att['type'] = att.get('type') or os.path.splitext(safe_name)[1].replace('.', '').lower()

                        # Handle PDF Logic
                        pdf_folder_key = f"{datetime.now().strftime('%Y%m%d')}_pdf"
                        
                        if safe_name.lower().endswith('.pdf'):
                            att['pdf_url'] = att['url']
                            att['pdf_path'] = att['pdf_url']
                        else:
                            original_data.seek(0)
                            pdf_stream = self._convert_office_to_pdf(original_data.read(), safe_name, spider)
                            if pdf_stream:
                                pdf_name = os.path.splitext(safe_name)[0] + '.pdf'
                                object_name_pdf = f"{pdf_folder_key}/{data_id}/{pdf_name}"
                                pdf_bytes = pdf_stream.getvalue()
                                self._upload_to_minio(io.BytesIO(pdf_bytes), len(pdf_bytes), 'application/pdf', object_name_pdf, spider)
                                att['pdf_url'] = self._minio_object_url(object_name_pdf)
                                att['pdf_path'] = att['pdf_url']
                            else:
                                att['pdf_url'] = None
                                att['pdf_path'] = None
                        
                    else:
                        spider.logger.warning(f"⚠️ Failed to download attachment: {att_url} Status: {resp.status_code}")
                except Exception as e:
                    spider.logger.error(f"❌ Error uploading attachment {att_url}: {e}")
            
            processed_attachments.append(att)

        # 6. 清理正文
        cleaned_content = self._clean_html(raw_content)
        
        # 7. 自动分类
        # Prioritize category from item if available (from spider config)
        category_tag = adapter.get('category')
        if not category_tag:
            category_tag = self._classify_category(title, cleaned_content, source_url)
        
        # 安全检查：防止分类字段过长导致后端报错
        if category_tag and len(category_tag) > 50:
            spider.logger.warning(f"⚠️ Detected abnormal category length ({len(category_tag)}). Value: {category_tag[:50]}... Resetting to '其他'.")
            category_tag = "其他"
        
        # 8. 提取来源网站
        source_website = spider.name.replace('_', ' ').title() if spider.name else "未知来源"
        if "gd_gov" in spider.name:
            source_website = "广东省人民政府"
        elif "hn_gov" in spider.name:
            source_website = "海南省人民政府"
        elif "hainanlist" in spider.name:
            source_website = "海南省人民政府列表"
        
        # 9. 构建符合后端要求的数据结构
        gov_data = {
            "dataId": data_id,
            "title": title,
            "content": cleaned_content,
            "publishTime": publish_time,
            "sourceUrl": source_url,
            "sourceWebsite": source_website,
            "publishDept": source_org or "未知单位",
            "category": category_tag,
            "crawlTime": current_time,
            "isNew": "1",  # 固定为1，标记未同步
            "attachments": json.dumps(processed_attachments, ensure_ascii=False)
        }

        # 10. Redis写入（严格遵循后端规范）
        try:
            # Step 1: 写入Hash结构
            hash_key = f"{self.HASH_KEY_PREFIX}{data_id}"
            self.redis_client.hset(hash_key, mapping=gov_data)
            self.redis_client.expire(hash_key, self.DATA_TTL)  # 24小时TTL
            
            # Step 2: 添加到待同步集合
            self.redis_client.zadd(self.NEW_DATA_SET, {data_id: current_timestamp})
            
            # Step 3: 添加到热门数据集合
            self.redis_client.zadd(self.HOT_DATA_SET, {data_id: current_timestamp})
            
            # Step 4: 保留最新100条热门数据
            self.redis_client.zremrangebyrank(self.HOT_DATA_SET, 0, -self.HOT_DATA_LIMIT - 1)
            
            spider.logger.info(f"✅ Pushed to Redis: {hash_key} | Category: {category_tag} | Source: {source_website}")
            
        except Exception as e:
            # 重试机制
            for retry in range(3):
                try:
                    spider.logger.warning(f"🔄 Retrying Redis write ({retry+1}/3)...")
                    # 重试写入
                    hash_key = f"{self.HASH_KEY_PREFIX}{data_id}"
                    self.redis_client.hset(hash_key, mapping=gov_data)
                    self.redis_client.expire(hash_key, self.DATA_TTL)
                    self.redis_client.zadd(self.NEW_DATA_SET, {data_id: current_timestamp})
                    self.redis_client.zadd(self.HOT_DATA_SET, {data_id: current_timestamp})
                    self.redis_client.zremrangebyrank(self.HOT_DATA_SET, 0, -self.HOT_DATA_LIMIT - 1)
                    spider.logger.info(f"✅ Redis write succeeded after retry.")
                    break
                except Exception as retry_e:
                    if retry == 2:  # 最后一次重试
                        spider.logger.error(f"❌ Redis write failed after 3 retries: {retry_e}")
                    else:
                        import time
                        time.sleep(1)  # 重试间隔1秒

        # 11. 更新Item，返回给后续管道
        adapter['dataId'] = data_id
        adapter['title'] = title
        adapter['content'] = cleaned_content
        adapter['publishTime'] = publish_time
        adapter['sourceUrl'] = source_url
        adapter['sourceWebsite'] = source_website
        adapter['publishDept'] = source_org or "未知单位"
        adapter['category'] = category_tag
        adapter['crawlTime'] = current_time
        adapter['isNew'] = "1"
        adapter['attachments'] = processed_attachments
        
        return item
