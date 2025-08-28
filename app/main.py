from fastapi import FastAPI
from .routers import (
    solver,
    scoring,
    dataset,
    corpus,
    combinations,
    dictionary,
    prediction,
    metrics
)
from .services.scoring_service import scoring_service
from .services.prediction_service import prediction_service
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PL8WRDS API",
    description="License plate word game API with AI scoring",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Tasks to run on application startup."""
    logger.info("Application startup...")
    # Initialize the prediction service (which loads the regression model)
    await prediction_service.initialize()
    logger.info("Prediction service initialized.")


# Include routers
app.include_router(solver.router)
app.include_router(scoring.router)
app.include_router(metrics.router)
app.include_router(dataset.router)
app.include_router(corpus.router)
app.include_router(combinations.router)
app.include_router(dictionary.router)
app.include_router(prediction.router)

@app.get("/", include_in_schema=False)
async def read_root():
    return {"message": "Welcome to PL8WRDS API"}
