import sys
from types import SimpleNamespace

sys.path.append('.')

from gov_data.pipelines import RedisPipeline


class DummySpider:
    name = 'dummy'
    mode = 'incremental'
    def __init__(self):
        self.logger = SimpleNamespace(info=print, warning=print, error=print)


def run():
    rp = RedisPipeline(redis_host=None, redis_port=None, redis_password=None, redis_db=None,
                       minio_endpoint=None, minio_access_key=None, minio_secret_key=None,
                       minio_bucket=None, minio_secure=False)
    atts = [
        {"name": "文件A.pdf", "url": "http://example.com/a.pdf", "type": "pdf"},
        {"name": "文件B.docx", "url": "http://example.com/b.docx", "type": "docx"},
        {"name": "表格C.xlsx", "url": "http://example.com/c.xlsx", "type": "xlsx"},
        {"name": "压缩D.zip", "url": "http://example.com/d.zip", "type": "zip"},
    ]
    types = rp._aggregate_file_types(atts)
    print("file_types=", types)


if __name__ == '__main__':
    run()

