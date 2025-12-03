package com.gov.ai.controller;

import com.gov.ai.repository.PublicInfoRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/_health")
public class HealthController {
    private final PublicInfoRepository repository;
    public HealthController(PublicInfoRepository repository) { this.repository = repository; }
    @GetMapping("/db")
    public Map<String, Object> db() {
        Map<String, Object> m = new HashMap<>();
        m.put("db", "ok");
        m.put("count", repository.count());
        return m;
    }
}

