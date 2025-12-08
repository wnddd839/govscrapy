package com.gov.ai.dto;

import lombok.Data;
import java.util.List;

@Data
public class PageResult<T> {
    private long total; // 总记录数
    private int page; // 当前页码
    private int size; // 每页条数
    private List<T> list; // 分页数据列表

    public PageResult(long total, int page, int size, List<T> list) {
        this.total = total;
        this.page = page;
        this.size = size;
        this.list = list;
    }
}
