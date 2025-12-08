package com.gov.ai.service.impl;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.gov.ai.cache.CacheKeyConstant;
import com.gov.ai.cache.RedisCacheUtil;
import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import com.gov.ai.service.DataSyncService;
import com.gov.ai.service.RedisHotDataService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@Service
public class DataSyncServiceImpl implements DataSyncService {
    private static final Logger log = LoggerFactory.getLogger(DataSyncServiceImpl.class);
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    
    private final PublicInfoRepository repository;
    private final RedisCacheUtil redisCache;
    private final StringRedisTemplate stringRedisTemplate;
    private final ObjectMapper objectMapper;
    private final RedisHotDataService redisHotDataService;

    public DataSyncServiceImpl(PublicInfoRepository repository, RedisCacheUtil redisCache, StringRedisTemplate stringRedisTemplate, RedisHotDataService redisHotDataService) {
        this.repository = repository;
        this.redisCache = redisCache;
        this.stringRedisTemplate = stringRedisTemplate;
        this.redisHotDataService = redisHotDataService;
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        this.objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    }

    @Override
    @Scheduled(fixedDelayString = "${app.sync.interval-ms:300000}") // 默认每5分钟执行一次
    @Transactional
    public void syncCrawlDataToMysql() {
        log.info("Start syncing crawl data from Redis to MySQL...");
        redisCache.set(CacheKeyConstant.CRAWL_TASK_STATUS, "RUNNING", Duration.ofMinutes(15));
        
        int successCount = 0;
        int failCount = 0;
        boolean hasUpdates = false;

        // ---------------------------------------------------------
        // 1. 同步 CRAWL_PENDING_IDS (来自 CrawlIngestServiceImpl 的数据)
        // ---------------------------------------------------------
        try {
            Set<String> pendingIds = stringRedisTemplate.opsForSet().members(CacheKeyConstant.CRAWL_PENDING_IDS);
            if (pendingIds != null && !pendingIds.isEmpty()) {
                log.info("Found {} pending items in CRAWL_PENDING_IDS", pendingIds.size());
                for (String pendingId : pendingIds) {
                    // pendingId format: "date:id"
                    String dataKey = CacheKeyConstant.CRAWL_DATA_PREFIX + ":" + pendingId;
                    try {
                        PublicInfo info = redisCache.getJson(dataKey, PublicInfo.class);
                        if (info != null) {
                            ensureRequiredFields(info, pendingId);

                            // Check if data already exists to avoid re-syncing/updating unchanged data
                            if (repository.existsByDataId(info.getDataId())) {
                                log.info("Data with dataId {} already exists in MySQL, skipping sync.", info.getDataId());
                                stringRedisTemplate.opsForSet().remove(CacheKeyConstant.CRAWL_PENDING_IDS, pendingId);
                                continue;
                            }

                            saveOrUpdate(info);
                            
                            // Remove from pending set
                            stringRedisTemplate.opsForSet().remove(CacheKeyConstant.CRAWL_PENDING_IDS, pendingId);
                            
                            // Add to Hot Data service for consistency
                            redisHotDataService.addHotData(info.getDataId(), 
                                info.getPublishTime() != null ? info.getPublishTime().toEpochSecond() : System.currentTimeMillis() / 1000);

                            successCount++;
                            hasUpdates = true;
                        } else {
                            // Data missing, remove ID
                            log.warn("Data missing for key: {}, removing from pending set", dataKey);
                            stringRedisTemplate.opsForSet().remove(CacheKeyConstant.CRAWL_PENDING_IDS, pendingId);
                        }
                    } catch (Exception e) {
                        log.error("Failed to sync pendingId from CRAWL_PENDING_IDS: {}", pendingId, e);
                        failCount++;
                    }
                }
            }
        } catch (Exception e) {
            log.error("Error processing CRAWL_PENDING_IDS", e);
        }

        // ---------------------------------------------------------
        // 2. 同步 GOV_DATA_NEW_SORTED_SET (兼容旧逻辑/新架构数据)
        // ---------------------------------------------------------
        try {
            Set<String> dataIdSet = stringRedisTemplate.opsForZSet().reverseRange(CacheKeyConstant.GOV_DATA_NEW_SORTED_SET, 0, -1);
            if (dataIdSet != null && !dataIdSet.isEmpty()) {
                log.info("Found {} pending items in GOV_DATA_NEW_SORTED_SET", dataIdSet.size());
                for (String dataId : dataIdSet) {
                    String dataKey = CacheKeyConstant.govDataHashKey(dataId);
                    try {
                        Map<Object, Object> rawDataMap = stringRedisTemplate.opsForHash().entries(dataKey);
                        if (rawDataMap != null && !rawDataMap.isEmpty()) {
                            String isNewStr = (String) rawDataMap.get("isNew");
                            if (isNewStr != null && "0".equals(isNewStr)) {
                                stringRedisTemplate.opsForZSet().remove(CacheKeyConstant.GOV_DATA_NEW_SORTED_SET, dataId);
                                continue;
                            }

                            Map<String, Object> processedMap = preprocessDataMap(rawDataMap);
                            PublicInfo info = convertMapToPublicInfo(processedMap);
                            
                            if (info != null && validatePublicInfo(info)) {
                                saveOrUpdate(info);
                                
                                stringRedisTemplate.opsForHash().put(dataKey, "isNew", "0");
                                stringRedisTemplate.expire(dataKey, Duration.ofSeconds(CacheKeyConstant.NEW_DATA_EXPIRE_SECONDS));
                                stringRedisTemplate.opsForZSet().remove(CacheKeyConstant.GOV_DATA_NEW_SORTED_SET, dataId);
                                
                                redisHotDataService.addHotData(dataId, info.getCrawlTime().toEpochSecond());
                                
                                hasUpdates = true;
                                successCount++;
                            } else {
                                log.warn("Invalid data for key: {}, removing", dataKey);
                                stringRedisTemplate.opsForZSet().remove(CacheKeyConstant.GOV_DATA_NEW_SORTED_SET, dataId);
                            }
                        } else {
                            stringRedisTemplate.opsForZSet().remove(CacheKeyConstant.GOV_DATA_NEW_SORTED_SET, dataId);
                        }
                    } catch (Exception e) {
                        log.error("Failed to sync dataId from GOV_DATA_NEW_SORTED_SET: {}", dataId, e);
                        failCount++;
                    }
                }
            }
        } catch (Exception e) {
            log.error("Error processing GOV_DATA_NEW_SORTED_SET", e);
        }
        
        // ---------------------------------------------------------
        // 3. 兜底同步：检查热门数据 (gov:data:hot) 是否已入库
        // ---------------------------------------------------------
        try {
            Set<String> hotDataIds = stringRedisTemplate.opsForZSet().reverseRange(CacheKeyConstant.GOV_DATA_HOT_SORTED_SET, 0, -1);
            if (hotDataIds != null && !hotDataIds.isEmpty()) {
                log.info("Checking {} items in GOV_DATA_HOT_SORTED_SET for sync", hotDataIds.size());
                for (String dataId : hotDataIds) {
    if (repository.existsByDataId(dataId)) {
        log.info("Data with dataId {} already exists in MySQL, skipping sync.", dataId);
        continue;
    }
    log.info("Syncing hot data: {}", dataId);
                    String dataKey = CacheKeyConstant.govDataHashKey(dataId);
                    try {
                        Map<Object, Object> rawDataMap = stringRedisTemplate.opsForHash().entries(dataKey);
                        if (rawDataMap != null && !rawDataMap.isEmpty()) {
                            Map<String, Object> processedMap = preprocessDataMap(rawDataMap);
                            PublicInfo info = convertMapToPublicInfo(processedMap);
                            
                            if (info != null && validatePublicInfo(info)) {
                                saveOrUpdate(info);
                                
                                // 标记已同步
                                stringRedisTemplate.opsForHash().put(dataKey, "isNew", "0");
                                stringRedisTemplate.expire(dataKey, Duration.ofSeconds(CacheKeyConstant.NEW_DATA_EXPIRE_SECONDS));
                                
                                hasUpdates = true;
                                successCount++;
                            }
                        } else {
                            // 数据丢失，从热门列表移除? 暂不移除，避免误删
                            log.warn("Data missing for hot key: {}", dataKey);
                        }
                    } catch (Exception e) {
                        log.error("Failed to sync hot dataId: {}", dataId, e);
                        failCount++;
                    }
                }
            }
        } catch (Exception e) {
            log.error("Error processing GOV_DATA_HOT_SORTED_SET", e);
        }
        
        if (hasUpdates) {
            refreshCache();
        }
        
        String result = String.format("IDLE: Last Sync Success %d, Fail %d", successCount, failCount);
        redisCache.set(CacheKeyConstant.CRAWL_TASK_STATUS, result, Duration.ofHours(1));
        log.info("Sync finished. Success: {}, Fail: {}", successCount, failCount);
    }

