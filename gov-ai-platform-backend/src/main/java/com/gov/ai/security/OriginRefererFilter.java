package com.gov.ai.security;

import com.gov.ai.config.SecurityProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpMethod;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

@Component
public class OriginRefererFilter extends OncePerRequestFilter {
    private final SecurityProperties props;
    public OriginRefererFilter(SecurityProperties props) { this.props = props; }
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
        if (HttpMethod.OPTIONS.matches(request.getMethod())) { filterChain.doFilter(request, response); return; }
        String origin = request.getHeader("Origin");
        String referer = request.getHeader("Referer");
        List<String> allow = props.getAllowedOrigins();
        if (origin == null && referer == null) {
            // Allow requests with no Origin/Referer (e.g. curl, server-to-server)
            // For stricter security, you might want to disable this in production or use API keys.
            filterChain.doFilter(request, response);
            return;
        }
        boolean ok = false;
        if (origin != null) {
            ok = allow.stream().anyMatch(o -> origin.startsWith(o));
        } else if (referer != null) {
            ok = allow.stream().anyMatch(o -> referer.startsWith(o));
        }
        if (!ok) { response.setStatus(403); return; }
        filterChain.doFilter(request, response);
    }
}

