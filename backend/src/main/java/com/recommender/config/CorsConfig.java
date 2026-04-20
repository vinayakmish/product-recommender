package com.recommender.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * CORS configuration to allow React frontend to call the backend APIs.
 */
@Configuration
public class CorsConfig {

    @Value("${FRONTEND_URL:}")
    private String frontendUrl;

    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                var mapping = registry.addMapping("/api/**")
                        .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                        .allowedHeaders("*");

                if (frontendUrl != null && !frontendUrl.isEmpty()) {
                    // Production: allow specific Vercel domain + localhost for dev
                    mapping.allowedOrigins(frontendUrl, "http://localhost:3000", "http://localhost:5173")
                           .allowCredentials(true);
                } else {
                    // Development: allow all origins
                    mapping.allowedOrigins("http://localhost:3000", "http://localhost:5173")
                           .allowCredentials(true);
                }
            }
        };
    }
}
