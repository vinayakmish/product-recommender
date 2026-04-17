package com.recommender.model;

import jakarta.persistence.*;
import lombok.*;

/**
 * Product entity representing items in the catalog.
 */
@Entity
@Table(name = "products")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 500)
    private String name;

    @Column(nullable = false)
    private String category;

    @Column(nullable = false)
    private Double price;

    @Column(length = 2000)
    private String description;

    @Column(name = "image_url")
    private String imageUrl;
}
