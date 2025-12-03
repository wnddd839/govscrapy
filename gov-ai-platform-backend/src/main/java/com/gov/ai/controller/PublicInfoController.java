package com.gov.ai.controller;

import com.gov.ai.dto.PublicInfoListResponse;
import com.gov.ai.entity.PublicInfo;
import com.gov.ai.service.PublicInfoService;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/public-info")
public class PublicInfoController {
    private final PublicInfoService service;
    public PublicInfoController(PublicInfoService service) { this.service = service; }

    @GetMapping("/hot")
    public List<PublicInfo> hot(@RequestParam(name = "region", required = false) String region) {
        return service.hot(region);
    }

    @GetMapping("/detail/{id}")
    public PublicInfo detail(@PathVariable("id") Long id) {
        return service.detail(id);
    }

    @GetMapping("/list")
    public PublicInfoListResponse list(@RequestParam(name = "q", required = false) String q,
                                       @RequestParam(name = "region", required = false) String region,
                                       @RequestParam(name = "category", required = false) String category,
                                       @RequestParam(name = "startDate", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate startDate,
                                       @RequestParam(name = "endDate", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate endDate,
                                       @RequestParam(name = "page", defaultValue = "0") int page,
                                       @RequestParam(name = "size", defaultValue = "10") int size) {
        Page<PublicInfo> result = service.list(q, region, category, startDate, endDate, PageRequest.of(page, size));
        return PublicInfoListResponse.of(result);
    }
}

