package com.gov.ai.controller;

import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/debug/redis")
public class RedisDebugController {

    private final StringRedisTemplate redisTemplate;
    private final PublicInfoRepository publicInfoRepository;

    public RedisDebugController(StringRedisTemplate redisTemplate, PublicInfoRepository publicInfoRepository) {
        this.redisTemplate = redisTemplate;
        this.publicInfoRepository = publicInfoRepository;
    }

    @GetMapping("/cleanup/categories")
    public Map<String, Object> cleanupCategories() {
        List<PublicInfo> list = publicInfoRepository.findAll();
        int updatedCount = 0;
        Map<String, Object> result = new HashMap<>();
        
        for (PublicInfo info : list) {
            String originalCategory = info.getCategory();
            if (originalCategory != null && originalCategory.trim().contains("人事信息")) {
                String title = info.getTitle();
                String newCategory = "人事任免"; // Default
                
                if (title != null) {
                    if (title.contains("招聘") || title.contains("招考") || title.contains("录用") || 
                        title.contains("遴选") || title.contains("公选") || title.contains("面试") || 
                        title.contains("笔试") || title.contains("成绩")) {
                        newCategory = "招考招聘";
                    }
                }
                
                if (!newCategory.equals(originalCategory)) {
                    info.setCategory(newCategory);
                    publicInfoRepository.save(info);
                    updatedCount++;
                }
            }
        }
        result.put("status", "success");
        result.put("updatedCount", updatedCount);
        return result;
    }

    /**
     * DANGER: Reset entire system data (MySQL + Redis)
     * Used for re-crawling fresh data
     */
    @GetMapping("/system/reset")
    public Map<String, Object> resetSystem() {
        Map<String, Object> result = new HashMap<>();
        
        // 1. Clear MySQL Data
        long mysqlCount = publicInfoRepository.count();
        publicInfoRepository.deleteAll(); 
        result.put("mysql_deleted_count", mysqlCount);
        
        // 2. Clear Redis Data
        Set<String> keys = new java.util.HashSet<>();
        
        // Collect keys by patterns
        Set<String> govKeys = redisTemplate.keys("gov:data*");
        if (govKeys != null) keys.addAll(govKeys);
        
        Set<String> crawlKeys = redisTemplate.keys("crawl:*");
        if (crawlKeys != null) keys.addAll(crawlKeys);
        
        Set<String> hotKeys = redisTemplate.keys("hot:*");
        if (hotKeys != null) keys.addAll(hotKeys);
        
        Set<String> detailKeys = redisTemplate.keys("detail:*");
        if (detailKeys != null) keys.addAll(detailKeys);
        
        // Execute Delete
        if (!keys.isEmpty()) {
            redisTemplate.delete(keys);
        }
        
        result.put("redis_keys_deleted_count", keys.size());
        result.put("status", "System reset successfully. Ready for new crawl.");
        
        return result;
    }

    @GetMapping("/keys")
    public Map<String, Object> listKeys(@RequestParam(name = "pattern", defaultValue = "*") String pattern) {
        Set<String> keys = redisTemplate.keys(pattern);
        Map<String, Object> result = new HashMap<>();
        result.put("count", keys != null ? keys.size() : 0);
        result.put("keys", keys);
        return result;
    }

    @GetMapping("/type")
    public String getType(@RequestParam("key") String key) {
        return redisTemplate.type(key).code();
    }
    
    @GetMapping("/get")
    public String get(@RequestParam("key") String key) {
        return redisTemplate.opsForValue().get(key);
    }

    @GetMapping("/zrange")
    public Set<String> zrange(@RequestParam("key") String key) {
        return redisTemplate.opsForZSet().range(key, 0, -1);
    }

    @GetMapping("/hgetall")
    public Map<Object, Object> hgetall(@RequestParam("key") String key) {
        return redisTemplate.opsForHash().entries(key);
    }
}
