package com.gov.ai.task;

import com.gov.ai.service.DataSyncService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@EnableScheduling
public class SyncTask {
    private final DataSyncService syncService;

    public SyncTask(DataSyncService syncService) {
        this.syncService = syncService;
    }

    // 每 10 分钟执行一次增量同步 (Redis -> MySQL)
    @Scheduled(fixedDelay = 600000)
    public void incrementalSync() {
        try {
            syncService.syncCrawlDataToMysql();
        } catch (Exception e) {
            log.error("增量同步任务失败", e);
        }
    }
}
