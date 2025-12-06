import json
import redis
import hashlib
import requests
import io
import os
import re
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
    def __init__(self, redis_host, redis_port, redis_password, redis_db, 
                 minio_endpoint, minio_access_key, minio_secret_key, minio_bucket, minio_secure):
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
            minio_secure=crawler.settings.get('MINIO_SECURE', False)
        )

    def open_spider(self, spider):
        # Redis Connection
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=True,
                socket_timeout=5
            )
            self.redis_client.ping()
            spider.logger.info("Redis connection established.")
        except Exception as e:
             spider.logger.error(f"Redis Connection Failed: {e}")

        
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
        # Trigger Backend Sync
        # POST /api/admin/sync/db
        # Using server IP since backend is likely on the server
        backend_url = "http://8.138.24.168:8080/api/admin/sync/db"
        try:
            spider.logger.info(f"Triggering backend sync at {backend_url}...")
            resp = requests.post(backend_url, json={"trigger": "crawler", "spider": spider.name}, timeout=10)
            if resp.status_code == 200:
                spider.logger.info("✅ Backend sync triggered successfully.")
            else:
                spider.logger.warning(f"⚠️ Backend sync returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            spider.logger.error(f"❌ Failed to trigger backend sync: {e}")

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
        t = title or ""
        c = content or ""
        s = (t + c)
        if any(k in s for k in ["任免","任命","人事","干部","录用","聘任","撤职"]):
            return "人事信息"
        if any(k in s for k in ["招标","采购","中标","投标","公开招标","竞争性谈判","询价"]):
            return "招标采购"
        if any(k in s for k in ["规划","计划","实施方案","行动计划","年度计划"]):
            return "规划计划"
        if any(k in s for k in ["财政","预算","决算","预决算","税","收费"]):
            return "财政预决算"
        if any(k in s for k in ["规定","办法","意见","决定","条例","指导意见","实施细则","政策"]):
            return "政策法规"
        u = (source_url or "").lower()
        if "zfwj" in u or "szfwj" in u:
            return "政策法规"
        return "其他"

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 1. Prepare Data
        title = adapter.get('title')
        source_url = adapter.get('sourceUrl')
        publish_date_str = adapter.get('publishDate')
        
        if not publish_date_str:
             publish_date_str = datetime.now().strftime('%Y-%m-%d')

        # Format date for key: yyyyMMdd
        date_key = None
        if publish_date_str:
            m = re.search(r'\d{4}[-/.]\d{2}[-/.]\d{2}', str(publish_date_str))
            if m:
                cleaned = m.group(0).replace('/', '-').replace('.', '-')
                try:
                    dt = datetime.strptime(cleaned, '%Y-%m-%d')
                    date_key = dt.strftime('%Y%m%d')
                except Exception:
                    pass
        if not date_key:
            date_key = datetime.now().strftime('%Y%m%d')

        # Generate ID
        if not source_url:
            return item 
            
        data_id = hashlib.md5(source_url.encode('utf-8')).hexdigest()

        # 2. Process Attachments (Upload to MinIO)
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
                        
                        # 2.1 Upload Original File
                        safe_name = os.path.basename(att_name) if att_name else f"file_{hashlib.md5(att_url.encode()).hexdigest()}"
                        object_name_original = f"{date_key}/{data_id}/{safe_name}"
                        
                        self._upload_to_minio(original_data, original_size, content_type, object_name_original, spider)
                        
                        # standardized fields for front-end/backend
                        minio_url = self._minio_object_url(object_name_original)
                        att['original_url'] = att_url
                        att['url'] = minio_url
                        att['size'] = original_size
                        # ensure type present
                        att['type'] = att.get('type') or os.path.splitext(safe_name)[1].replace('.', '').lower()

                        # 2.2 Handle PDF Logic
                        # If the file IS a PDF, we store it in the PDF folder as well for consistency? 
                        # User request: "pdf文件夹就以日期加pdf后缀标注即可" -> {date}_pdf/{id}/{filename}
                        
                        pdf_folder_key = f"{date_key}_pdf"
                        
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
                        spider.logger.warning(f"Failed to download attachment: {att_url} Status: {resp.status_code}")
                except Exception as e:
                    spider.logger.error(f"Error uploading attachment {att_url}: {e}")
            
            processed_attachments.append(att)

        # 3. Construct Payload
        # Clean content text (remove HTML tags)
        raw_content = adapter.get('contentText')
        cleaned_content = self._clean_html(raw_content)
        
        payload = {
            "title": title,
            "sourceOrg": adapter.get('sourceOrg'),
            "sourceUrl": source_url,
            "publishDate": publish_date_str,
            "region": adapter.get('region'),
            "contentText": cleaned_content,
            "attachments": processed_attachments,
            "category": self._classify_category(title, cleaned_content, source_url)
        }
        
        json_value = json.dumps(payload, ensure_ascii=False)

        # 4. Redis Operations (Priority 2 - Cache/Notification)
        # FILTER: Only write to Redis if the item is from 2025
        try:
            # Extract year from date_key (format YYYYMMDD) or publish_date_str
            item_year = int(date_key[:4])
            
            if item_year == 2025:
                redis_key = f"crawl:data:{date_key}:{data_id}"
                
                # Step 1: Write data details with TTL 3 days
                self.redis_client.setex(redis_key, 60 * 60 * 24 * 3, json_value)
                
                # Step 2: Add to pending set
                member = f"{date_key}:{data_id}"
                self.redis_client.sadd("crawl:pending:ids", member)
                
                spider.logger.info(f"Pushed to Redis: {redis_key} (Year: {item_year})")
            else:
                spider.logger.info(f"Skipped Redis write for old item: {title} (Year: {item_year})")
                
        except Exception as e:
            spider.logger.error(f"Redis Write Failed: {e}")

        return item
