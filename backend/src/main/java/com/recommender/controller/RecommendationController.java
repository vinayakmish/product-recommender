package com.recommender.controller;

import com.recommender.dto.MlServiceDtos.TrainResponse;
import com.recommender.dto.MlServiceDtos.HealthResponse;
import com.recommender.dto.RecommendationDto;
import com.recommender.service.CartService;
import com.recommender.service.RecommendationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST controller for ML-powered product recommendations.
 */
@RestController
@RequestMapping("/api/recommendations")
@RequiredArgsConstructor
@Tag(name = "Recommendations", description = "ML-powered product recommendations")
public class RecommendationController {

    private final RecommendationService recommendationService;
    private final CartService cartService;

    @PostMapping("/train")
    @Operation(summary = "Train the ML recommendation model",
               description = "Sends product catalog and transaction history to the ML service for training. " +
                       "This should be called after adding new transaction data.")
    public ResponseEntity<TrainResponse> trainModel() {
        TrainResponse response = recommendationService.trainModel();
        return ResponseEntity.ok(response);
    }

    @GetMapping("/cart/{userId}")
    @Operation(summary = "Get recommendations based on user's cart",
               description = "Returns top 5 recommended products based on what's currently in the user's cart. " +
                       "Uses both association rules (frequently bought together) and cosine similarity.")
    public ResponseEntity<List<RecommendationDto>> getCartRecommendations(
            @PathVariable Long userId,
            @RequestParam(defaultValue = "5") int topN) {
        List<Long> cartProductIds = cartService.getCartProductIds(userId);
        List<RecommendationDto> recommendations =
                recommendationService.getRecommendations(cartProductIds, topN);
        return ResponseEntity.ok(recommendations);
    }

    @PostMapping("/products")
    @Operation(summary = "Get recommendations for specific products",
               description = "Returns recommendations based on a list of product IDs (not tied to a user's cart)")
    public ResponseEntity<List<RecommendationDto>> getProductRecommendations(
            @RequestBody Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<Integer> productIdInts = (List<Integer>) body.get("productIds");
        List<Long> productIds = productIdInts.stream()
                .map(Integer::longValue)
                .toList();
        int topN = body.containsKey("topN") ? (int) body.get("topN") : 5;

        List<RecommendationDto> recommendations =
                recommendationService.getRecommendations(productIds, topN);
        return ResponseEntity.ok(recommendations);
    }

    @GetMapping("/health")
    @Operation(summary = "Check ML service health",
               description = "Returns the health status of the Python ML microservice")
    public ResponseEntity<HealthResponse> mlServiceHealth() {
        HealthResponse health = recommendationService.checkMlServiceHealth();
        return ResponseEntity.ok(health);
    }
}
