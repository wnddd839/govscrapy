package com.gov.ai;

import com.gov.ai.entity.PublicInfo;
import com.gov.ai.service.PublicInfoService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Page;

import java.util.List;

@SpringBootTest
public class CategoryDataApiTest {

    @Autowired
    private PublicInfoService publicInfoService;

    @Test
    public void testAllCategoriesData() {
        List<String> categories = publicInfoService.getCategories();
        for (String category : categories) {
            PageRequest pageRequest = PageRequest.of(0, 10);
            Page<PublicInfo> page = publicInfoService.getByCategory(category, null, null, pageRequest);
            System.out.println("分类: " + category + "，总数: " + page.getTotalElements());
            page.getContent().forEach(info -> {
                System.out.println("  标题: " + info.getTitle() + "，地区: " + info.getRegion() + "，发布时间: " + info.getPublishTime());
            });
        }
    }

    @Test
    public void testKeywordAndRegionFilter() {
        String category = "人事任免";
        String keyword = "招聘";
        String region = "北京";
        PageRequest pageRequest = PageRequest.of(0, 10);
        Page<PublicInfo> page = publicInfoService.getByCategory(category, keyword, region, pageRequest);
        System.out.println("分类: " + category + "，关键词: " + keyword + "，地区: " + region + "，总数: " + page.getTotalElements());
        page.getContent().forEach(info -> {
            System.out.println("  标题: " + info.getTitle() + "，地区: " + info.getRegion() + "，发布时间: " + info.getPublishTime());
        });
    }
}
