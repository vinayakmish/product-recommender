package com.recommender.service;

import com.recommender.dto.ProductDto;
import com.recommender.model.Product;
import com.recommender.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Service for product catalog operations.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ProductService {

    private final ProductRepository productRepository;

    public List<ProductDto> getAllProducts() {
        return productRepository.findAll().stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    public ProductDto getProductById(Long id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Product not found: " + id));
        return toDto(product);
    }

    public List<ProductDto> getProductsByCategory(String category) {
        return productRepository.findByCategory(category).stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    public List<ProductDto> searchProducts(String query) {
        return productRepository.findByNameContainingIgnoreCase(query).stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    public List<ProductDto> getProductsByIds(List<Long> ids) {
        return productRepository.findByIdIn(ids).stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    public ProductDto createProduct(ProductDto dto) {
        Product product = Product.builder()
                .name(dto.getName())
                .category(dto.getCategory())
                .price(dto.getPrice())
                .description(dto.getDescription())
                .imageUrl(dto.getImageUrl())
                .build();
        Product saved = productRepository.save(product);
        log.info("Created product: {} (ID: {})", saved.getName(), saved.getId());
        return toDto(saved);
    }

    private ProductDto toDto(Product product) {
        return ProductDto.builder()
                .id(product.getId())
                .name(product.getName())
                .category(product.getCategory())
                .price(product.getPrice())
                .description(product.getDescription())
                .imageUrl(product.getImageUrl())
                .build();
    }
}
