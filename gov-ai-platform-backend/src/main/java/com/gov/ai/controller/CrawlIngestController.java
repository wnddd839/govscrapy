package com.gov.ai.controller;

import com.gov.ai.dto.CrawlItemDTO;
import com.gov.ai.service.CrawlIngestService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/admin/crawl")
public class CrawlIngestController {
    private final CrawlIngestService ingestService;

    public CrawlIngestController(CrawlIngestService ingestService) {
        this.ingestService = ingestService;
    }

    @PostMapping("/ingest")
    public ResponseEntity<Map<String, Object>> ingest(@RequestParam("mode") String mode,
                                                      @RequestBody List<CrawlItemDTO> items) {
        if ("incremental".equalsIgnoreCase(mode)) {
            ingestService.ingestIncremental(items);
        } else if ("full".equalsIgnoreCase(mode)) {
            ingestService.ingestFull(items);
        } else {
            throw new IllegalArgumentException("mode must be incremental or full");
        }
        return ResponseEntity.ok(Map.of("accepted", items.size(), "mode", mode));
    }
}

