package com.gov.ai.service;

public interface DataSyncService {
    /**
     * 从 Redis 缓冲区同步新增爬虫数据到 MySQL
     */
    void syncCrawlDataToMysql();
    
    /**
     * 刷新热门数据缓存（全量/增量策略）
     */
    void refreshCache();
}
