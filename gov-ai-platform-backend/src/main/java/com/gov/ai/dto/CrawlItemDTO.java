package com.gov.ai.dto;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public class CrawlItemDTO {
    public Long id;
    public String title;
    public String sourceOrg;
    public String sourceUrl;
    public LocalDate publishDate;
    public String contentText;
    public String region;
    public String category;
    public String columnFlag;
    public List<Map<String, Object>> attachments;
}

