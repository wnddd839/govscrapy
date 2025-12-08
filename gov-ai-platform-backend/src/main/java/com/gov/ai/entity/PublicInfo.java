package com.gov.ai.entity;

import com.gov.ai.converter.JsonListConverter;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

@Data
@Entity
@Table(name = "public_info", indexes = {
        @Index(name = "idx_category", columnList = "category"),
        @Index(name = "idx_publish_time", columnList = "publish_time")
})
public class PublicInfo {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "data_id", nullable = false, unique = true, length = 64)
    private String dataId;
    
    @Column(nullable = false)
    private String title;
    
    @Column(name = "source_org")
    private String sourceOrg;
    
    @Column(name = "source_url", length = 512, nullable = false)
    private String sourceUrl;
    
    @Column(name = "source_website", nullable = false, length = 100)
    private String sourceWebsite;
    
    @Column(name = "publish_time", nullable = false)
    private OffsetDateTime publishTime;
    
    @Column(name = "crawl_time", nullable = false)
    private OffsetDateTime crawlTime;
    
    @Column(name = "content_text", columnDefinition = "TEXT")
    private String contentText;
    
    @Column(name = "region")
    private String region;

    @Column(name = "category", nullable = false, length = 255)
    private String category;

    @Column(name = "column_flag")
    private String columnFlag;
    
    @Column(name = "is_new", nullable = false, columnDefinition = "tinyint(1) default 1")
    private Integer isNew = 1;
    
    @Convert(converter = JsonListConverter.class)
    @Column(name = "attachments", columnDefinition = "JSON")
    private List<Map<String, Object>> attachments;
    
    @Column(name = "created_at")
    private OffsetDateTime createdAt;
    
    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
}
