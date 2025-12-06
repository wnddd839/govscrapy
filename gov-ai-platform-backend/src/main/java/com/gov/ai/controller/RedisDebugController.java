package com.gov.ai.controller;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/debug/redis")
public class RedisDebugController {

    private final StringRedisTemplate redisTemplate;

    public RedisDebugController(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
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
}
