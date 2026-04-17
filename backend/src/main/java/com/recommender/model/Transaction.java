package com.recommender.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Transaction entity representing a completed purchase.
 * Used for training the ML recommendation model.
 */
@Entity
@Table(name = "transactions")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Transaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id")
    private Long userId;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(
        name = "transaction_items",
        joinColumns = @JoinColumn(name = "transaction_id")
    )
    @Column(name = "product_id")
    @Builder.Default
    private List<Long> productIds = new ArrayList<>();
}
