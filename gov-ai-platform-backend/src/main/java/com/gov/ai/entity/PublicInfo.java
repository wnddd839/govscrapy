package com.gov.ai.entity;

import com.gov.ai.converter.JsonListConverter;
import jakarta.persistence.*;
import lombok.Data;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

@Data
@Entity
@Table(name = "public_info")
public class PublicInfo {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(nullable = false)
    private String title;
    @Column(name = "source_org")
    private String sourceOrg;
    @Column(name = "source_url")
    private String sourceUrl;
    @Column(name = "publish_date")
    private LocalDate publishDate;
    @Column(name = "content_text", columnDefinition = "TEXT")
    private String contentText;
    @Column(name = "region")
    private String region;

    @Column(name = "category")
    private String category;

    @Column(name = "column_flag")
    private String columnFlag;
    
    @Convert(converter = JsonListConverter.class)
    @Column(name = "attachments", columnDefinition = "JSON")
    private List<Map<String, Object>> attachments;
    
    @Column(name = "created_at")
    private OffsetDateTime createdAt;
    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
}
