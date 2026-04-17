package com.recommender.dto;

import lombok.*;

/**
 * DTO for product data in API responses.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ProductDto {
    private Long id;
    private String name;
    private String category;
    private Double price;
    private String description;
    private String imageUrl;
}
