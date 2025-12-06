package com.gov.ai.service;

import com.gov.ai.dto.CrawlItemDTO;

import java.util.List;

public interface CrawlIngestService {
    void ingestIncremental(List<CrawlItemDTO> items);
    void ingestFull(List<CrawlItemDTO> items);
}