    private void ensureRequiredFields(PublicInfo info, String pendingId) {
        // Ensure dataId
        if (!StringUtils.hasText(info.getDataId())) {
            // pendingId is "date:idStr"
            String idStr = pendingId;
            int lastColon = pendingId.lastIndexOf(":");
            if (lastColon >= 0 && lastColon < pendingId.length() - 1) {
                idStr = pendingId.substring(lastColon + 1);
            }
            info.setDataId(idStr);
        }
        
        // Ensure sourceWebsite
        if (!StringUtils.hasText(info.getSourceWebsite())) {
            info.setSourceWebsite("Government Portal");
        }
        
        // Ensure crawlTime
        if (info.getCrawlTime() == null) {
            info.setCrawlTime(OffsetDateTime.now());
        }

        // Ensure publishTime
        if (info.getPublishTime() == null) {
            info.setPublishTime(OffsetDateTime.now());
        }
    }

    private void saveOrUpdate(PublicInfo info) {
        PublicInfo existing = null;
        if (StringUtils.hasText(info.getDataId())) {
            existing = repository.findByDataId(info.getDataId());
        }
        
        if (existing == null && StringUtils.hasText(info.getSourceUrl())) {
            existing = repository.findBySourceUrl(info.getSourceUrl());
        }
        
        if (existing != null) {
            info.setId(existing.getId());
            info.setCreatedAt(existing.getCreatedAt() != null ? existing.getCreatedAt() : OffsetDateTime.now());
            info.setUpdatedAt(OffsetDateTime.now());
        } else {
            info.setCreatedAt(OffsetDateTime.now());
            info.setUpdatedAt(OffsetDateTime.now());
        }
        
        // Ensure category length
        if (info.getCategory() != null && info.getCategory().length() > 255) {
            info.setCategory(info.getCategory().substring(0, 255));
        }
        
        repository.save(info);
    }


