package com.gov.ai.service;

import com.gov.ai.cache.CacheKeyConstant;
import com.gov.ai.cache.RedisCacheUtil;
import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import com.gov.ai.service.impl.DataSyncServiceImpl;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.HashOperations;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;

import java.time.Duration;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class DataSyncServiceTest {

    @Mock
    private PublicInfoRepository repository;

    @Mock
    private RedisCacheUtil redisCache;
    @Mock
    private StringRedisTemplate stringRedisTemplate;
    @Mock
    private ZSetOperations<String, String> zSetOperations;
    @Mock
    private HashOperations<String, Object, Object> hashOperations;
    @Mock
    private RedisHotDataService redisHotDataService;

    private DataSyncServiceImpl dataSyncService;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForZSet()).thenReturn(zSetOperations);
        when(stringRedisTemplate.opsForHash()).thenReturn(hashOperations);
        dataSyncService = new DataSyncServiceImpl(repository, redisCache, stringRedisTemplate, redisHotDataService);
    }

    @Test
    void testSyncCrawlDataToMysql_Success() {
        // 1. Prepare Mock Data
        String dataId = "5320d15d8a2a4d659785ed0b82caa58d";
        String dataKey = CacheKeyConstant.govDataHashKey(dataId);
        Set<String> pendingIds = Collections.singleton(dataId);

        // Redis Hash Data (Raw Strings)
        Map<Object, Object> rawDataMap = new HashMap<>();
        rawDataMap.put("dataId", dataId);
        rawDataMap.put("title", "海南省2025年度公开遴选公务员公告");
        rawDataMap.put("content", "海南省公务员局...");
        rawDataMap.put("publishTime", "2025-01-15 00:00:00");
        rawDataMap.put("sourceUrl", "https://www.hainan.gov.cn/...");
        rawDataMap.put("sourceWebsite", "海南省人民政府");
        rawDataMap.put("publishDept", "海南省人民政府"); // old key
        rawDataMap.put("category", "招考招聘");
        rawDataMap.put("crawlTime", "2025-12-07 16:00:00");
        rawDataMap.put("isNew", "1");
        
        // Attachments as JSON String
        String attachmentsJson = "[{\"name\":\"附件.docx\",\"url\":\"http://minio/...\",\"type\":\"docx\"}]";
        rawDataMap.put("attachments", attachmentsJson);

        // 2. Define Mock Behavior
        when(zSetOperations.reverseRange(CacheKeyConstant.GOV_DATA_NEW_SORTED_SET, 0, -1)).thenReturn(pendingIds);
        when(hashOperations.entries(dataKey)).thenReturn(rawDataMap);
        when(repository.findByDataId(dataId)).thenReturn(null); // New data
        when(repository.findBySourceUrl(anyString())).thenReturn(null); // No duplicate URL

        // 3. Execute
        dataSyncService.syncCrawlDataToMysql();

        // 4. Verify
        // Verify repository save was called
        ArgumentCaptor<PublicInfo> captor = ArgumentCaptor.forClass(PublicInfo.class);
        verify(repository).save(captor.capture());
        PublicInfo savedInfo = captor.getValue();
        
        assertEquals(dataId, savedInfo.getDataId());
        assertEquals("海南省2025年度公开遴选公务员公告", savedInfo.getTitle());
        assertEquals("海南省公务员局...", savedInfo.getContentText()); // Check mapped key
        assertEquals("海南省人民政府", savedInfo.getSourceOrg()); // Check mapped key
        assertEquals("招考招聘", savedInfo.getCategory());
        assertNotNull(savedInfo.getPublishTime());
        // Verify Time (approx check or exact if timezone matches)
        assertEquals(2025, savedInfo.getPublishTime().getYear());
        assertEquals(1, savedInfo.getPublishTime().getMonthValue());
        
        assertNotNull(savedInfo.getAttachments());
        assertEquals(1, savedInfo.getAttachments().size());
        assertEquals("附件.docx", savedInfo.getAttachments().get(0).get("name"));

        // Verify Redis cleanup
        verify(hashOperations).put(dataKey, "isNew", "0");
        verify(stringRedisTemplate).expire(eq(dataKey), any(Duration.class));
        verify(zSetOperations).remove(CacheKeyConstant.GOV_DATA_NEW_SORTED_SET, dataId);
        
        // Verify status update
        verify(redisCache, atLeastOnce()).set(eq(CacheKeyConstant.CRAWL_TASK_STATUS), anyString(), any(Duration.class));
    }

    @Test
    void testSyncCrawlDataToMysql_NoPendingData() {
        when(zSetOperations.reverseRange(CacheKeyConstant.GOV_DATA_NEW_SORTED_SET, 0, -1)).thenReturn(Collections.emptySet());

        dataSyncService.syncCrawlDataToMysql();

        verify(repository, never()).save(any());
    }
}
