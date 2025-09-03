# PL8WRDS API Documentation

## Overview

PL8WRDS is a sophisticated word game scoring system that evaluates the impressiveness of word solutions for license plate patterns. The system uses a 3-dimensional scoring approach combining vocabulary sophistication, information theory, and orthographic complexity.

## System Architecture

### 3-Dimensional Scoring System

The core scoring system evaluates words across three independent dimensions:

1. **Vocabulary Sophistication** - Global corpus frequency analysis
2. **Information Content** - Shannon information theory (`-log₂(P(word|plate))`)
3. **Orthographic Complexity** - N-gram pattern analysis for cognitive difficulty

### Corpus

- **Source**: WordNet-filtered Hermit Dave frequency corpus
- **Size**: 103,949 verified English words
- **Quality**: Filtered using NLTK WordNet as ground truth for legitimate vocabulary
- **Coverage**: Eliminates 90.4% of junk (typos, foreign words, nonsense)

## API Endpoints

### 1. Word Solving

#### `GET /solve/{plate}`
Finds all possible English words that match a license plate pattern.

**Parameters:**
- `plate` (path): License plate pattern (3-8 characters, letters only)

**Example:**
```bash
curl "http://localhost:8000/solve/PDG"
```

**Response:**
```json
{
  "plate": "PDG",
  "solutions": ["pedagogue", "pudgier", ...],
  "count": 15,
  "execution_time": "0.042s"
}
```

### 2. Individual Scoring Components

#### `POST /predict/vocabulary`
Scores vocabulary sophistication based on global corpus frequency.

**Request Body:**
```json
{
  "word": "pedagogue"
}
```

**Response:**
```json
{
  "word": "pedagogue",
  "scores": {
    "inverse_frequency": 73.3,
    "percentile_rarity": 95,
    "z_score_rarity": 49.4,
    "combined": 77.2
  },
  "raw_metrics": {
    "frequency": 60,
    "log_frequency": 4.111,
    "z_score": -0.037
  },
  "context": {
    "frequency_rank": 46582,
    "total_corpus_words": 103949,
    "corpus_frequency_percentile": 5
  },
  "interpretation": {
    "inverse_frequency": "Uncommon word (above average vocabulary)",
    "percentile": "Top 5% rarest words",
    "combined": "High vocabulary sophistication"
  }
}
```

#### `POST /predict/information`
Scores information content using Shannon information theory.

**Request Body:**
```json
{
  "word": "pedagogue",
  "plate": "PDG"
}
```

**Response:**
```json
{
  "word": "pedagogue",
  "plate": "PDG",
  "information_content": 3.906,
  "information_score": 65,
  "plate_solutions": 15,
  "word_probability": 0.067,
  "interpretation": "Moderate information content - somewhat surprising solution"
}
```

#### `POST /predict/orthographic`
Scores orthographic complexity based on n-gram pattern analysis.

**Request Body:**
```json
{
  "word": "pedagogue"
}
```

**Response:**
```json
{
  "word": "pedagogue",
  "orthographic_score": 54,
  "ngram_analysis": {
    "word_length": 9,
    "total_ngrams": 28,
    "avg_ngram_probability": 0.0089
  },
  "complexity_breakdown": {
    "trigrams": ["ped", "eda", "dag", "ago", "gog", "ogu", "gue"],
    "avg_trigram_prob": 0.0045,
    "quartets": ["peda", "edag", "dago", "agog", "gogue"],
    "avg_quartet_prob": 0.0021
  },
  "interpretation": "Moderate orthographic complexity"
}
```

### 3. Ensemble Scoring

#### `POST /predict/ensemble`
**Main endpoint** - Combines all three dimensions into a weighted ensemble score.

**Request Body:**
```json
{
  "word": "pedagogue",
  "plate": "PDG",
  "weights": {
    "vocabulary": 1.0,
    "information": 1.0,
    "orthographic": 1.0
  }
}
```

**Response:**
```json
{
  "word": "pedagogue",
  "plate": "PDG",
  "ensemble_score": 65.2,
  "individual_scores": {
    "vocabulary": {
      "score": 77,
      "weight": 1.0,
      "contribution": 25.7
    },
    "information": {
      "score": 65,
      "weight": 1.0,
      "contribution": 21.7
    },
    "orthographic": {
      "score": 54,
      "weight": 1.0,
      "contribution": 18.0
    }
  },
  "scoring_breakdown": {
    "total_weighted_score": 196.0,
    "total_weights": 3.0,
    "normalized_score": 65.2
  },
  "interpretation": "Sophisticated word with good balance across dimensions"
}
```

### 4. System Information

#### `GET /corpus/stats`
Returns corpus statistics and health information.

**Response:**
```json
{
  "total_words": 103949,
  "frequency_range": {
    "min": 1,
    "max": 4764010,
    "median": 40,
    "mean": 3539.0
  },
  "corpus_source": "WordNet-filtered Hermit Dave",
  "quality_metrics": {
    "filtered_percentage": 90.4,
    "ground_truth": "NLTK WordNet"
  }
}
```

