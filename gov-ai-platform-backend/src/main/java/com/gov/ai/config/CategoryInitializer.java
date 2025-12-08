package com.gov.ai.config;

import com.gov.ai.entity.CategoryConfig;
import com.gov.ai.repository.CategoryConfigRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.List;

@Component
public class CategoryInitializer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(CategoryInitializer.class);

    private final CategoryConfigRepository categoryConfigRepository;

    public CategoryInitializer(CategoryConfigRepository categoryConfigRepository) {
        this.categoryConfigRepository = categoryConfigRepository;
    }

    @Override
    public void run(String... args) throws Exception {
        if (categoryConfigRepository.count() == 0) {
            log.info("Initializing category configs...");
            
            List<CategoryConfig> configs = Arrays.asList(
                createConfig("政策法规", "1001", "Policy and Regulations"),
                createConfig("人事任免", "1002", "Personnel Appointment and Removal"),
                createConfig("招考招聘", "1003", "Recruitment"),
                createConfig("规划计划", "1004", "Planning"),
                createConfig("统计数据", "1005", "Statistics")
            );
            
            categoryConfigRepository.saveAll(configs);
            log.info("Initialized {} category configs.", configs.size());
        } else {
            log.info("Category configs already initialized.");
        }
    }
    
    private CategoryConfig createConfig(String tag, String code, String remark) {
        CategoryConfig config = new CategoryConfig();
        config.setCategoryTag(tag);
        config.setCategoryCode(code);
        config.setRemark(remark);
        config.setStatus(1);
        return config;
    }
}
