package com.recommender.dto;

import lombok.*;
import java.util.List;

/**
 * DTO for a single recommendation with explanations.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RecommendationDto {
    private Long productId;
    private String productName;
    private String category;
    private Double price;
    private String description;
    private String imageUrl;
    private Double score;
    private List<ExplanationDto> explanations;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class ExplanationDto {
        private String method;
        private Double score;
        private String detail;
    }
}
