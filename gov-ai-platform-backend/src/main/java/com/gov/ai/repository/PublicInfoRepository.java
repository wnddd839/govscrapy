package com.gov.ai.repository;

import com.gov.ai.entity.PublicInfo;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDate;
import java.util.List;

public interface PublicInfoRepository extends JpaRepository<PublicInfo, Long> {
    List<PublicInfo> findTop10ByOrderByPublishDateDesc();

    @Query("select p from PublicInfo p where (:region is null or p.region = :region) " +
            "and (:category is null or p.category = :category) " +
            "and (:start is null or p.publishDate >= :start) and (:end is null or p.publishDate <= :end) " +
            "and (:q is null or lower(p.title) like lower(concat('%',:q,'%')) or lower(p.contentText) like lower(concat('%',:q,'%')))")
    Page<PublicInfo> search(@Param("q") String q,
                            @Param("region") String region,
                            @Param("category") String category,
                            @Param("start") LocalDate start,
                            @Param("end") LocalDate end,
                            Pageable pageable);

    List<PublicInfo> findByUpdatedAtAfter(java.time.OffsetDateTime timestamp);

    boolean existsBySourceUrl(String sourceUrl);
    PublicInfo findBySourceUrl(String sourceUrl);
}

