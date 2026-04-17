"""
Association Rule Mining service using FP-Growth algorithm.
Discovers frequently co-purchased product patterns.
"""
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import fpgrowth, association_rules
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class AssociationRuleEngine:
    """
    Uses FP-Growth algorithm to mine association rules from transaction data.
    
    How it works:
    1. Converts transactions into a binary matrix (product vs transaction)
    2. Finds frequent itemsets using FP-Growth (faster than Apriori)
    3. Generates association rules with confidence, support, and lift metrics
    
    Metrics explained:
    - Support: How often items appear together (frequency of co-occurrence)
    - Confidence: P(consequent | antecedent) - probability of buying B given A was bought
    - Lift: How much more likely items are bought together vs independently
      Lift > 1 means positive association
    """

    def __init__(self):
        self.rules: Optional[pd.DataFrame] = None
        self.product_id_to_name: Dict[int, str] = {}
        self.frequent_itemsets: Optional[pd.DataFrame] = None

    def train(
        self,
        transactions: List[List[int]],
        product_map: Dict[int, str],
        min_support: float = 0.05,
        min_confidence: float = 0.1,
        min_lift: float = 1.0,
    ) -> int:
        """
        Train the association rule model on transaction data.
        
        Args:
            transactions: List of transactions, each containing product IDs
            product_map: Mapping of product ID to product name
            min_support: Minimum support threshold (default 5%)
            min_confidence: Minimum confidence threshold (default 10%)
            min_lift: Minimum lift threshold (default 1.0)
            
        Returns:
            Number of rules discovered
        """
        self.product_id_to_name = product_map

        # Get all unique product IDs
        all_products = sorted(set(pid for txn in transactions for pid in txn))
        logger.info(f"Training on {len(transactions)} transactions with {len(all_products)} unique products")

        # Create binary transaction matrix
        # Each row = transaction, each column = product, value = 0/1
        data = []
        for txn in transactions:
            txn_set = set(txn)
            row = {pid: (pid in txn_set) for pid in all_products}
            data.append(row)

        df = pd.DataFrame(data)

        # Run FP-Growth to find frequent itemsets
        try:
            self.frequent_itemsets = fpgrowth(
                df, min_support=min_support, use_colnames=True
            )
            logger.info(f"Found {len(self.frequent_itemsets)} frequent itemsets")

            if len(self.frequent_itemsets) == 0:
                logger.warning("No frequent itemsets found. Try lowering min_support.")
                self.rules = pd.DataFrame()
                return 0

            # Generate association rules
            self.rules = association_rules(
                self.frequent_itemsets,
                metric="confidence",
                min_threshold=min_confidence,
                num_itemsets=len(self.frequent_itemsets),
            )

            # Filter by lift
            self.rules = self.rules[self.rules["lift"] >= min_lift]
            
            # Sort by confidence * lift for best recommendations
            self.rules["combined_score"] = self.rules["confidence"] * self.rules["lift"]
            self.rules = self.rules.sort_values("combined_score", ascending=False)

            logger.info(f"Generated {len(self.rules)} association rules")
            return len(self.rules)

        except Exception as e:
            logger.error(f"Error training association rules: {e}")
            self.rules = pd.DataFrame()
            return 0

    def get_recommendations(
        self, cart_product_ids: List[int], top_n: int = 5
    ) -> List[Tuple[int, float, str]]:
        """
        Get product recommendations based on association rules.
        
        Args:
            cart_product_ids: List of product IDs currently in cart
            top_n: Number of recommendations to return
            
        Returns:
            List of (product_id, score, explanation) tuples
        """
        if self.rules is None or len(self.rules) == 0:
            return []

        cart_set = frozenset(cart_product_ids)
        recommendations: Dict[int, Tuple[float, str]] = {}

        for _, rule in self.rules.iterrows():
            antecedent = rule["antecedents"]
            consequent = rule["consequents"]

            # Check if ALL antecedent items are in the cart
            if antecedent.issubset(cart_set):
                for product_id in consequent:
                    # Don't recommend items already in cart
                    if product_id not in cart_set:
                        score = float(rule["combined_score"])
                        support = float(rule["support"])
                        confidence = float(rule["confidence"])
                        lift = float(rule["lift"])

                        antecedent_names = [
                            self.product_id_to_name.get(pid, f"Product {pid}")
                            for pid in antecedent
                        ]
                        consequent_name = self.product_id_to_name.get(
                            product_id, f"Product {product_id}"
                        )

                        explanation = (
                            f"Customers who bought {', '.join(antecedent_names)} "
                            f"also bought {consequent_name} "
                            f"(Support: {support:.1%}, Confidence: {confidence:.1%}, Lift: {lift:.2f})"
                        )

                        # Keep the best score for each product
                        if product_id not in recommendations or score > recommendations[product_id][0]:
                            recommendations[product_id] = (score, explanation)

        # Sort by score and return top N
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1][0], reverse=True)
        return [(pid, score, explanation) for pid, (score, explanation) in sorted_recs[:top_n]]

    @property
    def rules_count(self) -> int:
        return len(self.rules) if self.rules is not None else 0
