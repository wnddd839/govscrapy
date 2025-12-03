package com.gov.ai.cache;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.time.Duration;

@Component
public class RedisCacheUtil {
    private static final Logger log = LoggerFactory.getLogger(RedisCacheUtil.class);
    
    private final StringRedisTemplate template;
    private final ObjectMapper objectMapper;

    public RedisCacheUtil(StringRedisTemplate template, ObjectMapper objectMapper) { 
        this.template = template;
        this.objectMapper = objectMapper;
    }

    public void set(String key, String value, Duration ttl) { 
        template.opsForValue().set(key, value, ttl); 
    }

    public String get(String key) { 
        return template.opsForValue().get(key); 
    }

    public void delete(String key) { 
        template.delete(key); 
    }

    public <T> void setJson(String key, T value, Duration ttl) {
        try {
            String json = objectMapper.writeValueAsString(value);
            template.opsForValue().set(key, json, ttl);
        } catch (JsonProcessingException e) {
            log.error("Redis setJson error for key: {}", key, e);
            throw new RuntimeException("Redis serialization error", e);
        }
    }

    public <T> T getJson(String key, Class<T> clazz) {
        String json = template.opsForValue().get(key);
        if (json == null) return null;
        try {
            return objectMapper.readValue(json, clazz);
        } catch (JsonProcessingException e) {
            log.error("Redis getJson error for key: {}", key, e);
            return null;
        }
    }

    public boolean hasKey(String key) {
        return Boolean.TRUE.equals(template.hasKey(key));
    }
    
    public void expire(String key, Duration ttl) {
        template.expire(key, ttl);
    }

    public static String safeHash(String s) { 
        return StringUtils.hasText(s) ? Integer.toHexString(s.hashCode()) : ""; 
    }
    
    // Helper to generate keys based on pattern prefix:date:id
    public String generateKey(String prefix, String date, String id) {
        return String.format("%s:%s:%s", prefix, date, id);
    }
}

