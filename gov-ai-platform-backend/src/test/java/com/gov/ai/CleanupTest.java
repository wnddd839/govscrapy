package com.gov.ai;

import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.stream.Collectors;

@SpringBootTest
public class CleanupTest {

    @Autowired
    private PublicInfoRepository repository;

    @Test
    public void cleanupGarbageData() {
        System.out.println("Starting garbage data cleanup...");
        
        // 1. Find garbage data (category is null or empty)
        List<PublicInfo> allData = repository.findAll();
        List<PublicInfo> garbageData = allData.stream()
                .filter(p -> !StringUtils.hasText(p.getCategory()))
                .collect(Collectors.toList());

        System.out.println("Found " + garbageData.size() + " garbage records (category is null or empty).");

        // 2. Delete them
        if (!garbageData.isEmpty()) {
            repository.deleteAll(garbageData);
            System.out.println("Successfully deleted " + garbageData.size() + " records.");
        } else {
            System.out.println("No garbage data found. Database is clean.");
        }
    }
}
