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

    public static String crawlHotKey(String category) {
        return "crawl:hot:" + (category == null ? "all" : category);
    }
    
    // 政务数据Redis存储新结构
    // 单条政务数据Hash结构键前缀，完整键：gov:data:{dataId}
    public static final String GOV_DATA_HASH_PREFIX = "gov:data";
    
    // 待同步MySQL的新数据Sorted Set，分值：crawlTime时间戳，成员：dataId
    public static final String GOV_DATA_NEW_SORTED_SET = "gov:data:new";
    
    // 热门数据Sorted Set，分值：crawlTime时间戳，成员：dataId
    public static final String GOV_DATA_HOT_SORTED_SET = "gov:data:hot";
    
    // 过期时间常量（秒）
    // 新数据过期时间：24小时
    public static final int NEW_DATA_EXPIRE_SECONDS = 86400;
    
    // 热门数据过期时间：7天
    public static final int HOT_DATA_EXPIRE_SECONDS = 604800;
    
    // 热门数据最大缓存量，避免集合过大
    public static final int HOT_DATA_MAX_SIZE = 100;
    
    // 生成政务数据Hash键
    public static String govDataHashKey(String dataId) {
        return GOV_DATA_HASH_PREFIX + ":" + dataId;
    }
}

