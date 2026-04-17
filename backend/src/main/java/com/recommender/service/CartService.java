package com.recommender.service;

import com.recommender.dto.AddToCartRequest;
import com.recommender.dto.CartItemDto;
import com.recommender.model.CartItem;
import com.recommender.model.Product;
import com.recommender.model.User;
import com.recommender.repository.CartItemRepository;
import com.recommender.repository.ProductRepository;
import com.recommender.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Service for shopping cart operations.
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class CartService {

    private final CartItemRepository cartItemRepository;
    private final ProductRepository productRepository;
    private final UserRepository userRepository;

    /**
     * Get all cart items for a user.
     */
    public List<CartItemDto> getCartItems(Long userId) {
        return cartItemRepository.findByUserId(userId).stream()
                .map(this::toDto)
                .collect(Collectors.toList());
    }

    /**
     * Get product IDs in user's cart (for recommendation engine).
     */
    public List<Long> getCartProductIds(Long userId) {
        return cartItemRepository.findByUserId(userId).stream()
                .map(item -> item.getProduct().getId())
                .collect(Collectors.toList());
    }

    /**
     * Add a product to the user's cart. If already exists, increment quantity.
     */
    @Transactional
    public CartItemDto addToCart(Long userId, AddToCartRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found: " + userId));
        Product product = productRepository.findById(request.getProductId())
                .orElseThrow(() -> new RuntimeException("Product not found: " + request.getProductId()));

        int qty = request.getQuantity() != null ? request.getQuantity() : 1;

        // Check if product already in cart
        var existing = cartItemRepository.findByUserIdAndProductId(userId, request.getProductId());
        CartItem cartItem;

        if (existing.isPresent()) {
            cartItem = existing.get();
            cartItem.setQuantity(cartItem.getQuantity() + qty);
            log.info("Updated cart item quantity for user {}: product {} → qty {}",
                    userId, product.getName(), cartItem.getQuantity());
        } else {
            cartItem = CartItem.builder()
                    .user(user)
                    .product(product)
                    .quantity(qty)
                    .build();
            log.info("Added to cart for user {}: {} (qty: {})", userId, product.getName(), qty);
        }

        CartItem saved = cartItemRepository.save(cartItem);
        return toDto(saved);
    }

    /**
     * Remove a product from the user's cart.
     */
    @Transactional
    public void removeFromCart(Long userId, Long productId) {
        cartItemRepository.deleteByUserIdAndProductId(userId, productId);
        log.info("Removed product {} from cart for user {}", productId, userId);
    }

    /**
     * Clear all items from user's cart.
     */
    @Transactional
    public void clearCart(Long userId) {
        cartItemRepository.deleteByUserId(userId);
        log.info("Cleared cart for user {}", userId);
    }

    private CartItemDto toDto(CartItem item) {
        return CartItemDto.builder()
                .id(item.getId())
                .productId(item.getProduct().getId())
                .productName(item.getProduct().getName())
                .productCategory(item.getProduct().getCategory())
                .productPrice(item.getProduct().getPrice())
                .productImageUrl(item.getProduct().getImageUrl())
                .quantity(item.getQuantity())
                .build();
    }
}
