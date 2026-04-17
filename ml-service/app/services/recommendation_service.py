"""
Recommendation orchestrator that combines Association Rules + Cosine Similarity.
"""
from typing import List, Dict, Tuple
from app.services.association_engine import AssociationRuleEngine
from app.services.similarity_engine import SimilarityEngine
from app.schemas.models import (
    RecommendedProduct,
    RecommendationExplanation,
)
import logging

logger = logging.getLogger(__name__)


class RecommendationOrchestrator:
    """
    Combines multiple recommendation strategies:
    
    1. Association Rules (FP-Growth): "Customers who bought X also bought Y"
       - Based on co-purchase patterns in transaction history
       - High precision for known patterns
       
    2. Cosine Similarity: "Products similar to what's in your cart"
       - Based on product features (category, price, description)
       - Handles cold-start better (works without transaction history)
    
    Scoring:
    - Association rules get higher weight (0.6) as they capture real buying behavior
    - Similarity gets lower weight (0.4) as a fallback and diversity mechanism
    - Final score = weighted combination, normalized to [0, 1]
    """

    def __init__(self):
        self.association_engine = AssociationRuleEngine()
        self.similarity_engine = SimilarityEngine()
        self.is_trained = False

    def train(
        self,
        products: List[Dict],
        transactions: List[List[int]],
    ) -> Dict:
        """
        Train both recommendation engines.
        
        Args:
            products: List of product dicts
            transactions: List of transaction product ID lists
            
        Returns:
            Training statistics
        """
        product_map = {p["id"]: p["name"] for p in products}

        # Train Association Rules
        rules_count = self.association_engine.train(
            transactions=transactions,
            product_map=product_map,
            min_support=0.03,   # Lower threshold for smaller datasets
            min_confidence=0.08,
            min_lift=0.8,
        )

        # Train Similarity Engine
        sim_shape = self.similarity_engine.train(products=products)

        self.is_trained = True
        logger.info(f"Training complete: {rules_count} rules, similarity matrix {sim_shape}")

        return {
            "rules_count": rules_count,
            "similarity_shape": list(sim_shape),
        }

    def recommend(
        self,
        cart_product_ids: List[int],
        top_n: int = 5,
        association_weight: float = 0.6,
        similarity_weight: float = 0.4,
    ) -> List[RecommendedProduct]:
        """
        Generate hybrid recommendations combining both engines.
        
        Args:
            cart_product_ids: Products in the user's cart
            top_n: Number of recommendations desired
            association_weight: Weight for association rule scores
            similarity_weight: Weight for similarity scores
            
        Returns:
            List of RecommendedProduct with explanations
        """
        if not self.is_trained:
            logger.warning("Models not trained yet")
            return []

        # Get recommendations from both engines
        assoc_recs = self.association_engine.get_recommendations(cart_product_ids, top_n * 2)
        sim_recs = self.similarity_engine.get_recommendations(cart_product_ids, top_n * 2)

        # Combine scores
        combined: Dict[int, Dict] = {}

        # Process association rule recommendations
        for pid, score, explanation in assoc_recs:
            if pid not in combined:
                combined[pid] = {"score": 0.0, "explanations": []}
            combined[pid]["score"] += score * association_weight
            combined[pid]["explanations"].append(
                RecommendationExplanation(
                    method="association_rules",
                    score=round(score, 4),
                    detail=explanation,
                )
            )

        # Process similarity recommendations
        for pid, score, explanation in sim_recs:
            if pid not in combined:
                combined[pid] = {"score": 0.0, "explanations": []}
            combined[pid]["score"] += score * similarity_weight
            combined[pid]["explanations"].append(
                RecommendationExplanation(
                    method="cosine_similarity",
                    score=round(score, 4),
                    detail=explanation,
                )
            )

        # Sort by combined score
        sorted_products = sorted(combined.items(), key=lambda x: x[1]["score"], reverse=True)

        results = []
        for pid, data in sorted_products[:top_n]:
            results.append(
                RecommendedProduct(
                    product_id=pid,
                    score=round(data["score"], 4),
                    explanations=data["explanations"],
                )
            )

        logger.info(
            f"Generated {len(results)} recommendations for cart {cart_product_ids}"
        )
        return results
