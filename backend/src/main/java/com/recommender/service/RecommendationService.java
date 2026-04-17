package com.recommender.service;

import com.recommender.dto.MlServiceDtos.*;
import com.recommender.dto.RecommendationDto;
import com.recommender.model.Product;
import com.recommender.model.Transaction;
import com.recommender.repository.ProductRepository;
import com.recommender.repository.TransactionRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Service that communicates with the Python ML microservice
 * for training models and fetching recommendations.
 */
@Service
@Slf4j
public class RecommendationService {

    private final WebClient webClient;
    private final ProductRepository productRepository;
    private final TransactionRepository transactionRepository;
    private final Duration timeout;

    public RecommendationService(
            WebClient.Builder webClientBuilder,
            ProductRepository productRepository,
            TransactionRepository transactionRepository,
            @Value("${ml-service.base-url}") String mlServiceBaseUrl,
            @Value("${ml-service.timeout-seconds}") int timeoutSeconds) {
        this.webClient = webClientBuilder.baseUrl(mlServiceBaseUrl).build();
        this.productRepository = productRepository;
        this.transactionRepository = transactionRepository;
        this.timeout = Duration.ofSeconds(timeoutSeconds);
        log.info("ML Service URL: {}", mlServiceBaseUrl);
    }

    /**
     * Train the ML models by sending all products and transaction history
     * to the Python service.
     */
    public TrainResponse trainModel() {
        log.info("Starting model training...");

        // Gather all products
        List<Product> products = productRepository.findAll();
        List<MlProduct> mlProducts = products.stream()
                .map(p -> MlProduct.builder()
                        .id(p.getId())
                        .name(p.getName())
                        .category(p.getCategory())
                        .price(p.getPrice())
                        .description(p.getDescription())
                        .build())
                .collect(Collectors.toList());

        // Gather all transactions
        List<Transaction> transactions = transactionRepository.findAll();
        List<MlTransaction> mlTransactions = transactions.stream()
                .map(t -> MlTransaction.builder()
                        .transactionId(String.valueOf(t.getId()))
                        .productIds(t.getProductIds())
                        .build())
                .collect(Collectors.toList());

        log.info("Sending {} products and {} transactions to ML service",
                mlProducts.size(), mlTransactions.size());

        TrainRequest request = TrainRequest.builder()
                .products(mlProducts)
                .transactions(mlTransactions)
                .build();

        try {
            TrainResponse response = webClient.post()
                    .uri("/train-model")
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(TrainResponse.class)
                    .timeout(timeout)
                    .block();

            log.info("Model training complete: {}", response != null ? response.getMessage() : "null");
            return response;
        } catch (Exception e) {
            log.error("Failed to train model: {}", e.getMessage());
            throw new RuntimeException("ML Service training failed: " + e.getMessage(), e);
        }
    }

    /**
     * Get product recommendations based on cart contents.
     *
     * @param cartProductIds Product IDs currently in the cart
     * @param topN           Number of recommendations to return
     * @return List of recommendation DTOs with product details and explanations
     */
    public List<RecommendationDto> getRecommendations(List<Long> cartProductIds, int topN) {
        if (cartProductIds == null || cartProductIds.isEmpty()) {
            log.warn("Empty cart, no recommendations to generate");
            return new ArrayList<>();
        }

        log.info("Fetching recommendations for cart: {}", cartProductIds);

        RecommendRequest request = RecommendRequest.builder()
                .cartProductIds(cartProductIds)
                .topN(topN)
                .build();

        try {
            RecommendResponse response = webClient.post()
                    .uri("/recommend")
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(RecommendResponse.class)
                    .timeout(timeout)
                    .block();

            if (response == null || response.getRecommendations() == null) {
                return new ArrayList<>();
            }

            // Enrich recommendations with full product details
            List<Long> recommendedIds = response.getRecommendations().stream()
                    .map(MlRecommendation::getProductId)
                    .collect(Collectors.toList());

            Map<Long, Product> productMap = productRepository.findByIdIn(recommendedIds).stream()
                    .collect(Collectors.toMap(Product::getId, p -> p));

            return response.getRecommendations().stream()
                    .filter(rec -> productMap.containsKey(rec.getProductId()))
                    .map(rec -> {
                        Product product = productMap.get(rec.getProductId());
                        List<RecommendationDto.ExplanationDto> explanations =
                                rec.getExplanations() != null
                                        ? rec.getExplanations().stream()
                                        .map(e -> RecommendationDto.ExplanationDto.builder()
                                                .method(e.getMethod())
                                                .score(e.getScore())
                                                .detail(e.getDetail())
                                                .build())
                                        .collect(Collectors.toList())
                                        : new ArrayList<>();

                        return RecommendationDto.builder()
                                .productId(product.getId())
                                .productName(product.getName())
                                .category(product.getCategory())
                                .price(product.getPrice())
                                .description(product.getDescription())
                                .imageUrl(product.getImageUrl())
                                .score(rec.getScore())
                                .explanations(explanations)
                                .build();
                    })
                    .collect(Collectors.toList());

        } catch (Exception e) {
            log.error("Failed to get recommendations: {}", e.getMessage());
            throw new RuntimeException("ML Service recommendation failed: " + e.getMessage(), e);
        }
    }

    /**
     * Check health of the ML service.
     */
    public HealthResponse checkMlServiceHealth() {
        try {
            return webClient.get()
                    .uri("/health")
                    .retrieve()
                    .bodyToMono(HealthResponse.class)
                    .timeout(Duration.ofSeconds(5))
                    .block();
        } catch (Exception e) {
            log.warn("ML service health check failed: {}", e.getMessage());
            HealthResponse response = new HealthResponse();
            response.setStatus("unavailable");
            response.setModelTrained(false);
            response.setRulesCount(0);
            return response;
        }
    }
}
