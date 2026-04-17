package com.recommender.dto;

import lombok.*;

/**
 * Request body for adding a product to cart.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AddToCartRequest {
    private Long productId;
    private Integer quantity;
}
