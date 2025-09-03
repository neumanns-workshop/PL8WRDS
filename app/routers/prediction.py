"""
FastAPI router for model-based score predictions.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from dependency_injector.wiring import Provide, inject

from ..core.container import Container
from ..application.services import PredictionService
from ..services.information_scorer import information_scorer
from ..services.frequency_scorer import frequency_scorer
from ..services.orthographic_scorer import orthographic_scorer


router = APIRouter(prefix="/predict", tags=["prediction"])

class PredictionRequest(BaseModel):
    word: str = Field(..., example="syzygy", description="The word to score.")
    plate: str = Field(..., min_length=3, max_length=3, example="SGY", description="The 3-letter plate.")

class PredictionResponse(BaseModel):
    word: str
    plate: str
    predicted_score: float
    model_version: str

@router.post("/score", response_model=PredictionResponse)
@inject
async def predict_score(
    request: PredictionRequest,
    prediction_service: PredictionService = Depends(Provide[Container.prediction_service])
):
    """
    Predict the impressiveness score of a word for a given 3-letter plate
    using the trained regression model.
    """
    try:
        result = await prediction_service.predict_score(request.word, request.plate)
        return PredictionResponse(
            word=result["word"],
            plate=result["plate"],
            predicted_score=result["predicted_score"],
            model_version=result.get("model", "ridge_regression")
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"Model not loaded: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/health")
@inject
async def prediction_health_check(
    prediction_service: PredictionService = Depends(Provide[Container.prediction_service])
):
    """Health check for the prediction service."""
    health_info = await prediction_service.health_check()
    status_code = 200 if health_info["status"] == "healthy" else 503
    
    return health_info

@router.get("/feature-importance")
@inject
async def get_feature_importance(
    top_k: int = Query(20, ge=1, le=100, description="Number of top features to return"),
    prediction_service: PredictionService = Depends(Provide[Container.prediction_service])
):
    """
    Get the most important features from the trained regression model.
    Shows which linguistic features have the strongest influence on predictions.
    """
    try:
        importance_data = await prediction_service.get_feature_importance(top_k=top_k)
        return importance_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feature importance: {e}")

@router.post("/explain")
@inject
async def explain_prediction(
    request: PredictionRequest,
    top_k: int = Query(10, ge=1, le=50, description="Number of top contributing features to return"),
    prediction_service: PredictionService = Depends(Provide[Container.prediction_service])
):
    """
    Explain a specific prediction by showing which features contributed most 
    to the predicted score for a given word-plate pair.
    """
    try:
        explanation = await prediction_service.explain_prediction(request.word, request.plate, top_k=top_k)
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to explain prediction: {e}")

# Frequency Scoring Endpoints

class FrequencyRequest(BaseModel):
    word: str = Field(..., example="pedagogue", description="The word to analyze")

class FrequencyResponse(BaseModel):
    word: str
    scores: Dict[str, float]
    raw_metrics: Dict[str, float]
    context: Dict[str, Any]
    interpretation: Dict[str, str]

@router.post("/frequency", response_model=FrequencyResponse)
async def score_frequency(request: FrequencyRequest):
    """
    Score a word based purely on global corpus frequency.
    
    Returns vocabulary sophistication scores:
    - Inverse Frequency: Higher for rarer words (vocabulary sophistication)
    - Percentile Rarity: Where this word ranks in the frequency distribution  
    - Z-Score Rarity: Statistical deviation from mean frequency
    - Combined: Weighted combination of all rarity measures
    
    This measures vocabulary impressiveness independent of game constraints.
    """
    try:
        result = frequency_scorer.score_word(request.word)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return FrequencyResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Frequency scoring failed: {e}")

@router.get("/frequency/distribution")
async def get_frequency_distribution():
    """Get corpus frequency distribution statistics."""
    try:
        distribution = frequency_scorer.get_frequency_distribution()
        return distribution
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get frequency distribution: {e}")

@router.post("/frequency/batch")
async def batch_score_frequency(words: List[str]):
    """
    Score multiple words with frequency analysis.
    Shows relative vocabulary sophistication across different words.
    """
    try:
        results = frequency_scorer.batch_score(words)
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch frequency scoring failed: {e}")

@router.get("/frequency/rarest-words")
async def get_rarest_words(limit: int = Query(20, ge=1, le=100)):
    """
    Get the rarest words in the corpus by frequency.
    Shows the most sophisticated vocabulary available.
    """
    try:
        rare_words = frequency_scorer.get_top_rare_words(limit)
        return {
            "rarest_words": rare_words,
            "count": len(rare_words),
            "description": "Words ranked by corpus frequency rarity"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rarest words: {e}")

# Orthographic Complexity Scoring Endpoints

class OrthographicRequest(BaseModel):
    word: str = Field(..., example="ambulance", description="The word to analyze")
    plate: str = Field(..., example="ABC", description="The license plate letters")

class OrthographicResponse(BaseModel):
    word: str
    plate: str
    matching_sequence: str
    scores: Dict[str, float]
    raw_metrics: Dict[str, float]
    ngram_details: Dict[str, Any]
    interpretation: Dict[str, str]

@router.post("/orthographic", response_model=OrthographicResponse)
async def score_orthographic_complexity(request: OrthographicRequest):
    """
    Score a word-plate combination using orthographic complexity analysis.
    
    Returns letter pattern complexity scores:
    - Bigram Complexity: How unusual the 2-letter sequences are
    - Trigram Complexity: How unusual the 3-letter sequences are  
    - Combined Complexity: Weighted combination emphasizing trigrams
    
    This measures cognitive processing difficulty of letter patterns
    independent of vocabulary sophistication or game constraints.
    """
    try:
        result = orthographic_scorer.score_word_plate(request.word, request.plate)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return OrthographicResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orthographic scoring failed: {e}")

@router.get("/orthographic/model-stats")
async def get_orthographic_model_stats():
    """Get statistics about the loaded orthographic complexity model."""
    try:
        stats = orthographic_scorer.get_model_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
            
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get orthographic model stats: {e}")

@router.post("/orthographic/batch")
async def batch_score_orthographic_complexity(word_plate_pairs: List[OrthographicRequest]):
    """
    Score multiple word-plate combinations with orthographic complexity analysis.
    Shows relative letter pattern processing difficulty across different solutions.
    """
    try:
        # Convert to tuple format expected by scorer
        pairs = [(req.word, req.plate) for req in word_plate_pairs]
        results = orthographic_scorer.batch_score(pairs)
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch orthographic scoring failed: {e}")



# Information Content Scoring Endpoints

class InformationRequest(BaseModel):
    word: str = Field(..., example="ambulance", description="The word to analyze")
    plate: str = Field(..., example="ABC", description="The license plate letters")

class InformationResponse(BaseModel):
    word: str
    plate: str
    scores: Dict[str, float]
    raw_metrics: Dict[str, float]
    context: Dict[str, Any]
    interpretation: Dict[str, str]

@router.post("/information", response_model=InformationResponse)
async def score_information_content(request: InformationRequest):
    """
    Score a word-plate combination using information theory.
    
    Returns information content scores:
    - Information Bits: Shannon information content (-log₂(P(word|plate)))
    - Normalized: Scaled to 0-100 based on plate's maximum possible information
    - Percentile: Where this word ranks among all solutions for this plate
    
    This measures how surprising/informative the word choice is given the constraints.
    """
    try:
        result = information_scorer.score_word(request.word, request.plate)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return InformationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Information scoring failed: {e}")

@router.get("/information/model-stats")
async def get_information_model_stats():
    """Get statistics about the loaded information content model."""
    try:
        stats = information_scorer.get_model_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
            
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get information model stats: {e}")

@router.post("/information/batch")
async def batch_score_information_content(word_plate_pairs: list[InformationRequest]):
    """
    Score multiple word-plate combinations with information content analysis.
    Shows relative information content across different word choices.
    """
    try:
        results = []
        for req in word_plate_pairs:
            result = information_scorer.score_word(req.word, req.plate)
            results.append(result)
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch information scoring failed: {e}")

@router.get("/information/top-words/{plate}")
async def get_top_information_words_for_plate(plate: str, limit: int = Query(10, ge=1, le=50)):
    """
    Get top words for a plate ranked by information content.
    Shows which solutions convey the most information bits given the constraints.
    """
    try:
        top_words = information_scorer.get_top_words_for_plate(plate, limit)
        return {
            "plate": plate,
            "top_words": top_words,
            "count": len(top_words),
            "description": "Words ranked by Shannon information content (bits)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get top information words: {e}")

# Ensemble Scoring Endpoints
class EnsembleRequest(BaseModel):
    word: str = Field(..., example="pedagogue", description="The word to analyze")
    plate: str = Field(..., example="PDG", description="The license plate letters")

class EnsembleResponse(BaseModel):
    word: str
    plate: str
    ensemble_score: float
    confidence: float = Field(description="Confidence based on number of working components (0-1)")
    weights_used: Dict[str, float]
    individual_scores: Dict[str, Any]
    working_components: int
    total_components: int = 3
    interpretation: str

@router.post("/ensemble", response_model=EnsembleResponse)
async def score_ensemble(
    request: EnsembleRequest,
    vocab_weight: float = Query(0.33, ge=0, le=1, description="Weight for vocabulary sophistication (0-1)"),
    info_weight: float = Query(0.33, ge=0, le=1, description="Weight for information content (0-1)"),
    ortho_weight: float = Query(0.34, ge=0, le=1, description="Weight for orthographic complexity (0-1)")
):
    """
    Ensemble endpoint that combines all three core scoring dimensions with configurable weights.
    
    Dimensions:
    - Vocabulary Sophistication: Global corpus frequency rarity
    - Information Content: Game-contextualized surprisal  
    - Orthographic Complexity: Letter pattern rarity
    
    Weights should sum to ~1.0 for best results. The system handles graceful degradation
    when some components fail (e.g., words not in corpus).
    """
    # Normalize weights to sum to 1.0
    total_weight = vocab_weight + info_weight + ortho_weight
    if total_weight == 0:
        raise HTTPException(status_code=400, detail="At least one weight must be non-zero")
    
    vocab_weight_norm = vocab_weight / total_weight
    info_weight_norm = info_weight / total_weight  
    ortho_weight_norm = ortho_weight / total_weight
    
    individual_scores = {}
    working_components = 0
    ensemble_components = []
    
    # 1. Vocabulary Sophistication (Frequency Scorer)
    try:
        freq_result = frequency_scorer.score_word(request.word)
        
        if "error" in freq_result:
            individual_scores["vocabulary"] = {
                "status": "failed",
                "error": freq_result["error"],
                "weight": vocab_weight_norm,
                "weighted_contribution": 0
            }
        else:
            individual_scores["vocabulary"] = {
                "status": "success",
                "score": freq_result["scores"]["combined"],
                "weight": vocab_weight_norm,
                "weighted_contribution": freq_result["scores"]["combined"] * vocab_weight_norm,
                "details": {
                    "frequency": freq_result["raw_metrics"]["frequency"],
                    "percentile_rarity": freq_result["scores"]["percentile_rarity"],
                    "interpretation": freq_result["interpretation"]["combined"]
                }
            }
            ensemble_components.append(freq_result["scores"]["combined"] * vocab_weight_norm)
            working_components += 1
    except Exception as e:
        individual_scores["vocabulary"] = {
            "status": "failed",
            "error": str(e),
            "weight": vocab_weight_norm,
            "weighted_contribution": 0
        }
    
    # 2. Information Content (Game Constraint Surprisal)
    try:
        info_result = information_scorer.score_word(request.word, request.plate)
        
        if "error" in info_result:
            individual_scores["information"] = {
                "status": "failed",
                "error": info_result["error"],
                "weight": info_weight_norm,
                "weighted_contribution": 0
            }
        else:
            individual_scores["information"] = {
                "status": "success", 
                "score": info_result["scores"]["normalized"],
                "weight": info_weight_norm,
                "weighted_contribution": info_result["scores"]["normalized"] * info_weight_norm,
                "details": {
                    "information_bits": info_result["scores"]["information_bits"],
                    "plate_solutions": info_result["context"]["plate_solutions"],
                    "interpretation": info_result["interpretation"]["overall"]
                }
            }
            ensemble_components.append(info_result["scores"]["normalized"] * info_weight_norm)
            working_components += 1
    except Exception as e:
        individual_scores["information"] = {
            "status": "failed",
            "error": str(e),
            "weight": info_weight_norm,
            "weighted_contribution": 0
        }
    
    # 3. Orthographic Complexity
    try:
        ortho_result = orthographic_scorer.score_word_plate(request.word, request.plate)
        
        if "error" in ortho_result:
            individual_scores["orthographic"] = {
                "status": "failed",
                "error": ortho_result["error"],
                "weight": ortho_weight_norm,
                "weighted_contribution": 0
            }
        else:
            individual_scores["orthographic"] = {
                "status": "success",
                "score": ortho_result["scores"]["combined_complexity"], 
                "weight": ortho_weight_norm,
                "weighted_contribution": ortho_result["scores"]["combined_complexity"] * ortho_weight_norm,
                "details": {
                    "matching_sequence": ortho_result["matching_sequence"],
                    "bigram_complexity": ortho_result["scores"]["bigram_complexity"],
                    "trigram_complexity": ortho_result["scores"]["trigram_complexity"], 
                    "interpretation": ortho_result["interpretation"]["overall_complexity"]
                }
            }
            ensemble_components.append(ortho_result["scores"]["combined_complexity"] * ortho_weight_norm)
            working_components += 1
    except Exception as e:
        individual_scores["orthographic"] = {
            "status": "failed",
            "error": str(e),
            "weight": ortho_weight_norm,
            "weighted_contribution": 0
        }
    

    
    # Calculate ensemble score and confidence
    if working_components == 0:
        raise HTTPException(status_code=500, detail="All scoring components failed")
    
    # Calculate ensemble score (sum of weighted contributions from working components)
    ensemble_score = sum(ensemble_components)
    
    # Confidence based on component availability
    confidence = working_components / 3.0
    
    # Generate interpretation
    if ensemble_score >= 80:
        interpretation = f"🔥 EXCEPTIONAL ({ensemble_score:.1f}/100) - Truly impressive solution!"
    elif ensemble_score >= 65:
        interpretation = f"⭐ EXCELLENT ({ensemble_score:.1f}/100) - Outstanding solution!"  
    elif ensemble_score >= 50:
        interpretation = f"👍 GOOD ({ensemble_score:.1f}/100) - Strong solution!"
    elif ensemble_score >= 35:
        interpretation = f"😊 DECENT ({ensemble_score:.1f}/100) - Solid solution!"
    elif ensemble_score >= 20:
        interpretation = f"😐 BASIC ({ensemble_score:.1f}/100) - Simple solution"
    else:
        interpretation = f"😴 MINIMAL ({ensemble_score:.1f}/100) - Very basic solution"
    
    # Add confidence qualifier
    if confidence < 1.0:
        interpretation += f" (confidence: {confidence:.1%} - {working_components}/3 components working)"
    
    return EnsembleResponse(
        word=request.word,
        plate=request.plate,
        ensemble_score=round(ensemble_score, 1),
        confidence=round(confidence, 3),
        weights_used={
            "vocabulary": round(vocab_weight_norm, 3),
            "information": round(info_weight_norm, 3), 
            "orthographic": round(ortho_weight_norm, 3)
        },
        individual_scores=individual_scores,
        working_components=working_components,
        interpretation=interpretation
    )
