package com.gov.ai.service.impl;

import com.gov.ai.config.MinioProperties;
import com.gov.ai.service.FileService;
import io.minio.BucketExistsArgs;
import io.minio.GetPresignedObjectUrlArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import io.minio.http.Method;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class FileServiceImpl implements FileService {
    private final MinioClient minioClient;
    private final MinioProperties properties;
    
    public FileServiceImpl(MinioClient minioClient, MinioProperties properties) { 
        this.minioClient = minioClient;
        this.properties = properties;
    }

    @PostConstruct
    public void init() {
        String bucket = properties.getBucketName();
        try {
            boolean found = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucket).build());
            if (!found) {
                log.info("Bucket {} does not exist, creating...", bucket);
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucket).build());
                
                // CORS Configuration:
                // 由于 MinIO Java SDK 版本差异，代码配置 CORS 可能不稳定。
                // 建议通过 MinIO Console (http://8.138.24.168:9001) 或 mc 命令行工具手动配置 Bucket CORS。
                // 规则示例：
                // Allowed Origins: *
                // Allowed Methods: GET, HEAD, OPTIONS
                // Allowed Headers: *
            }

        } catch (Exception e) {
            log.error("MinIO init failed: {}", e.getMessage());
        }
    }

    @Override
    public String presignedPreviewUrl(String objectName) {
        try {
            Map<String, String> params = new HashMap<>();
            // 强制浏览器内联显示，而非下载
            params.put("response-content-disposition", "inline; filename=\"" + objectName + "\"");
            // 明确指定 PDF 类型，防止浏览器无法识别
            if (objectName.toLowerCase().endsWith(".pdf")) {
                params.put("response-content-type", "application/pdf");
            }

            return minioClient.getPresignedObjectUrl(
                    GetPresignedObjectUrlArgs.builder()
                            .method(Method.GET)
                            .bucket(properties.getBucketName())
                            .object(objectName)
                            .extraQueryParams(params)
                            .build());
        } catch (Exception e) {
            return null;
        }
    }

    @Override
    public String presignedDownloadUrl(String objectName) {
        try {
            Map<String, String> params = new HashMap<>();
            // 强制下载
            params.put("response-content-disposition", "attachment; filename=\"" + objectName + "\"");
            
            return minioClient.getPresignedObjectUrl(
                    GetPresignedObjectUrlArgs.builder()
                            .method(Method.GET)
                            .bucket(properties.getBucketName())
                            .object(objectName)
                            .extraQueryParams(params)
                            .build());
        } catch (Exception e) {
            return null;
        }
    }
}

