package com.gov.ai.service.impl;

import com.gov.ai.entity.CategoryConfig;
import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.CategoryConfigRepository;
import com.gov.ai.repository.PublicInfoRepository;
import com.gov.ai.service.PublicInfoService;
import com.gov.ai.service.RedisHotDataService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class PublicInfoServiceImpl implements PublicInfoService {
    private final PublicInfoRepository mysqlRepository;
    private final CategoryConfigRepository categoryConfigRepository;
    private final RedisHotDataService redisHotDataService;

    public PublicInfoServiceImpl(PublicInfoRepository mysqlRepository, 
                                 CategoryConfigRepository categoryConfigRepository, 
                                 RedisHotDataService redisHotDataService) {
        this.mysqlRepository = mysqlRepository;
        this.categoryConfigRepository = categoryConfigRepository;
        this.redisHotDataService = redisHotDataService;
    }

    @Override
    @Cacheable(value = "hot", key = "T(com.gov.ai.cache.CacheKeyConstant).hot(#region)")
    public List<PublicInfo> hot(String region) {
        return mysqlRepository.findTop10ByOrderByPublishTimeDesc();
    }

    @Override
    @Cacheable(value = "detail", key = "T(com.gov.ai.cache.CacheKeyConstant).detail(#id)")
    public PublicInfo detail(Long id) {
        return mysqlRepository.findById(id).orElse(null);
    }

    @Override
    public Page<PublicInfo> list(String q, String region, String category, OffsetDateTime start, OffsetDateTime end, Pageable pageable) {
        // 1. 关键词与筛选查询：直接走 MySQL
        // 注意：对于大量数据的全文检索，MySQL 性能不如 ES。但针对当前 50+ 条存量数据及少量增量数据，MySQL LIKE 模糊查询完全足够。
        // 后续若数据量超过 1万+，可考虑迁移回 ES 或使用 MySQL 全文索引。
        
        return mysqlRepository.search(q, region, category, start, end, pageable);
    }
    
    @Override
    public List<String> getCategories() {
        List<CategoryConfig> categoryConfigs = categoryConfigRepository.findByStatusOrderByCategoryCodeAsc(1);
        List<String> categories = new ArrayList<>();
        for (CategoryConfig config : categoryConfigs) {
            categories.add(config.getCategoryTag());
        }
        return categories;
    }
    
    @Override
    public Page<PublicInfo> getByCategory(String categoryTag, String q, String region, Pageable pageable) {
        // 支持分类、关键词、地区多条件筛选
        return mysqlRepository.search(q, region, categoryTag, null, null, pageable);
    }
    
    @Override
    public List<PublicInfo> getHotList() {
        // 从Redis获取热门数据
        List<PublicInfo> hotDataList = redisHotDataService.getHotDataTop20();
        
        // 如果Redis中没有数据，从MySQL获取最新20条数据
        if (hotDataList.isEmpty()) {
            log.info("No hot data found in Redis, fetching from MySQL");
            Page<PublicInfo> page = mysqlRepository.search(null, null, null, null, null, 
                    PageRequest.of(0, 20, Sort.by(Sort.Direction.DESC, "publishTime")));
            hotDataList = page.getContent();
        }
        
        hotDataList.sort((a, b) -> {
            if (a.getPublishTime() == null && b.getPublishTime() == null) return 0;
            if (a.getPublishTime() == null) return 1;
            if (b.getPublishTime() == null) return -1;
            return b.getPublishTime().compareTo(a.getPublishTime());
        });
        return hotDataList;
    }
    
    @Override
    @Cacheable(value = "detail", key = "#dataId + '-' + (#source == null ? 'default' : #source)", unless = "#result == null")
    public PublicInfo getByDataId(String dataId, String source) {
        // 1. 强制走 Redis
        if ("redis".equalsIgnoreCase(source)) {
            return redisHotDataService.getHotDataById(dataId);
        }
        
        // 2. 强制走 MySQL
        if ("mysql".equalsIgnoreCase(source)) {
            return mysqlRepository.findByDataId(dataId);
        }
        
        // 3. 默认逻辑：自动降级 (Redis -> MySQL)
        PublicInfo info = redisHotDataService.getHotDataById(dataId);
        
        // 如果 Redis 中没有，或者 Redis 中的数据分类不标准（仍为"人事信息"），则尝试从 MySQL 获取更准确的数据
        if (info == null || "人事信息".equals(info.getCategory())) {
            PublicInfo mysqlInfo = mysqlRepository.findByDataId(dataId);
            if (mysqlInfo != null) {
                info = mysqlInfo;
            }
        }
        
        // 4. 容错逻辑：如果按 dataId 没找到，尝试按主键 ID (PK) 查找
        // 前端有时会错误地将 numeric ID 传给 dataId 参数
        if (info == null) {
            try {
                long id = Long.parseLong(dataId);
                info = mysqlRepository.findById(id).orElse(null);
            } catch (NumberFormatException e) {
                // ignore
            }
        }
        
        // 5. 最终兜底修正：如果拿到的数据分类仍为 "人事信息"，进行实时修正
        if (info != null && "人事信息".equals(info.getCategory())) {
            String title = info.getTitle();
            if (title != null) {
                if (title.contains("招聘") || title.contains("招考") || title.contains("录用") || 
                    title.contains("遴选") || title.contains("公选") || title.contains("面试") || 
                    title.contains("笔试") || title.contains("成绩")) {
                    info.setCategory("招考招聘");
                } else {
                    info.setCategory("人事任免");
                }
            }
        }
        
        return info;
    }
}

