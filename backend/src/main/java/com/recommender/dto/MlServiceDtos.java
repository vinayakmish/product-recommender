package com.recommender.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;
import java.util.List;

/**
 * DTOs for communication with the Python ML microservice.
 */
public class MlServiceDtos {

    // --- Train Request/Response ---

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class MlProduct {
        private Long id;
        private String name;
        private String category;
        private Double price;
        private String description;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class MlTransaction {
        @JsonProperty("transaction_id")
        private String transactionId;

        @JsonProperty("product_ids")
        private List<Long> productIds;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class TrainRequest {
        private List<MlProduct> products;
        private List<MlTransaction> transactions;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TrainResponse {
        private String status;

        @JsonProperty("association_rules_count")
        private Integer associationRulesCount;

        @JsonProperty("similarity_matrix_shape")
        private List<Integer> similarityMatrixShape;

        private String message;
    }

    // --- Recommend Request/Response ---

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class RecommendRequest {
        @JsonProperty("cart_product_ids")
        private List<Long> cartProductIds;

        @JsonProperty("top_n")
        private Integer topN;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MlExplanation {
        private String method;
        private Double score;
        private String detail;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class MlRecommendation {
        @JsonProperty("product_id")
        private Long productId;

        private Double score;
        private List<MlExplanation> explanations;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RecommendResponse {
        private List<MlRecommendation> recommendations;

        @JsonProperty("model_info")
        private Object modelInfo;
    }

    // --- Health Check ---

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class HealthResponse {
        private String status;

        @JsonProperty("model_trained")
        private Boolean modelTrained;

        @JsonProperty("rules_count")
        private Integer rulesCount;
    }
}
