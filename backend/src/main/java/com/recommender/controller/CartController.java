package com.recommender.controller;

import com.recommender.dto.AddToCartRequest;
import com.recommender.dto.CartItemDto;
import com.recommender.service.CartService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST controller for shopping cart operations.
 */
@RestController
@RequestMapping("/api/cart")
@RequiredArgsConstructor
@Tag(name = "Cart", description = "Shopping cart management")
public class CartController {

    private final CartService cartService;

    @GetMapping("/{userId}")
    @Operation(summary = "Get cart items for a user")
    public ResponseEntity<List<CartItemDto>> getCart(@PathVariable Long userId) {
        return ResponseEntity.ok(cartService.getCartItems(userId));
    }

    @PostMapping("/{userId}/add")
    @Operation(summary = "Add a product to user's cart",
               description = "If product already exists in cart, quantity is incremented")
    public ResponseEntity<CartItemDto> addToCart(
            @PathVariable Long userId,
            @RequestBody AddToCartRequest request) {
        return ResponseEntity.ok(cartService.addToCart(userId, request));
    }

    @DeleteMapping("/{userId}/remove/{productId}")
    @Operation(summary = "Remove a product from user's cart")
    public ResponseEntity<Map<String, String>> removeFromCart(
            @PathVariable Long userId,
            @PathVariable Long productId) {
        cartService.removeFromCart(userId, productId);
        return ResponseEntity.ok(Map.of("message", "Product removed from cart"));
    }

    @DeleteMapping("/{userId}/clear")
    @Operation(summary = "Clear all items from user's cart")
    public ResponseEntity<Map<String, String>> clearCart(@PathVariable Long userId) {
        cartService.clearCart(userId);
        return ResponseEntity.ok(Map.of("message", "Cart cleared"));
    }
}
