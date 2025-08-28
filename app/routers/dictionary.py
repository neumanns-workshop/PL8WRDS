from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.word_service import word_service

router = APIRouter()

class WordLookupResponse(BaseModel):
    word: str
    frequency: int

@router.get("/lookup/{word}", response_model=WordLookupResponse)
async def lookup_word(word: str):
    """
    Looks up a word in the dictionary and returns its frequency.
    """
    frequency = word_service.lookup_word(word)
    if frequency is None:
        raise HTTPException(status_code=404, detail="Word not found")
    
    return {"word": word, "frequency": frequency}
