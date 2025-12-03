package com.gov.ai.dto;

import com.gov.ai.entity.PublicInfo;
import lombok.AllArgsConstructor;
import lombok.Data;
import org.springframework.data.domain.Page;

import java.util.List;

@Data
@AllArgsConstructor
public class PublicInfoListResponse {
    private List<PublicInfo> data;
    private int page;
    private int size;
    private long total;

    public static PublicInfoListResponse of(Page<PublicInfo> pageData) {
        return new PublicInfoListResponse(pageData.getContent(), pageData.getNumber(), pageData.getSize(), pageData.getTotalElements());
    }
}

