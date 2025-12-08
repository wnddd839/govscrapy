package com.gov.ai.repository;

import com.gov.ai.entity.CategoryConfig;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CategoryConfigRepository extends JpaRepository<CategoryConfig, Long> {
    
    /**
     * 获取所有启用状态的分类标签
     * 
     * @return 分类标签列表
     */
    List<CategoryConfig> findByStatusOrderByCategoryCodeAsc(Integer status);
    
    /**
     * 获取所有分类标签
     * 
     * @return 分类标签列表
     */
    List<CategoryConfig> findAllByOrderByCategoryCodeAsc();
}
