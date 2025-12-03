package com.gov.ai.controller;

import com.gov.ai.service.FileService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/file")
public class FileController {
    private final FileService fileService;
    public FileController(FileService fileService) { this.fileService = fileService; }

    @GetMapping("/preview/{*object}")
    public ResponseEntity<String> preview(@PathVariable("object") String object) {
        // {*object} captures the path including the leading slash, e.g., "/folder/file.pdf"
        // MinIO object names usually don't start with slash, so we strip it.
        String objectName = object.startsWith("/") ? object.substring(1) : object;
        String url = fileService.presignedPreviewUrl(objectName);
        if (url == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(url);
    }

    @GetMapping("/download/{*object}")
    public ResponseEntity<String> download(@PathVariable("object") String object) {
        String objectName = object.startsWith("/") ? object.substring(1) : object;
        String url = fileService.presignedDownloadUrl(objectName);
        if (url == null) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(url);
    }
}