#### `GET /dataset/status`
Returns current system status and active endpoints.

**Response:**
```json
{
  "message": "Using new 3D scoring system",
  "old_dataset": "disabled", 
  "active_endpoints": [
    "/predict/ensemble - 3D scoring system",
    "/solve/{plate} - word solver",
    "/corpus/stats - corpus statistics"
  ]
}
```

## Usage Workflows

### Basic Word Scoring Workflow

```bash
# 1. Find all solutions for a plate
curl "http://localhost:8000/solve/PDG"

# 2. Score a specific solution
curl -X POST "http://localhost:8000/predict/ensemble" \
  -H "Content-Type: application/json" \
  -d '{"word": "pedagogue", "plate": "PDG"}'

# 3. Get detailed breakdown of individual components
curl -X POST "http://localhost:8000/predict/vocabulary" \
  -H "Content-Type: application/json" \
  -d '{"word": "pedagogue"}'
```

### Gameplay Pipeline

```python
import asyncio
import httpx

async def analyze_plate(plate: str):
    """Complete analysis of a license plate."""
    async with httpx.AsyncClient() as client:
        # 1. Find all solutions
        solutions_resp = await client.get(f"http://localhost:8000/solve/{plate}")
        solutions = solutions_resp.json()["solutions"]
        
        # 2. Score each solution
        scored_solutions = []
        for word in solutions[:10]:  # Limit for performance
            score_resp = await client.post(
                "http://localhost:8000/predict/ensemble",
                json={"word": word, "plate": plate}
            )
            if score_resp.status_code == 200:
                scored_solutions.append(score_resp.json())
        
        # 3. Rank by ensemble score
        scored_solutions.sort(key=lambda x: x["ensemble_score"], reverse=True)
        
        return {
            "plate": plate,
            "total_solutions": len(solutions),
            "top_solutions": scored_solutions[:5]
        }

# Usage
result = asyncio.run(analyze_plate("PDG"))
```

### Custom Weight Tuning

```python
# Emphasize vocabulary sophistication
weights = {
    "vocabulary": 2.0,    # Double weight
    "information": 1.0,
    "orthographic": 0.5   # Half weight
}

response = await client.post(
    "http://localhost:8000/predict/ensemble",
    json={
        "word": "pedagogue", 
        "plate": "PDG",
        "weights": weights
    }
)
```

## Scoring Interpretation

### Score Ranges
- **90-100**: Exceptional (ultra-rare, maximum complexity)
- **70-89**: Excellent (sophisticated, high difficulty)
- **50-69**: Good (above average, moderate complexity)
- **30-49**: Fair (average vocabulary, simple patterns)
- **0-29**: Poor (common words, basic patterns)

### Dimension Interpretations

#### Vocabulary (0-100)
- **90+**: Top 1% rarest words (e.g., "faqir", "quetzal")
- **70-89**: Top 5-10% sophisticated vocabulary
- **50-69**: Above average, educated vocabulary
- **30-49**: Common but legitimate words
- **0-29**: Very frequent, basic vocabulary

#### Information Content (0-100)
- **90+**: Extremely surprising solution (very few alternatives)
- **70-89**: High information, unexpected choice
- **50-69**: Moderate surprisal, reasonable alternatives exist
- **30-49**: Lower information, many alternatives
- **0-29**: Predictable solution, obvious choice

#### Orthographic Complexity (0-100)
- **90+**: Maximum cognitive difficulty (complex n-gram patterns)
- **70-89**: High pattern complexity, difficult to process
- **50-69**: Moderate complexity, some unusual patterns
- **30-49**: Standard patterns, moderate processing
- **0-29**: Simple patterns, easy cognitive processing

## Error Handling

### Common Error Responses

#### Invalid Plate Format
```json
{
  "detail": "Invalid plate format. Must be 3-8 letters only."
}
```

#### Word Not Found
```json
{
  "detail": "Word 'invalidword' not found in corpus"
}
```

#### Missing Request Body
```json
{
  "detail": "Request body required for POST endpoints"
}
```

## Performance Characteristics

### Response Times
- **Solver endpoint**: 20-100ms (depends on pattern complexity)
- **Individual scorers**: 10-50ms
- **Ensemble scoring**: 50-150ms
- **Full plate analysis**: 500ms-2s (depends on solution count)

### Rate Limits
- No explicit rate limiting currently implemented
- Performance degrades with concurrent requests > 10

## Technical Details

### Model Files
- `models/information_model.json`: Information content probabilities (655MB)
- `models/orthographic_model.json`: N-gram probability model (310KB)
- `data/words_with_freqs.json`: WordNet-filtered corpus (8.5MB)

### Dependencies
- FastAPI for API framework
- NLTK WordNet for corpus validation
- Mathematical models for scoring computation
- Asyncio for concurrent processing

### System Requirements
- Python 3.8+
- 2GB+ RAM (for model loading)
- 1GB+ disk space (for models and corpus)

---

*Last Updated: Current Date*
*API Version: 3D Ensemble System*
