package com.gov.ai.repository;

import com.gov.ai.entity.PublicInfo;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface PublicInfoRepository extends JpaRepository<PublicInfo, Long> {
    List<PublicInfo> findTop10ByOrderByPublishTimeDesc();

    @Query("select p from PublicInfo p where (:region is null or p.region = :region) " +
            "and (:category is null or p.category = :category) " +
            "and (:start is null or p.publishTime >= :start) and (:end is null or p.publishTime <= :end) " +
            "and (:q is null or lower(p.title) like lower(concat('%',:q,'%')) or lower(p.contentText) like lower(concat('%',:q,'%')))")
    Page<PublicInfo> search(@Param("q") String q,
                            @Param("region") String region,
                            @Param("category") String category,
                            @Param("start") java.time.OffsetDateTime start,
                            @Param("end") java.time.OffsetDateTime end,
                            Pageable pageable);

    List<PublicInfo> findByUpdatedAtAfter(java.time.OffsetDateTime timestamp);

    boolean existsBySourceUrl(String sourceUrl);
    PublicInfo findBySourceUrl(String sourceUrl);
    
    PublicInfo findByDataId(String dataId);
    boolean existsByDataId(String dataId);
}

