package com.gov.ai.service;

import com.gov.ai.entity.PublicInfo;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;

public interface PublicInfoService {
    List<PublicInfo> hot(String region);
    PublicInfo detail(Long id);
    Page<PublicInfo> list(String q, String region, String category, java.time.OffsetDateTime start, java.time.OffsetDateTime end, Pageable pageable);
    
    /**
     * 获取所有分类标签
     * 
     * @return 分类标签列表
     */
    List<String> getCategories();
    
    /**
     * 根据分类标签查询数据
     * 
     * @param categoryTag 分类标签
     * @param pageable    分页参数
     * @return 分页数据
     */
    Page<PublicInfo> getByCategory(String categoryTag, String q, String region, Pageable pageable);
    
    /**
     * 获取首页热门数据（最新20条）
     * 
     * @return 热门数据列表
     */
    List<PublicInfo> getHotList();
    
    /**
     * 根据dataId查询详情
     * 
     * @param dataId 数据ID
     * @param source 数据源 (redis/mysql)
     * @return 详情信息
     */
    PublicInfo getByDataId(String dataId, String source);

    /**
     * 根据dataId查询详情 (默认策略)
     *
     * @param dataId 数据ID
     * @return 详情信息
     */
    default PublicInfo getByDataId(String dataId) {
        return getByDataId(dataId, null);
    }
}

