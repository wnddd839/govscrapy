package com.gov.ai.service;

public interface FileService {
    String presignedPreviewUrl(String objectName);
    String presignedDownloadUrl(String objectName);
}

