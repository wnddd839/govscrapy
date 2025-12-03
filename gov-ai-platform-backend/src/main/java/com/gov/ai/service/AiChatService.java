package com.gov.ai.service;

import com.gov.ai.dto.AiChatResponse;

public interface AiChatService {
    AiChatResponse chat(String question);
}