    private Map<String, Object> preprocessDataMap(Map<Object, Object> rawDataMap) {
        Map<String, Object> map = new HashMap<>();
        for (Map.Entry<Object, Object> entry : rawDataMap.entrySet()) {
            map.put(entry.getKey().toString(), entry.getValue());
        }

        // 1. 字段映射
        if (map.containsKey("content")) {
            map.put("contentText", map.remove("content"));
        }
        if (map.containsKey("publishDept")) {
            map.put("sourceOrg", map.remove("publishDept"));
        }

        // 确保 category 存在且处理 columnFlag
        if (map.containsKey("category")) {
            String category = (String) map.get("category");
            if (StringUtils.hasText(category)) {
                category = category.trim();
                // 截断过长的分类名称，防止数据库报错
                if (category.length() > 50) {
                    log.warn("Abnormal category length detected (len={}): {}", category.length(), category);
                    if (category.length() > 255) {
                        category = category.substring(0, 255);
                    }
                }
                
                // ---------------------------------------------------------
                // 特殊处理：分类名称映射 (解决爬虫分类与前端分类不一致问题)
                // ---------------------------------------------------------
                if ("人事信息".equals(category)) {
                    String title = (String) map.get("title");
                    if (title != null) {
                        if (title.contains("招聘") || title.contains("招考") || title.contains("录用") || 
                            title.contains("遴选") || title.contains("公选") || title.contains("面试") || 
                            title.contains("笔试") || title.contains("成绩")) {
                            category = "招考招聘";
                        } else {
                            category = "人事任免";
                        }
                    } else {
                        category = "人事任免"; // 默认兜底
                    }
                    log.info("Mapped category '人事信息' to '{}'", category);
                }
                
                map.put("category", category);
                
                // 如果 columnFlag 不存在，默认使用 category 的值
                // 这样既支持新逻辑(category)，也兼容旧逻辑(columnFlag)
                if (!map.containsKey("columnFlag") || !StringUtils.hasText((String)map.get("columnFlag"))) {
                    map.put("columnFlag", category);
                }
            }
        }

        // 2. 时间格式处理
        processDateTimeField(map, "publishTime");
        processDateTimeField(map, "crawlTime");

        // 3. 附件处理 (JSON String -> List)
        if (map.containsKey("attachments")) {
            String attachmentsJson = (String) map.get("attachments");
            if (StringUtils.hasText(attachmentsJson)) {
                try {
                    List<Map<String, Object>> attachments = objectMapper.readValue(attachmentsJson, new TypeReference<List<Map<String, Object>>>() {});
                    map.put("attachments", attachments);
                } catch (Exception e) {
                    log.warn("Failed to parse attachments json: {}", attachmentsJson);
                    map.put("attachments", new ArrayList<>());
                }
            } else {
                 map.put("attachments", new ArrayList<>());
            }
        }
        
        return map;
    }

