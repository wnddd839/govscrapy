package com.gov.ai;

import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.annotation.Rollback;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@SpringBootTest
public class DataCleanupTest {

    @Autowired
    private PublicInfoRepository repository;

    @Test
    @Rollback(false) // Commit changes to DB
    @Transactional
    public void splitPersonnelInfoCategory() {
        // 1. Find all records with category containing "人事信息"
        // Using a broad search since frontend mentioned mixed data
        List<PublicInfo> list = repository.findAll(); // In production, use pagination or specific query
        
        int updatedCount = 0;
        
        for (PublicInfo info : list) {
            String originalCategory = info.getCategory();
            if (originalCategory != null && originalCategory.trim().contains("人事信息")) {
                String title = info.getTitle();
                String newCategory = "人事任免"; // Default
                
                if (title != null) {
                    if (title.contains("招聘") || title.contains("招考") || title.contains("录用") || 
                        title.contains("遴选") || title.contains("公选") || title.contains("面试") || 
                        title.contains("笔试") || title.contains("成绩")) {
                        newCategory = "招考招聘";
                    }
                }
                
                // Update if changed
                if (!newCategory.equals(originalCategory)) {
                    info.setCategory(newCategory);
                    repository.save(info);
                    updatedCount++;
                    System.out.println("Updated DataID: " + info.getDataId() + " | Title: " + title + " | " + originalCategory + " -> " + newCategory);
                }
            }
        }
        
        System.out.println("Cleanup finished. Total records updated: " + updatedCount);
    }
}
