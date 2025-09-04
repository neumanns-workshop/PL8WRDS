# 🔧 PL8WRDS API Reference

Simple API documentation for customizing PL8WRDS scoring (optional - game works without this).

## 🎯 Quick Start

```bash
# Install and start API
pip install -r requirements.txt
python rebuild_all_models.py  # Takes ~10 minutes
uvicorn app.main:app --reload

# Test basic functionality
curl http://localhost:8000/health
curl http://localhost:8000/solve/ABC
```

**Base URL**: `http://localhost:8000`  
**Interactive Docs**: `http://localhost:8000/docs`

---

## 📋 Core Endpoints

### 🔍 Word Solving

#### `GET /solve/{plate}`
Find all English words that match a license plate pattern.

**Parameters:**
- `plate` (path): 3-8 character license plate (letters only)

**Example:**
```bash
curl "http://localhost:8000/solve/PDG"
```

**Response:**
```json
{
  "plate": "PDG",
  "solutions": ["pedagogue", "pudgier", "pledging", ...],
  "count": 15,
  "execution_time": "0.042s"
}
```

---

### 🎯 Ensemble Scoring (Main Endpoint)

#### `POST /predict/ensemble`
Complete 3D scoring with vocabulary, information, and orthographic components.

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
  "interpretation": "Sophisticated word with good balance across dimensions"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/predict/ensemble" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "pedagogue",
    "plate": "PDG"
  }'
```

---

### 📊 Individual Scoring Components

#### `POST /predict/vocabulary`
Vocabulary sophistication scoring based on word frequency.

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
Information content scoring using Shannon information theory.

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
Orthographic complexity scoring based on letter pattern analysis.

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

---

### 📈 System Information

#### `GET /corpus/stats`
Corpus statistics and health information.

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

#### `GET /health`
Basic system health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

#### `GET /dataset/status`
Current system status and active endpoints.

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

---

## 🎮 Usage Examples

### Basic Gameplay Workflow

```python
import httpx
import asyncio

async def play_plate(plate: str):
    async with httpx.AsyncClient() as client:
        # 1. Find all solutions
        solutions_resp = await client.get(f"http://localhost:8000/solve/{plate}")
        solutions = solutions_resp.json()["solutions"]
        print(f"Plate {plate} has {len(solutions)} solutions")
        
        # 2. Score top solutions
        scored_solutions = []
        for word in solutions[:5]:  # Top 5 solutions
            score_resp = await client.post(
                "http://localhost:8000/predict/ensemble",
                json={"word": word, "plate": plate}
            )
            if score_resp.status_code == 200:
                data = score_resp.json()
                scored_solutions.append({
                    "word": word,
                    "score": data["ensemble_score"]
                })
        
        # 3. Show results
        scored_solutions.sort(key=lambda x: x["score"], reverse=True)
        for solution in scored_solutions:
            print(f"{solution['word']:>12}: {solution['score']:.1f}")

# Run example
asyncio.run(play_plate("PDG"))
```

### Custom Weight Configuration

```python
async def score_with_custom_weights():
    async with httpx.AsyncClient() as client:
        # Emphasize vocabulary over other dimensions
        weights = {
            "vocabulary": 2.0,     # Double weight
            "information": 1.0,
            "orthographic": 0.5    # Half weight  
        }
        
        response = await client.post(
            "http://localhost:8000/predict/ensemble",
            json={
                "word": "pedagogue",
                "plate": "PDG", 
                "weights": weights
            }
        )
        
        result = response.json()
        print(f"Custom weighted score: {result['ensemble_score']:.1f}")
```

### Batch Processing

```python
async def batch_score_words(plate: str, words: list):
    async with httpx.AsyncClient() as client:
        tasks = []
        for word in words:
            task = client.post(
                "http://localhost:8000/predict/ensemble",
                json={"word": word, "plate": plate}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        results = []
        for response in responses:
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "word": data["word"],
                    "ensemble": data["ensemble_score"],
                    "vocabulary": data["individual_scores"]["vocabulary"]["score"],
                    "information": data["individual_scores"]["information"]["score"],
                    "orthographic": data["individual_scores"]["orthographic"]["score"]
                })
        
        return sorted(results, key=lambda x: x["ensemble"], reverse=True)
```

---

## 🏆 Score Interpretation

### Score Ranges (0-100)
- **90-100**: Exceptional (ultra-rare, maximum complexity)
- **70-89**: Excellent (sophisticated, high difficulty)
- **50-69**: Good (above average, moderate complexity)
- **30-49**: Fair (average vocabulary, simple patterns)
- **0-29**: Poor (common words, basic patterns)

### Dimension Details

#### Vocabulary Sophistication
- **Data Source**: 103,949-word corpus with frequency analysis
- **90+**: Top 1% rarest words (e.g., "faqir", "quetzal")
- **70-89**: Top 5-10% sophisticated vocabulary
- **Example**: "pedagogue" = 77 (sophisticated academic word)

#### Information Content
- **Formula**: `-log₂(P(word|plate))` normalized to 0-100
- **90+**: Extremely surprising solution (very few alternatives)
- **70-89**: High information, unexpected choice
- **Example**: "pedagogue" for "PDG" = 65 (moderate surprisal, 15 total solutions)

#### Orthographic Complexity
- **Analysis**: N-gram patterns (trigrams + quartets)
- **90+**: Maximum cognitive difficulty (complex patterns)
- **70-89**: High pattern complexity, difficult to process
- **Example**: "pedagogue" = 54 (moderate complexity)

---

## 🚨 Error Handling

### Common HTTP Status Codes
- **200**: Success
- **400**: Invalid request (malformed JSON, invalid plate format)
- **404**: Resource not found (word not in corpus)
- **422**: Validation error (missing required fields)
- **500**: Internal server error (model loading issues)

### Error Response Format
```json
{
  "detail": "Error message describing the issue",
  "error_code": "SPECIFIC_ERROR_CODE",
  "status_code": 400
}
```

### Common Errors

#### Invalid Plate Format
```json
{
  "detail": "Invalid plate format. Must be 3-8 letters only.",
  "error_code": "INVALID_PLATE_FORMAT"
}
```

#### Word Not Found
```json
{
  "detail": "Word 'invalidword' not found in corpus",
  "error_code": "WORD_NOT_FOUND"
}
```

#### Missing Request Body
```json
{
  "detail": "Request body required for POST endpoints",
  "error_code": "MISSING_REQUEST_BODY"
}
```

---

## 🚨 Common Issues

**API won't start**: Run `python rebuild_all_models.py` first

**"Word not found"**: Word must be in the 103k word corpus

**Slow responses**: Model loading takes time on first request

**Port conflicts**: Use `uvicorn app.main:app --port 8001`

---

## 💡 Note

The React game includes all pre-computed scores and works completely offline. This API is only needed if you want to customize scoring algorithms or build your own integrations.

**For most users**: Just use the game at `pl8wrds.gbe.games` 🎮
