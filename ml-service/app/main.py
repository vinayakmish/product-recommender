"""
FastAPI ML Recommendation Microservice
=======================================
Provides product recommendations using:
1. Association Rule Mining (FP-Growth) - discovers co-purchase patterns
2. Cosine Similarity - finds products with similar features

Endpoints:
- POST /train-model  → Train the recommendation models
- POST /recommend    → Get recommendations for cart items
- GET  /health       → Service health check
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas.models import (
    TrainRequest,
    TrainResponse,
    RecommendRequest,
    RecommendResponse,
    HealthResponse,
)
from app.services.recommendation_service import RecommendationOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global recommendation engine instance
recommender = RecommendationOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup + shutdown."""
    logger.info("🚀 ML Recommendation Service starting up...")
    yield
    logger.info("🛑 ML Recommendation Service shutting down...")


app = FastAPI(
    title="Product Recommendation ML Service",
    description=(
        "Machine Learning microservice for product recommendations. "
        "Uses FP-Growth association rules and cosine similarity."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - allow Spring Boot backend to call this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check if the service is running and models are trained."""
    return HealthResponse(
        status="healthy",
        model_trained=recommender.is_trained,
        rules_count=recommender.association_engine.rules_count,
    )


@app.post("/train-model", response_model=TrainResponse, tags=["Training"])
async def train_model(request: TrainRequest):
    """
    Train recommendation models on product catalog and transaction history.
    
    This endpoint accepts:
    - Product catalog (id, name, category, price, description)
    - Transaction history (list of product IDs per transaction)
    
    It trains two models:
    1. FP-Growth: Finds association rules from transaction patterns
    2. Cosine Similarity: Builds product feature similarity matrix
    """
    try:
        logger.info(
            f"Training request: {len(request.products)} products, "
            f"{len(request.transactions)} transactions"
        )

        products = [p.model_dump() for p in request.products]
        transactions = [t.product_ids for t in request.transactions]

        stats = recommender.train(products=products, transactions=transactions)

        return TrainResponse(
            status="success",
            association_rules_count=stats["rules_count"],
            similarity_matrix_shape=stats["similarity_shape"],
            message=(
                f"Models trained successfully. "
                f"Found {stats['rules_count']} association rules. "
                f"Similarity matrix: {stats['similarity_shape'][0]}x{stats['similarity_shape'][1]}"
            ),
        )

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@app.post("/recommend", response_model=RecommendResponse, tags=["Recommendations"])
async def get_recommendations(request: RecommendRequest):
    """
    Get product recommendations based on items currently in the user's cart.
    
    Returns hybrid recommendations combining:
    - Association rules (60% weight): "Frequently bought together"
    - Cosine similarity (40% weight): "Similar products"
    
    Each recommendation includes explanations with scores.
    """
    if not recommender.is_trained:
        raise HTTPException(
            status_code=400,
            detail="Models not trained yet. Call /train-model first.",
        )

    try:
        recommendations = recommender.recommend(
            cart_product_ids=request.cart_product_ids,
            top_n=request.top_n,
        )

        return RecommendResponse(
            recommendations=recommendations,
            model_info={
                "association_rules_count": recommender.association_engine.rules_count,
                "similarity_matrix_shape": recommender.similarity_engine.matrix_shape,
                "methods": ["FP-Growth Association Rules", "Cosine Similarity"],
                "weights": {"association_rules": 0.6, "cosine_similarity": 0.4},
            },
        )

    except Exception as e:
        logger.error(f"Recommendation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Recommendation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
