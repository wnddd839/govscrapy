package com.gov.ai.controller;

import com.gov.ai.service.DataSyncService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/admin/sync")
public class SyncController {
    private final DataSyncService syncService;

    public SyncController(DataSyncService syncService) {
        this.syncService = syncService;
    }

    @PostMapping("/cache")
    public String refreshCache() {
        syncService.refreshCache();
        return "缓存刷新已触发";
    }

    @PostMapping("/db")
    public String syncToDb() {
        syncService.syncCrawlDataToMysql();
        return "Redis->MySQL 同步已触发";
    }
}