    private void processDateTimeField(Map<String, Object> map, String fieldName) {
        if (map.containsKey(fieldName)) {
            String timeStr = (String) map.get(fieldName);
            if (StringUtils.hasText(timeStr)) {
                try {
                    // 假设格式为 "yyyy-MM-dd HH:mm:ss"
                    LocalDateTime localDateTime = LocalDateTime.parse(timeStr, DATE_FORMATTER);
                    // 转换为 OffsetDateTime (假设为系统默认时区)
                    OffsetDateTime offsetDateTime = localDateTime.atZone(ZoneId.systemDefault()).toOffsetDateTime();
                    // 序列化为 ISO-8601 字符串以便 Jackson 反序列化，或者直接放入对象如果 ObjectMapper 配置支持
                    // 这里我们放入 OffsetDateTime 对象，因为我们接下来用 writeValueAsString 再 readValue
                    // 只要 Jackson 配置了 JavaTimeModule，它就能处理 OffsetDateTime
                    map.put(fieldName, offsetDateTime);
                } catch (Exception e) {
                    log.warn("Failed to parse time field {}: {}", fieldName, timeStr);
                    // 如果解析失败，可能需要移除该字段以免导致整体反序列化失败，或者保留原值看运气
                     map.remove(fieldName);
                }
            }
        }
    }
    
    /**
     * 将预处理后的 Map 转换为 PublicInfo 对象
     */
    private PublicInfo convertMapToPublicInfo(Map<String, Object> dataMap) {
        try {
            String json = objectMapper.writeValueAsString(dataMap);
            return objectMapper.readValue(json, PublicInfo.class);
        } catch (Exception e) {
            log.error("Failed to convert map to PublicInfo: {}", dataMap, e);
            return null;
        }
    }
    
    /**
     * 验证PublicInfo对象的关键字段是否有效
     */
    private boolean validatePublicInfo(PublicInfo info) {
        if (info == null) return false;
        if (!StringUtils.hasText(info.getDataId())) return false;
        if (!StringUtils.hasText(info.getTitle())) return false;
        if (!StringUtils.hasText(info.getSourceUrl())) return false;
        if (!StringUtils.hasText(info.getSourceWebsite())) return false;
        if (info.getPublishTime() == null) return false;
        if (info.getCrawlTime() == null) return false;
        if (!StringUtils.hasText(info.getCategory())) return false;
        return true;
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
