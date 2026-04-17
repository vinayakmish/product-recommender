package com.recommender.dto;

import lombok.*;

/**
 * DTO for adding/removing items from cart.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CartItemDto {
    private Long id;
    private Long productId;
    private String productName;
    private String productCategory;
    private Double productPrice;
    private String productImageUrl;
    private Integer quantity;
}
