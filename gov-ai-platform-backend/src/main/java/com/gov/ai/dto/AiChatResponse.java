package com.gov.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class AiChatResponse {
    private String answer;
    private List<String> references;
}

