package com.gov.ai.service.impl;

import com.gov.ai.cache.CacheKeyConstant;
import com.gov.ai.cache.RedisCacheUtil;
import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import com.gov.ai.service.DataSyncService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.Duration;
import java.util.Set;

@Service
public class DataSyncServiceImpl implements DataSyncService {
    private static final Logger log = LoggerFactory.getLogger(DataSyncServiceImpl.class);
    
    private final PublicInfoRepository repository;
    private final RedisCacheUtil redisCache;
    private final StringRedisTemplate stringRedisTemplate;
    private final org.springframework.cache.CacheManager cacheManager;

    public DataSyncServiceImpl(PublicInfoRepository repository, RedisCacheUtil redisCache, StringRedisTemplate stringRedisTemplate, org.springframework.cache.CacheManager cacheManager) {
        this.repository = repository;
        this.redisCache = redisCache;
        this.stringRedisTemplate = stringRedisTemplate;
        this.cacheManager = cacheManager;
    }

    @Override
    @Scheduled(fixedDelayString = "${app.sync.interval-ms:60000}") // 默认每1分钟执行一次
    @Transactional
    public void syncCrawlDataToMysql() {
        log.info("Start syncing crawl data from Redis to MySQL...");
        redisCache.set(CacheKeyConstant.CRAWL_TASK_STATUS, "RUNNING", Duration.ofMinutes(15));
        
        // 1. 获取待同步 ID 集合
        Set<String> pendingIds = stringRedisTemplate.opsForSet().members(CacheKeyConstant.CRAWL_PENDING_IDS);
        if (pendingIds == null || pendingIds.isEmpty()) {
            log.info("No pending crawl data found.");
            redisCache.set(CacheKeyConstant.CRAWL_TASK_STATUS, "IDLE: No Data", Duration.ofHours(1));
            return;
        }

        int successCount = 0;
        int failCount = 0;
        boolean hasUpdates = false;

        for (String idSuffix : pendingIds) {
            // ... existing loop ...
            // idSuffix format expected: {date}:{id}
            String dataKey = CacheKeyConstant.CRAWL_DATA_PREFIX + ":" + idSuffix;
            
            try {
                // 2. 获取数据
                PublicInfo info = redisCache.getJson(dataKey, PublicInfo.class);
                if (info != null) {
                    // 3. 查重 (可选，根据 ID 或 URL)
                    if (info.getId() != null && repository.existsById(info.getId())) {
                         // Update exist
                         repository.save(info);
                    } else {
                        // 简单查重：根据 sourceUrl
                        if (StringUtils.hasText(info.getSourceUrl())) {
                            PublicInfo existing = repository.findBySourceUrl(info.getSourceUrl());
                            if (existing != null) {
                                // Found duplicate by URL -> Update it
                                info.setId(existing.getId());
                            }
                        }
                        
                        repository.save(info);
                    }
                    
                    // === PROACTIVE CACHING (Write-Through) ===
                    // REMOVED: 手动写入缓存容易导致 Key 不一致或脏数据问题（如前端反馈的 ID 错乱）。
                    // 改为使用标准的 Cache-Aside 模式：
                    // 数据只写入 MySQL，当用户请求详情时，由 @Cacheable 自动加载并缓存。
                    // 这样虽然第一次请求会查库，但能保证缓存 Key 的绝对正确和数据一致性。

                    hasUpdates = true;
                    
                    successCount++;
                } else {
                    log.warn("Data missing for key: {}", dataKey);
                }
                
                // 4. 清理 Redis (仅移除任务 ID，保留数据 Key 让其自然过期)
                stringRedisTemplate.opsForSet().remove(CacheKeyConstant.CRAWL_PENDING_IDS, idSuffix);
                // redisCache.delete(dataKey); // 不需要删掉，redis会过期的
                
            } catch (Exception e) {
                log.error("Failed to sync data for key: {}", dataKey, e);
                failCount++;
            }
        }
        
        if (hasUpdates) {
            // 刷新热门列表缓存
            refreshCache();
        }
        
        String result = String.format("IDLE: Last Sync Success %d, Fail %d", successCount, failCount);
        redisCache.set(CacheKeyConstant.CRAWL_TASK_STATUS, result, Duration.ofHours(1));
        log.info("Sync finished. Success: {}, Fail: {}", successCount, failCount);
    }

    @Override
    public void refreshCache() {
        // 刷新热门数据缓存逻辑
        // 这里可以主动预热 Redis 缓存，例如查询最新的数据放入 hot key
        log.info("Refreshing hot cache...");
        redisCache.delete(CacheKeyConstant.hot("all"));
        // 更多刷新逻辑...
    }
}
