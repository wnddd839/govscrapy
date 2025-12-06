package com.gov.ai.service.impl;

import com.gov.ai.cache.CacheKeyConstant;
import com.gov.ai.cache.RedisCacheUtil;
import com.gov.ai.dto.CrawlItemDTO;
import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import com.gov.ai.service.CrawlIngestService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;

@Service
public class CrawlIngestServiceImpl implements CrawlIngestService {
    private static final Logger log = LoggerFactory.getLogger(CrawlIngestServiceImpl.class);
    private final RedisCacheUtil redis;
    private final StringRedisTemplate redisTemplate;
    private final PublicInfoRepository repository;

    public CrawlIngestServiceImpl(RedisCacheUtil redis, StringRedisTemplate redisTemplate, PublicInfoRepository repository) {
        this.redis = redis;
        this.redisTemplate = redisTemplate;
        this.repository = repository;
    }

    @Override
    public void ingestIncremental(List<CrawlItemDTO> items) {
        if (items == null || items.isEmpty()) return;
        for (CrawlItemDTO dto : items) {
            PublicInfo info = toEntity(dto);
            String date = dto.publishDate != null ? dto.publishDate.toString() : LocalDate.now().toString();
            String idStr = dto.id != null ? String.valueOf(dto.id) : RedisCacheUtil.safeHash(dto.sourceUrl + ":" + dto.title);

            // 写入详情JSON用于后续同步到MySQL
            String dataKey = CacheKeyConstant.crawlDataKey(date, idStr);
            redis.setJson(dataKey, info, Duration.ofDays(7));
            redisTemplate.opsForSet().add(CacheKeyConstant.CRAWL_PENDING_IDS, date + ":" + idStr);

            // 写入热门分栏ZSet（member为dataKey，score为发布时间）
            String hotKey = CacheKeyConstant.crawlHotKey(dto.category);
            double score = (info.getPublishDate() != null ? info.getPublishDate() : LocalDate.now())
                    .atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli();
            redisTemplate.opsForZSet().add(hotKey, dataKey, score);
            redisTemplate.expire(hotKey, java.time.Duration.ofDays(7));
        }
        log.info("Incremental ingest completed: {} items", items.size());
    }

    @Override
    @Transactional
    public void ingestFull(List<CrawlItemDTO> items) {
        if (items == null || items.isEmpty()) return;
        for (CrawlItemDTO dto : items) {
            PublicInfo info = toEntity(dto);
            // 去重：优先按ID，其次按sourceUrl
            if (info.getId() != null && repository.existsById(info.getId())) {
                repository.save(info);
            } else if (info.getSourceUrl() != null) {
                com.gov.ai.entity.PublicInfo existing = repository.findBySourceUrl(info.getSourceUrl());
                if (existing != null) {
                    info.setId(existing.getId());
                }
                repository.save(info);
            } else {
                repository.save(info);
            }
        }
        log.info("Full ingest completed: {} items", items.size());
    }

    private PublicInfo toEntity(CrawlItemDTO dto) {
        PublicInfo pi = new PublicInfo();
        pi.setId(dto.id);
        pi.setTitle(dto.title);
        pi.setSourceOrg(dto.sourceOrg);
        pi.setSourceUrl(dto.sourceUrl);
        pi.setPublishDate(dto.publishDate);
        pi.setContentText(dto.contentText);
        pi.setRegion(dto.region);
        pi.setCategory(dto.category);
        pi.setColumnFlag(dto.columnFlag);
        pi.setAttachments(dto.attachments);
        return pi;
    }
}

