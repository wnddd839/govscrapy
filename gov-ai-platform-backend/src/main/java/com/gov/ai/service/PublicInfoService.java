package com.gov.ai.service;

import com.gov.ai.entity.PublicInfo;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.time.LocalDate;
import java.util.List;

public interface PublicInfoService {
    List<PublicInfo> hot(String region);
    PublicInfo detail(Long id);
    Page<PublicInfo> list(String q, String region, String category, LocalDate start, LocalDate end, Pageable pageable);
}

