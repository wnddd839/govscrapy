package com.gov.ai.cache;

public final class CacheKeyConstant {
    private CacheKeyConstant() {}
    
    // 热门与详情
    public static String hot(String region) { return "hot:" + (region == null ? "all" : region); }
    public static String detail(Long id) { return "detail:" + id; }
    public static String list(String hash) { return "list:" + hash; }
    
    // AI 相关
    public static String aiAnswer(String hash) { return "ai:answer:" + hash; }
    
    // 爬虫数据同步相关
    // 待同步的数据ID集合 (Set)
    public static final String CRAWL_PENDING_IDS = "crawl:pending:ids";
    // 爬虫数据详情前缀 (String JSON), key format: crawl:data:{date}:{id}
    public static final String CRAWL_DATA_PREFIX = "crawl:data";
    // 爬虫任务状态
    public static final String CRAWL_TASK_STATUS = "crawl:task:status";
    
    public static String crawlDataKey(String date, String id) {
        return CRAWL_DATA_PREFIX + ":" + date + ":" + id;
    }
}

