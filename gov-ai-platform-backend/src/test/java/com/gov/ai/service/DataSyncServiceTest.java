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
import org.springframework.data.redis.core.SetOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.time.Duration;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
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
    private SetOperations<String, String> setOperations;

    private DataSyncServiceImpl dataSyncService;

    @BeforeEach
    void setUp() {
        when(stringRedisTemplate.opsForSet()).thenReturn(setOperations);
        dataSyncService = new DataSyncServiceImpl(repository, redisCache, stringRedisTemplate);
    }

    @Test
    void testSyncCrawlDataToMysql_Success() {
        // 1. Prepare Mock Data
        String idSuffix = "2023-10-27:hn-123";
        String dataKey = CacheKeyConstant.CRAWL_DATA_PREFIX + ":" + idSuffix;
        Set<String> pendingIds = Collections.singleton(idSuffix);

        PublicInfo mockInfo = new PublicInfo();
        mockInfo.setTitle("Test Title");
        mockInfo.setSourceUrl("http://example.com");
        mockInfo.setContentText("Content");
        // Mock Attachments
        Map<String, Object> attachment = new HashMap<>();
        attachment.put("name", "test.pdf");
        attachment.put("url", "http://minio/file.pdf");
        mockInfo.setAttachments(List.of(attachment));

        // 2. Define Mock Behavior
        when(setOperations.members(CacheKeyConstant.CRAWL_PENDING_IDS)).thenReturn(pendingIds);
        when(redisCache.getJson(dataKey, PublicInfo.class)).thenReturn(mockInfo);
        when(repository.existsById(any())).thenReturn(false);

        // 3. Execute
        dataSyncService.syncCrawlDataToMysql();

        // 4. Verify
        // Verify repository save was called
        ArgumentCaptor<PublicInfo> captor = ArgumentCaptor.forClass(PublicInfo.class);
        verify(repository).save(captor.capture());
        PublicInfo savedInfo = captor.getValue();
        
        assertEquals("Test Title", savedInfo.getTitle());
        assertEquals("http://example.com", savedInfo.getSourceUrl());
        assertNotNull(savedInfo.getAttachments());
        assertEquals(1, savedInfo.getAttachments().size());
        assertEquals("http://minio/file.pdf", savedInfo.getAttachments().get(0).get("url"));

        // Verify Redis cleanup
        verify(setOperations).remove(CacheKeyConstant.CRAWL_PENDING_IDS, idSuffix);
        verify(redisCache).delete(dataKey);
        
        // Verify status update
        verify(redisCache, atLeastOnce()).set(eq(CacheKeyConstant.CRAWL_TASK_STATUS), anyString(), any(Duration.class));
    }

    @Test
    void testSyncCrawlDataToMysql_NoPendingData() {
        when(setOperations.members(CacheKeyConstant.CRAWL_PENDING_IDS)).thenReturn(Collections.emptySet());

        dataSyncService.syncCrawlDataToMysql();

        verify(repository, never()).save(any());
        verify(redisCache, times(1)).set(eq(CacheKeyConstant.CRAWL_TASK_STATUS), contains("IDLE"), any(Duration.class));
    }
}
