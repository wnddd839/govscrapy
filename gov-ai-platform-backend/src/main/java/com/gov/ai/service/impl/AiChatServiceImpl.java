package com.gov.ai.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gov.ai.config.AiTongyiProperties;
import com.gov.ai.dto.AiChatResponse;
import com.gov.ai.entity.PublicInfo;
import com.gov.ai.repository.PublicInfoRepository;
import com.gov.ai.service.AiChatService;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class AiChatServiceImpl implements AiChatService {
    private final AiTongyiProperties props;
    private final PublicInfoRepository mysqlRepository; // 使用 MySQL 替代 ES
    private final RestTemplate http;

    public AiChatServiceImpl(AiTongyiProperties props, PublicInfoRepository mysqlRepository) {
        this.props = props;
        this.mysqlRepository = mysqlRepository;
        this.http = new RestTemplate();
    }

    @Override
    public AiChatResponse chat(String question) {
        // 1. 检索相关文档 (MySQL LIKE)
        // 简化实现：只检索标题或正文包含关键词的前5条数据
        // 注意：MySQL LIKE 不支持复杂的自然语言检索，这里仅作为简单替代。
        // 实际生产中，即便没有ES，也可以考虑简单的关键词分词后再去数据库匹配。
        Page<PublicInfo> docPage = mysqlRepository.search(question, null, null, null, null, PageRequest.of(0, 5));
        List<PublicInfo> docs = docPage.getContent();
        
        List<String> refs = docs.stream().map(PublicInfo::getSourceUrl).filter(StringUtils::hasText).collect(Collectors.toList());
        
        // 2. 构建上下文
        String context = docs.stream()
                .map(d -> "标题: " + d.getTitle() + "\n正文: " + safeTrim(d.getContentText()))
                .collect(Collectors.joining("\n\n"));

        // 3. 调用通义千问
        Map<String, Object> body = new HashMap<>();
        body.put("model", props.getModel());
        List<Map<String, String>> messages = List.of(
                Map.of("role", "system", "content", "你是一个基于政务公开数据回答问题的助手，回答要简洁，给出来源链接。"),
                Map.of("role", "user", "content", buildUserPrompt(question, context, refs))
        );
        body.put("messages", messages);

        Map<String, String> headers = new HashMap<>();
        headers.put("Authorization", "Bearer " + props.getAccessKeySecret());
        headers.put("Content-Type", "application/json");

        String answer = callTongyi(props.getApiUrl(), body, headers);
        return new AiChatResponse(answer, refs);
    }

    private String buildUserPrompt(String question, String context, List<String> refs) {
        if (context.isBlank()) {
            return "用户问题：" + question + "\n\n没有找到相关政务信息，请直接回答。";
        }
        return "参考以下政务信息回答用户问题：\n\n" + context + "\n\n用户问题：" + question;
    }

    private String safeTrim(String s) {
        if (s == null) return "";
        int max = 800;
        return s.length() > max ? s.substring(0, max) : s;
    }

    private String callTongyi(String url, Map<String, Object> body, Map<String, String> headers) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            String json = mapper.writeValueAsString(body);
            org.springframework.http.HttpHeaders hh = new org.springframework.http.HttpHeaders();
            headers.forEach(hh::add);
            org.springframework.http.HttpEntity<String> entity = new org.springframework.http.HttpEntity<>(json, hh);
            org.springframework.http.ResponseEntity<String> resp = http.postForEntity(url, entity, String.class);
            if (resp.getBody() == null) return "";
            JsonNode root = mapper.readTree(resp.getBody());
            JsonNode choices = root.get("choices");
            if (choices != null && choices.isArray() && choices.size() > 0) {
                JsonNode msg = choices.get(0).get("message");
                if (msg != null && msg.get("content") != null) return msg.get("content").asText();
            }
            return "";
        } catch (Exception e) {
            return "服务暂不可用";
        }
    }
}
