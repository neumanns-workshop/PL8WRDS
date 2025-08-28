import logging
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

from ..services import combination_generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

class GenerationMode(str, Enum):
    ALL = "all"
    RANDOM = "random"
    BATCH = "batch"

class CombinationRequest(BaseModel):
    lengths: List[int] = Field(..., description="A list of lengths for the combinations.")
    character_set: str = Field("abcdefghijklmnopqrstuvwxyz", description="The character set to use for generation.")
    generation_mode: GenerationMode = Field(GenerationMode.ALL, description="The mode of generation.")
    batch_size: Optional[int] = Field(10, description="The number of combinations to generate in 'batch' mode.")


class CombinationResponse(BaseModel):
    combinations: List[str]

@router.post("/generate-combinations", response_model=CombinationResponse)
async def generate_combinations_endpoint(request: CombinationRequest):
    """
    Generate all possible strings for the given lengths using the provided character set.
    """
    logger.info(f"Received request with mode: {request.generation_mode}, lengths: {request.lengths}, batch_size: {request.batch_size}")

    all_combinations = []
    for length in request.lengths:
        combinations_for_length = combination_generator.generate_combinations(
            character_set=request.character_set,
            length=length,
            mode=request.generation_mode,
            batch_size=request.batch_size
        )
        all_combinations.extend(combinations_for_length)
    
    return {"combinations": all_combinations}
