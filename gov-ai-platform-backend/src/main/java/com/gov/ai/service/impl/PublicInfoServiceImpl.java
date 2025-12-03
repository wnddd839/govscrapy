package com.gov.ai.service.impl;

import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import com.gov.ai.service.PublicInfoService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Slf4j
@Service
public class PublicInfoServiceImpl implements PublicInfoService {
    private final PublicInfoRepository mysqlRepository;

    public PublicInfoServiceImpl(PublicInfoRepository mysqlRepository) {
        this.mysqlRepository = mysqlRepository;
    }

    @Override
    @Cacheable(value = "hot", key = "T(com.gov.ai.cache.CacheKeyConstant).hot(#region)")
    public List<PublicInfo> hot(String region) {
        return mysqlRepository.findTop10ByOrderByPublishDateDesc();
    }

    @Override
    @Cacheable(value = "detail", key = "T(com.gov.ai.cache.CacheKeyConstant).detail(#id)")
    public PublicInfo detail(Long id) {
        return mysqlRepository.findById(id).orElse(null);
    }

    @Override
    public Page<PublicInfo> list(String q, String region, String category, LocalDate start, LocalDate end, Pageable pageable) {
        // 1. 关键词与筛选查询：直接走 MySQL
        // 注意：对于大量数据的全文检索，MySQL 性能不如 ES。但针对当前 50+ 条存量数据及少量增量数据，MySQL LIKE 模糊查询完全足够。
        // 后续若数据量超过 1万+，可考虑迁移回 ES 或使用 MySQL 全文索引。
        
        return mysqlRepository.search(q, region, category, start, end, pageable);
    }
}

