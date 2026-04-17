"""
Pydantic schemas for request/response models.
"""
from pydantic import BaseModel
from typing import List, Optional


class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float
    description: Optional[str] = ""


class Transaction(BaseModel):
    transaction_id: str
    product_ids: List[int]


class TrainRequest(BaseModel):
    products: List[Product]
    transactions: List[Transaction]


class RecommendRequest(BaseModel):
    cart_product_ids: List[int]
    top_n: int = 5


class RecommendationExplanation(BaseModel):
    method: str  # "association_rules" or "cosine_similarity"
    score: float
    detail: str


class RecommendedProduct(BaseModel):
    product_id: int
    score: float
    explanations: List[RecommendationExplanation]


class RecommendResponse(BaseModel):
    recommendations: List[RecommendedProduct]
    model_info: dict


class TrainResponse(BaseModel):
    status: str
    association_rules_count: int
    similarity_matrix_shape: List[int]
    message: str


class HealthResponse(BaseModel):
    status: str
    model_trained: bool
    rules_count: int
