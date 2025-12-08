#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
政务公开信息整合平台定时调度器
使用APScheduler实现定时爬取任务
"""

import os
import yaml
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import subprocess
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('gov_spider_scheduler')


class GovSpiderScheduler:
    """
    政务爬虫定时调度器
    """
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.crawl_rules = self._load_crawl_rules()
    
    def _load_crawl_rules(self):
        """加载爬取规则配置"""
        rules_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'crawl_rules.yml')
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('websites', [])
        except Exception as e:
            logger.error(f"❌ Failed to load crawl rules: {e}")
            return []
    
    def _start_spider(self, spider_name='config_based_spider', **kwargs):
        """启动爬虫"""
        try:
            logger.info(f"🚀 Starting spider: {spider_name} with kwargs: {kwargs}")
            
            # 构建scrapy命令
            cmd = [
                sys.executable, '-m', 'scrapy', 'crawl', spider_name
            ]
            
            # 添加额外参数
            for key, value in kwargs.items():
                cmd.extend(['-a', f'{key}={value}'])
            
            logger.debug(f"📝 Executing command: {' '.join(cmd)}")
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            
            # 记录输出
            if result.stdout:
                logger.debug(f"📤 Spider output: {result.stdout}")
            if result.stderr:
                logger.warning(f"⚠️ Spider stderr: {result.stderr}")
            
            if result.returncode == 0:
                logger.info(f"✅ Spider {spider_name} completed successfully")
                return True
            else:
                logger.error(f"❌ Spider {spider_name} failed with return code {result.returncode}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to start spider {spider_name}: {e}")
            return False
    
    def _add_cron_job(self, website):
        """添加cron定时任务"""
        website_name = website.get('website_name')
        crawl_config = website.get('crawl_config', {})
        
        # 获取cron表达式配置
        cron_config = crawl_config.get('cron', {})
        enabled = website.get('enabled', True)
        
        if not enabled:
            logger.info(f"⏸️ Skipping disabled website: {website_name}")
            return
        
        if not cron_config:
            # 默认每小时执行一次
            cron_config = {
                'minute': '0',
                'hour': '*',
                'day': '*',
                'month': '*',
                'day_of_week': '*'
            }
            logger.info(f"📅 No cron config for {website_name}, using default: hourly")
        
        # 构建cron触发器
        trigger = CronTrigger(
            minute=cron_config.get('minute', '*'),
            hour=cron_config.get('hour', '*'),
            day=cron_config.get('day', '*'),
            month=cron_config.get('month', '*'),
            day_of_week=cron_config.get('day_of_week', '*')
        )
        
        # 添加任务
        self.scheduler.add_job(
            func=self._start_spider,
            trigger=trigger,
            id=f"spider_{website_name}",
            name=f"Spider for {website_name}",
            replace_existing=True,
            kwargs={
                'spider_name': 'config_based_spider',
                'website_name': website_name
            }
        )
        
        logger.info(f"📅 Added cron job for {website_name}: {cron_config}")
    
    def _add_interval_job(self, website):
        """添加间隔定时任务"""
        website_name = website.get('website_name')
        crawl_config = website.get('crawl_config', {})
        
        # 获取间隔配置
        interval = crawl_config.get('interval', 3600)  # 默认3600秒（1小时）
        enabled = website.get('enabled', True)
        
        if not enabled:
            logger.info(f"⏸️ Skipping disabled website: {website_name}")
            return
        
        # 构建间隔触发器
        trigger = IntervalTrigger(seconds=interval)
        
        # 添加任务
        self.scheduler.add_job(
            func=self._start_spider,
            trigger=trigger,
            id=f"spider_{website_name}",
            name=f"Spider for {website_name}",
            replace_existing=True,
            kwargs={
                'spider_name': 'config_based_spider',
                'website_name': website_name
            }
        )
        
        logger.info(f"⏰ Added interval job for {website_name}: every {interval} seconds")
    
    def configure_jobs(self):
        """配置定时任务"""
        logger.info("🔧 Configuring scheduler jobs...")
        
        for website in self.crawl_rules:
            website_name = website.get('website_name')
            crawl_config = website.get('crawl_config', {})
            schedule_type = crawl_config.get('schedule_type', 'cron')
            
            try:
                if schedule_type == 'cron':
                    self._add_cron_job(website)
                elif schedule_type == 'interval':
                    self._add_interval_job(website)
                else:
                    logger.warning(f"⚠️ Unknown schedule type {schedule_type} for {website_name}, using cron")
                    self._add_cron_job(website)
            except Exception as e:
                logger.error(f"❌ Failed to configure job for {website_name}: {e}")
    
    def start(self):
        """启动调度器"""
        try:
            logger.info("🚀 Starting GovSpiderScheduler...")
            
            # 配置任务
            self.configure_jobs()
            
            # 启动调度器
            self.scheduler.start()
            
            logger.info("✅ GovSpiderScheduler started successfully")
            logger.info(f"📋 Scheduled jobs: {len(self.scheduler.get_jobs())}")
            
            # 列出所有任务
            for job in self.scheduler.get_jobs():
                logger.info(f"📅 Job: {job.id} | {job.name} | {job.trigger}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start scheduler: {e}")
            return False
    
    def stop(self):
        """停止调度器"""
        try:
            logger.info("⏸️ Stopping GovSpiderScheduler...")
            self.scheduler.shutdown()
            logger.info("✅ GovSpiderScheduler stopped successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to stop scheduler: {e}")
            return False
    
    def run_once(self):
        """立即执行一次所有爬虫"""
        logger.info("🔥 Running all spiders once...")
        
        success_count = 0
        failed_count = 0
        
        for website in self.crawl_rules:
            if website.get('enabled', True):
                if self._start_spider(spider_name='config_based_spider'):
                    success_count += 1
                else:
                    failed_count += 1
        
        logger.info(f"📊 Run once completed: {success_count} succeeded, {failed_count} failed")
        return success_count, failed_count


def main():
    """主函数"""
    scheduler = GovSpiderScheduler()
    
    # 启动调度器
    scheduler.start()
    
    # 立即执行一次
    scheduler.run_once()
    
    # 保持运行
    try:
        logger.info("🕒 Scheduler is running. Press Ctrl+C to exit...")
        while True:
            input()
    except KeyboardInterrupt:
        logger.info("🔴 Received KeyboardInterrupt, stopping scheduler...")
        scheduler.stop()


if __name__ == '__main__':
    main()