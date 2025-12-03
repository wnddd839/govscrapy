package com.gov.ai.security;

import com.gov.ai.config.SecurityProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.Duration;

@Component
public class RateLimitFilter extends OncePerRequestFilter {
    private final StringRedisTemplate redis;
    private final SecurityProperties props;
    public RateLimitFilter(StringRedisTemplate redis, SecurityProperties props) { this.redis = redis; this.props = props; }
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isBlank()) ip = request.getRemoteAddr();
        String minute = String.valueOf(System.currentTimeMillis() / 60000);
        String key = "rl:" + ip + ":" + minute + ":" + request.getRequestURI();
        Long v = redis.opsForValue().increment(key);
        if (v != null && v == 1L) redis.expire(key, Duration.ofMinutes(1));
        if (v != null && v > props.getRateLimitPerMinute()) { response.setStatus(429); return; }
        filterChain.doFilter(request, response);
    }
}

