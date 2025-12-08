package com.gov.ai.entity;

import jakarta.persistence.*;
import lombok.Data;

@Data
@Entity
@Table(name = "gov_category_config", uniqueConstraints = {
        @UniqueConstraint(name = "uk_category_tag", columnNames = "category_tag"),
        @UniqueConstraint(name = "uk_category_code", columnNames = "category_code")
})
public class CategoryConfig {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "category_tag", nullable = false, length = 50)
    private String categoryTag;
    
    @Column(name = "category_code", nullable = false, length = 20)
    private String categoryCode;
    
    @Column(name = "status", nullable = false, columnDefinition = "tinyint(1) default 1")
    private Integer status = 1;
    
    @Column(name = "remark", length = 255)
    private String remark;
}
