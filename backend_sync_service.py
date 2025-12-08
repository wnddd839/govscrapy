#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政务公开信息整合平台 - 后端同步服务
功能：将Redis中的新数据同步到MySQL数据库
"""

import os
import json
import logging
import redis
import pymysql
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('backend_sync')

# 配置信息
CONFIG = {
    # Redis配置
    'redis': {
        'host': os.getenv('REDIS_HOST', '8.138.24.168'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'password': os.getenv('REDIS_PASSWORD', '123456'),
        'db': int(os.getenv('REDIS_DB', 0)),
        'socket_timeout': 5
    },
    # MySQL配置
    'mysql': {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'password'),
        'database': os.getenv('MYSQL_DATABASE', 'gov_data'),
        'charset': 'utf8mb4'
    },
    # 同步配置
    'sync': {
        'interval_minutes': 5,  # 同步间隔（分钟）
        'batch_size': 50,  # 每次同步批量大小
        'max_retries': 3  # 最大重试次数
    }
}

class BackendSyncService:
    def __init__(self):
        self.redis_client = None
        self.mysql_conn = None
        self.mysql_cursor = None
        self.scheduler = BackgroundScheduler()
        self.init_connections()
    
    def init_connections(self):
        """初始化Redis和MySQL连接"""
        try:
            # 连接Redis
            self.redis_client = redis.Redis(
                host=CONFIG['redis']['host'],
                port=CONFIG['redis']['port'],
                password=CONFIG['redis']['password'],
                db=CONFIG['redis']['db'],
                decode_responses=True,
                socket_timeout=CONFIG['redis']['socket_timeout']
            )
            self.redis_client.ping()
            logger.info("✅ Redis连接成功")
            
            # 连接MySQL
            self.mysql_conn = pymysql.connect(
                host=CONFIG['mysql']['host'],
                port=CONFIG['mysql']['port'],
                user=CONFIG['mysql']['user'],
                password=CONFIG['mysql']['password'],
                database=CONFIG['mysql']['database'],
                charset=CONFIG['mysql']['charset'],
                autocommit=False
            )
            self.mysql_cursor = self.mysql_conn.cursor()
            logger.info("✅ MySQL连接成功")
            
        except Exception as e:
            logger.error(f"❌ 初始化连接失败: {e}")
            raise
    
    def close_connections(self):
        """关闭连接"""
        if self.mysql_cursor:
            self.mysql_cursor.close()
        if self.mysql_conn:
            self.mysql_conn.close()
        if self.redis_client:
            self.redis_client.close()
        logger.info("🔌 连接已关闭")
    
    def get_new_data_from_redis(self):
        """从Redis获取新数据"""
        try:
            # 获取有序集合中的所有成员（按分值倒序，即最新的在前）
            new_data_ids = self.redis_client.zrange('gov_data_new', 0, -1, withscores=True, desc=True)
            logger.info(f"📋 发现 {len(new_data_ids)} 条新数据待同步")
            
            data_list = []
            for data_id, score in new_data_ids[:CONFIG['sync']['batch_size']]:
                # 获取Hash数据
                hash_key = f'gov_data:{data_id}'
                data = self.redis_client.hgetall(hash_key)
                if data:
                    data['data_id'] = data_id
                    data_list.append(data)
            
            return data_list
        except Exception as e:
            logger.error(f"❌ 从Redis获取数据失败: {e}")
            return []
    
    def validate_data(self, data):
        """验证数据有效性"""
        required_fields = ['data_id', 'title', 'content', 'publish_time', 'source_url', 'source_website', 'category_tag', 'crawl_time']
        
        for field in required_fields:
            if not data.get(field):
                logger.warning(f"⚠️ 数据缺失必填字段 {field}: {data.get('data_id')}")
                return False
        
        # 验证发布时间格式
        try:
            datetime.strptime(data['publish_time'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.warning(f"⚠️ 发布时间格式错误: {data.get('publish_time')} ({data.get('data_id')})")
            return False
        
        # 验证爬取时间格式
        try:
            datetime.strptime(data['crawl_time'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.warning(f"⚠️ 爬取时间格式错误: {data.get('crawl_time')} ({data.get('data_id')})")
            return False
        
        return True
    
    def check_existing_data(self, data_id):
        """检查数据是否已存在于MySQL"""
        try:
            sql = "SELECT id FROM gov_data WHERE data_id = %s"
            self.mysql_cursor.execute(sql, (data_id,))
            return self.mysql_cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"❌ 检查数据存在性失败: {e}")
            return False
    
    def insert_into_mysql(self, data):
        """将数据插入MySQL"""
        try:
            sql = """
            INSERT INTO gov_data (
                data_id, title, content, publish_time, source_url, 
                source_website, publish_dept, category_tag, crawl_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                data['data_id'],
                data['title'],
                data['content'],
                data['publish_time'],
                data['source_url'],
                data['source_website'],
                data.get('publish_dept', ''),
                data['category_tag'],
                data['crawl_time']
            )
            
            self.mysql_cursor.execute(sql, values)
            self.mysql_conn.commit()
            logger.info(f"✅ 数据已插入MySQL: {data['data_id']} | {data['title'][:20]}...")
            return True
        except Exception as e:
            logger.error(f"❌ 插入MySQL失败: {e}")
            self.mysql_conn.rollback()
            return False
    
    def update_redis_sync_status(self, data_id):
        """更新Redis中的同步状态"""
        try:
            hash_key = f'gov_data:{data_id}'
            # 更新is_new字段为0
            self.redis_client.hset(hash_key, 'is_new', '0')
            # 从有序集合中移除
            self.redis_client.zrem('gov_data_new', data_id)
            logger.debug(f"📝 更新Redis同步状态: {data_id}")
        except Exception as e:
            logger.error(f"❌ 更新Redis同步状态失败: {e}")
    
    def sync_data(self):
        """执行数据同步"""
        logger.info("🚀 开始数据同步任务")
        
        try:
            # 1. 获取新数据
            data_list = self.get_new_data_from_redis()
            
            if not data_list:
                logger.info("📭 没有新数据需要同步")
                return
            
            # 2. 遍历同步数据
            success_count = 0
            failed_count = 0
            
            for data in data_list:
                data_id = data['data_id']
                
                # 3. 验证数据
                if not self.validate_data(data):
                    failed_count += 1
                    continue
                
                # 4. 检查是否已存在
                if self.check_existing_data(data_id):
                    logger.info(f"🔄 数据已存在，跳过: {data_id}")
                    # 更新同步状态
                    self.update_redis_sync_status(data_id)
                    success_count += 1
                    continue
                
                # 5. 插入MySQL
                if self.insert_into_mysql(data):
                    # 6. 更新同步状态
                    self.update_redis_sync_status(data_id)
                    success_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"📊 同步完成: 成功 {success_count} 条, 失败 {failed_count} 条")
            
        except Exception as e:
            logger.error(f"❌ 同步任务失败: {e}")
            # 重试连接
            self.close_connections()
            self.init_connections()
    
    def start_scheduler(self):
        """启动定时调度器"""
        # 添加定时任务
        self.scheduler.add_job(
            self.sync_data,
            trigger=IntervalTrigger(minutes=CONFIG['sync']['interval_minutes']),
            id='gov_data_sync',
            name='政务数据同步任务',
            replace_existing=True
        )
        
        # 立即执行一次
        self.sync_data()
        
        # 启动调度器
        self.scheduler.start()
        logger.info(f"⏰ 定时同步服务已启动，每 {CONFIG['sync']['interval_minutes']} 分钟执行一次")
    
    def run(self):
        """运行服务"""
        try:
            self.start_scheduler()
            # 保持运行
            while True:
                input("按 Ctrl+C 停止服务...\n")
                break
        except KeyboardInterrupt:
            logger.info("⏸️  服务已停止")
        finally:
            self.scheduler.shutdown()
            self.close_connections()

if __name__ == '__main__':
    service = BackendSyncService()
    service.run()