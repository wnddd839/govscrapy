package com.gov.ai.dto;

import lombok.Data;

@Data
public class ApiResponse<T> {
    private int code; // 响应码：200-成功，500-失败
    private String msg; // 响应信息
    private T data; // 响应数据

    // 成功响应静态方法
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(200, "操作成功", data);
    }

    // 失败响应静态方法
    public static <T> ApiResponse<T> fail(String msg) {
        return new ApiResponse<>(500, msg, null);
    }
    
    // 构造方法
    private ApiResponse(int code, String msg, T data) {
        this.code = code;
        this.msg = msg;
        this.data = data;
    }
}
