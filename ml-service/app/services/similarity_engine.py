"""
Cosine Similarity engine for product-to-product recommendations.
Uses product features (category, price range, TF-IDF of descriptions) to compute similarity.
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from scipy.sparse import hstack
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """
    Computes product similarity using cosine similarity on multiple features:
    
    1. Category (one-hot encoded) - products in same category are more similar
    2. Price (normalized) - products in similar price range are more similar  
    3. Description (TF-IDF) - products with similar descriptions are more similar
    
    The final similarity is a weighted combination of these feature similarities.
    """

    def __init__(self):
        self.similarity_matrix: Optional[np.ndarray] = None
        self.product_ids: List[int] = []
        self.product_id_to_idx: Dict[int, int] = {}
        self.product_id_to_name: Dict[int, str] = {}
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=500, stop_words="english", ngram_range=(1, 2)
        )
        self.category_encoder = OneHotEncoder(sparse_output=True, handle_unknown="ignore")
        self.price_scaler = MinMaxScaler()

    def train(
        self,
        products: List[Dict],
        category_weight: float = 0.4,
        price_weight: float = 0.2,
        description_weight: float = 0.4,
    ) -> Tuple[int, int]:
        """
        Build the similarity matrix from product features.
        
        Args:
            products: List of product dicts with id, name, category, price, description
            category_weight: Weight for category similarity
            price_weight: Weight for price similarity
            description_weight: Weight for description similarity
            
        Returns:
            Tuple of (matrix_rows, matrix_cols)
        """
        if not products:
            logger.warning("No products provided for similarity training")
            return (0, 0)

        df = pd.DataFrame(products)
        self.product_ids = df["id"].tolist()
        self.product_id_to_idx = {pid: idx for idx, pid in enumerate(self.product_ids)}
        self.product_id_to_name = dict(zip(df["id"], df["name"]))

        logger.info(f"Building similarity matrix for {len(products)} products")

        # 1. Category features (one-hot encoded)
        categories = df[["category"]].fillna("unknown")
        cat_features = self.category_encoder.fit_transform(categories)
        cat_sim = cosine_similarity(cat_features)

        # 2. Price features (normalized)
        prices = df[["price"]].fillna(0)
        price_normalized = self.price_scaler.fit_transform(prices)
        price_sim = cosine_similarity(price_normalized)

        # 3. Description features (TF-IDF)
        descriptions = df["description"].fillna("").tolist()
        # Add category to description for better context
        enriched_descriptions = [
            f"{row['category']} {row.get('description', '')}" for _, row in df.iterrows()
        ]
        desc_features = self.tfidf_vectorizer.fit_transform(enriched_descriptions)
        desc_sim = cosine_similarity(desc_features)

        # Weighted combination
        self.similarity_matrix = (
            category_weight * cat_sim
            + price_weight * price_sim
            + description_weight * desc_sim
        )

        # Zero out self-similarity to avoid recommending the same product
        np.fill_diagonal(self.similarity_matrix, 0)

        shape = self.similarity_matrix.shape
        logger.info(f"Similarity matrix shape: {shape}")
        return shape

    def get_recommendations(
        self, cart_product_ids: List[int], top_n: int = 5
    ) -> List[Tuple[int, float, str]]:
        """
        Get recommendations based on cosine similarity.
        
        For each product in cart, finds the most similar products.
        Aggregates scores across all cart items.
        
        Args:
            cart_product_ids: Product IDs in cart
            top_n: Number of recommendations
            
        Returns:
            List of (product_id, score, explanation) tuples
        """
        if self.similarity_matrix is None:
            return []

        cart_set = set(cart_product_ids)
        # Aggregate similarity scores across all cart items
        aggregated_scores: Dict[int, Tuple[float, str]] = {}

        for cart_pid in cart_product_ids:
            if cart_pid not in self.product_id_to_idx:
                continue

            idx = self.product_id_to_idx[cart_pid]
            similarities = self.similarity_matrix[idx]

            for other_idx, score in enumerate(similarities):
                other_pid = self.product_ids[other_idx]

                # Skip products already in cart
                if other_pid in cart_set:
                    continue

                if score > 0.01:  # Minimum threshold
                    cart_product_name = self.product_id_to_name.get(cart_pid, f"Product {cart_pid}")
                    other_name = self.product_id_to_name.get(other_pid, f"Product {other_pid}")
                    explanation = (
                        f"{other_name} is similar to {cart_product_name} "
                        f"in your cart (Similarity: {score:.1%})"
                    )

                    if other_pid not in aggregated_scores or score > aggregated_scores[other_pid][0]:
                        aggregated_scores[other_pid] = (float(score), explanation)

        sorted_recs = sorted(aggregated_scores.items(), key=lambda x: x[1][0], reverse=True)
        return [(pid, score, explanation) for pid, (score, explanation) in sorted_recs[:top_n]]

    @property
    def matrix_shape(self) -> List[int]:
        if self.similarity_matrix is not None:
            return list(self.similarity_matrix.shape)
        return [0, 0]
