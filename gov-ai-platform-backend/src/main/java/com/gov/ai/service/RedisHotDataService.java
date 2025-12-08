package com.gov.ai.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.gov.ai.cache.CacheKeyConstant;
import com.gov.ai.entity.PublicInfo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

@Service
public class RedisHotDataService {
    private static final Logger log = LoggerFactory.getLogger(RedisHotDataService.class);
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    
    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    
    public RedisHotDataService(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        this.objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    }
    
    /**
     * 添加热门数据到Redis Sorted Set
     * 
     * @param dataId                数据ID
     * @param crawlTimeTimestamp    爬取时间戳（用于排序）
     */
    public void addHotData(String dataId, Long crawlTimeTimestamp) {
        try {
            // 添加到Sorted Set（按爬取时间戳排序，时间戳越大越新）
            redisTemplate.opsForZSet().add(CacheKeyConstant.GOV_DATA_HOT_SORTED_SET, dataId, crawlTimeTimestamp);
            
            // 限制集合大小，超过100则删除最旧数据
            Long size = redisTemplate.opsForZSet().size(CacheKeyConstant.GOV_DATA_HOT_SORTED_SET);
            if (size != null && size > CacheKeyConstant.HOT_DATA_MAX_SIZE) {
                // 删除最旧的数据（索引从0开始，删除到size - HOT_DATA_MAX_SIZE - 1）
                redisTemplate.opsForZSet().removeRange(CacheKeyConstant.GOV_DATA_HOT_SORTED_SET, 
                        0, size - CacheKeyConstant.HOT_DATA_MAX_SIZE - 1);
            }
            
            // 设置集合过期时间（7天）
            redisTemplate.expire(CacheKeyConstant.GOV_DATA_HOT_SORTED_SET, 
                    CacheKeyConstant.HOT_DATA_EXPIRE_SECONDS, TimeUnit.SECONDS);
            
            log.debug("Added hot data: {}, timestamp: {}", dataId, crawlTimeTimestamp);
        } catch (Exception e) {
            log.error("Failed to add hot data: {}", dataId, e);
        }
    }
    
    /**
     * 获取最新20条热门数据
     * 
     * @return 热门数据列表，按爬取时间倒序排列
     */
    public List<PublicInfo> getHotDataTop20() {
        List<PublicInfo> hotDataList = new ArrayList<>();
        
        try {
            // 按分值倒序获取Top20 dataId（最新数据在前）
            Set<String> dataIdSet = redisTemplate.opsForZSet().reverseRange(CacheKeyConstant.GOV_DATA_HOT_SORTED_SET, 0, 19);
            if (dataIdSet == null || dataIdSet.isEmpty()) {
                log.info("No hot data found in Redis");
                return hotDataList;
            }
            
            // 批量查询Hash数据，组装返回结果
            for (String dataId : dataIdSet) {
                String dataKey = CacheKeyConstant.govDataHashKey(dataId);
                Map<Object, Object> dataMap = redisTemplate.opsForHash().entries(dataKey);
                
                if (!dataMap.isEmpty()) {
                    // 映射为PublicInfo对象
                    PublicInfo publicInfo = convertMapToPublicInfo(dataMap);
                    if (publicInfo != null) {
                        hotDataList.add(publicInfo);
                    }
                }
            }
            
            log.debug("Retrieved {} hot data items", hotDataList.size());
        } catch (Exception e) {
            log.error("Failed to get hot data", e);
        }
        
        return hotDataList;
    }
    
    /**
     * 根据dataId从Redis获取热门数据详情
     *
     * @param dataId 数据ID
     * @return 详情信息，若不存在则返回null
     */
    public PublicInfo getHotDataById(String dataId) {
        try {
            String dataKey = CacheKeyConstant.govDataHashKey(dataId);
            Map<Object, Object> dataMap = redisTemplate.opsForHash().entries(dataKey);
            
            if (!dataMap.isEmpty()) {
                return convertMapToPublicInfo(dataMap);
            }
        } catch (Exception e) {
            log.error("Failed to get hot data by id: {}", dataId, e);
        }
        return null;
    }

    /**
     * 将Redis Hash数据转换为PublicInfo对象
     */
    private PublicInfo convertMapToPublicInfo(Map<Object, Object> dataMap) {
        try {
            // 预处理 Map 数据，适配 PublicInfo 字段和类型
            Map<String, Object> processedMap = preprocessDataMap(dataMap);
            
            String json = objectMapper.writeValueAsString(processedMap);
            return objectMapper.readValue(json, PublicInfo.class);
        } catch (Exception e) {
            log.error("Failed to convert map to PublicInfo: {}", dataMap, e);
            return null;
        }
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
                // 截断过长的分类名称，保持与数据库一致
                if (category.length() > 50) {
                    log.warn("Abnormal category length detected in Redis hot data (len={}): {}", category.length(), category);
                    if (category.length() > 255) {
                        category = category.substring(0, 255);
                    }
                }
                map.put("category", category);
                
                // 如果 columnFlag 不存在，默认使用 category 的值
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
                    LocalDateTime localDateTime = LocalDateTime.parse(timeStr, DATE_FORMATTER);
                    OffsetDateTime offsetDateTime = localDateTime.atZone(ZoneId.systemDefault()).toOffsetDateTime();
                    map.put(fieldName, offsetDateTime);
                } catch (Exception e) {
                    log.warn("Failed to parse time field {}: {}", fieldName, timeStr);
                     map.remove(fieldName);
                }
            }
        }
    }
    
    /**
     * 刷新热门数据缓存（用于数据同步后更新）
     */
    public void refreshHotDataCache() {
        try {
            // 清除现有的热门数据集合
            redisTemplate.delete(CacheKeyConstant.GOV_DATA_HOT_SORTED_SET);
            log.info("Hot data cache refreshed");
        } catch (Exception e) {
            log.error("Failed to refresh hot data cache", e);
        }
    }
}
