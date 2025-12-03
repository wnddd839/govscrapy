package com.gov.ai.controller;

import com.gov.ai.dto.AiChatRequest;
import com.gov.ai.dto.AiChatResponse;
import com.gov.ai.service.AiChatService;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/ai")
public class AiChatController {
    private final AiChatService service;
    public AiChatController(AiChatService service) { this.service = service; }
    @PostMapping("/chat")
    public AiChatResponse chat(@RequestBody AiChatRequest request) {
        return service.chat(request.getQuestion());
    }
}

