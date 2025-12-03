package com.gov.ai.config;

import com.gov.ai.security.OriginRefererFilter;
import com.gov.ai.security.RateLimitFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class SecurityConfig {
    private final OriginRefererFilter originRefererFilter;
    private final RateLimitFilter rateLimitFilter;
    public SecurityConfig(OriginRefererFilter originRefererFilter, RateLimitFilter rateLimitFilter) {
        this.originRefererFilter = originRefererFilter;
        this.rateLimitFilter = rateLimitFilter;
    }
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http.csrf(csrf -> csrf.disable())
                .cors(Customizer.withDefaults())
                .authorizeHttpRequests(auth -> auth.requestMatchers("/**").permitAll())
                .httpBasic(Customizer.withDefaults());
        http.addFilterBefore(originRefererFilter, UsernamePasswordAuthenticationFilter.class);
        http.addFilterBefore(rateLimitFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }
}
