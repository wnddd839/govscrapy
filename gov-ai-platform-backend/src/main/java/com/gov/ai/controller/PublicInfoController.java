package com.gov.ai.controller;

import com.gov.ai.dto.ApiResponse;
import com.gov.ai.dto.PageResult;
import com.gov.ai.dto.PublicInfoListResponse;
import com.gov.ai.entity.PublicInfo;
import com.gov.ai.service.PublicInfoService;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

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
                                       @RequestParam(name = "startDate", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) java.time.OffsetDateTime startDate,
                                       @RequestParam(name = "endDate", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) java.time.OffsetDateTime endDate,
                                       @RequestParam(name = "page", defaultValue = "0") int page,
                                       @RequestParam(name = "size", defaultValue = "10") int size) {
        Page<PublicInfo> result = service.list(q, region, category, startDate, endDate, PageRequest.of(page, size));
        return PublicInfoListResponse.of(result);
    }
    
    /**
     * 获取所有分类标签
     * 
     * @return 分类标签列表
     */
    @GetMapping("/category/list")
    public ApiResponse<List<String>> getCategories() {
        List<String> categories = service.getCategories();
        return ApiResponse.success(categories);
    }
    
    /**
     * 分类专区数据查询
     * 
     * @param categoryTag 分类标签
     * @param page 页码（默认1）
     * @param size 每页条数（默认20）
     * @return 分页数据
     */
    @GetMapping("/category/data")
    public ApiResponse<PageResult<PublicInfo>> getCategoryData(
        @RequestParam("categoryTag") String categoryTag,
        @RequestParam(name = "q", required = false) String q,
        @RequestParam(name = "region", required = false) String region,
        @RequestParam(name = "source", required = false) String source,
        @RequestParam(name = "page", defaultValue = "1") int page,
        @RequestParam(name = "size", defaultValue = "20") int size) {
        int pageIndex = page > 0 ? page - 1 : 0;
        PageRequest pageRequest = PageRequest.of(pageIndex, size);
        Page<PublicInfo> result = service.getByCategory(categoryTag, q, region, pageRequest);
        PageResult<PublicInfo> pageResult = new PageResult<>(result.getTotalElements(),
                pageIndex + 1, size, result.getContent());
        return ApiResponse.success(pageResult);
    }
    
    /**
     * 首页热门数据查询（最新20条）
     * 
     * @return 20条热门数据
     */
    @GetMapping("/hot/list")
    public ApiResponse<List<PublicInfo>> getHotList() {
        List<PublicInfo> hotList = service.getHotList();
        return ApiResponse.success(hotList);
    }
    
    /**
     * 按dataId查询信息详情
     * 
     * @param dataId 数据ID
     * @param source 数据源 (redis/mysql)
     * @return 信息详情
     */
    @GetMapping("/detail/data/{dataId}")
    public ApiResponse<PublicInfo> getDetailByDataId(@PathVariable("dataId") String dataId,
                                                     @RequestParam(name = "source", required = false) String source) {
        PublicInfo info = service.getByDataId(dataId, source);
        return ApiResponse.success(info);
    }
}

