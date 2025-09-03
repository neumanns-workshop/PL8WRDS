# PL8WRDS Scoring Architecture 🎯

## Overview

The PL8WRDS scoring system uses a **3-dimensional ensemble approach** to evaluate the impressiveness of word-plate combinations. Each dimension captures a different aspect of cognitive challenge and linguistic sophistication.

## The 3 Core Dimensions

### 1. **Vocabulary Sophistication** (`frequency_scorer.py`)
- **Concept**: How rare/sophisticated is this word in general English usage?
- **Method**: Global corpus frequency analysis from SUBTLEX-US
- **Metrics**: 
  - Inverse frequency (rarer = higher score)
  - Percentile rarity (what % of words are more common)
  - Z-score deviation from mean frequency
- **Score Range**: 0-100 (100 = ultra-rare vocabulary)
- **Model**: `frequency_stats.json` (pre-computed frequency statistics)

### 2. **Information Content** (`information_scorer.py`)  
- **Concept**: How surprising is this solution given the plate constraints?
- **Method**: Shannon Information Theory - calculates `-log₂(P(word|plate))`
- **Metrics**:
  - Game-contextualized surprisal
  - Plate solution frequency analysis
  - Conditional probability estimation
- **Score Range**: 0-100 (100 = maximum surprisal/least expected)
- **Model**: `information_model.json` (14,998 plates with solution statistics)

### 3. **Orthographic Complexity** (`orthographic_scorer.py`)
- **Concept**: How cognitively challenging are the letter patterns to process?
- **Method**: N-gram probability analysis with boundary markers
- **Metrics**:
  - Bigram surprisal (average across word)
  - Trigram surprisal (average across word) 
  - Combined complexity score
- **Score Range**: 0-100 (100 = most complex letter patterns)
- **Model**: `orthographic_model.json` (n-gram probabilities from 74k word corpus)



## Ensemble Combination

### API Endpoint: `/predict/ensemble`

**Request**:
```json
{
  "word": "pedagogue",
  "plate": "PDG"
}
```

**Configurable Weights** (default ~0.33 each):
- `vocab_weight`: Vocabulary sophistication weight (default: 0.33)
- `info_weight`: Information content weight (default: 0.33)
- `ortho_weight`: Orthographic complexity weight (default: 0.34)

**Response**:
```json
{
  "ensemble_score": 76.9,
  "confidence": 1.0,
  "working_components": 3,
  "individual_scores": {
    "vocabulary": {"score": 85.2, "status": "success"},
    "information": {"score": 67.1, "status": "success"}, 
    "orthographic": {"score": 78.4, "status": "success"}
  },
  "weights_used": {"vocabulary": 0.33, "information": 0.33, "orthographic": 0.34}
}
```

### Graceful Degradation
- System handles component failures (e.g., words not in corpus)
- Confidence score reflects working components (0-1)
- Failed components contribute 0 to ensemble score
- Minimum 1 working component required

## Data Sources & Models

### Primary Corpus
- **File**: `data/words_with_freqs.json`
- **Source**: SUBTLEX-US frequency database
- **Size**: ~74,000 words with frequencies
- **Format**: `{"word": frequency_per_million, ...}`

### Pre-built Models
1. **`frequency_stats.json`**: Global frequency statistics and percentiles
2. **`information_model.json`**: Plate→solutions mapping with probabilities  
3. **`orthographic_model.json`**: N-gram probabilities with boundary analysis

### Model Building Scripts
- `build_information_model.py`: Comprehensive plate solution analysis
- `build_orthographic_model.py`: N-gram frequency analysis from corpus
- Built-in frequency stats generation in `frequency_scorer.py`

## API Structure

### Core Scoring Endpoints
- `/predict/vocabulary` - Vocabulary sophistication only
- `/predict/information` - Information content only
- `/predict/orthographic` - Orthographic complexity only
- `/predict/ensemble` - Combined 3-dimensional scoring

### Supporting Endpoints  
- `/solve/{plate}` - Find all valid words for plate
- `/generate/combinations` - Generate plate combinations
- `/corpus/stats` - Corpus statistics and health

## Gameplay Pipeline

### Full Workflow Example
1. **Generate plate**: `GET /generate/combinations`
2. **Find solutions**: `GET /solve/{plate}` 
3. **Score solutions**: `POST /predict/ensemble` (for each word)
4. **Rank by ensemble score**: Sort by `ensemble_score` descending

### Script: `gameplay_pipeline.py`
Demonstrates complete end-to-end gameplay with scoring.

## Performance Characteristics

### Scoring Speed
- **Vocabulary**: ~instant (lookup)
- **Information**: ~instant (lookup) 
- **Orthographic**: ~2-3ms (n-gram calculation)
- **Ensemble**: ~5-10ms total

### Coverage
- **Vocabulary**: 74k words from corpus
- **Information**: 15k plates with solutions
- **Orthographic**: Any word (calculated)

## Score Interpretation

### Tier System
- **🔥🔥🔥 LEGENDARY (80+)**: Top 2-5% of solutions
- **🔥🔥 MYTHIC (70-79)**: Top 10-15% of solutions
- **🔥 EPIC (60-69)**: Top 25-30% of solutions  
- **⭐ RARE (50-59)**: Above average solutions
- **Standard (<50)**: Common/easy solutions

### Typical Score Ranges
- **Easy words** (e.g., "big"/"BIG"): 25-45
- **Medium words** (e.g., "pedagogue"/"PDG"): 50-75
- **Hard words** (e.g., "razzmatazz"/"RZZ"): 75-95
- **Ultra-rare** (e.g., words with Q/X/Z): 85-100

## Configuration & Customization

### Swapping Word Sources
1. Replace `data/words_with_freqs.json` with new corpus
2. Rebuild models: `python build_information_model.py`
3. Rebuild models: `python build_orthographic_model.py`  
4. Restart API server

### Tuning Weights
- Adjust default weights in `/predict/ensemble` endpoint
- Use query parameters for per-request weight tuning
- Monitor `confidence` score for component health

### Adding New Dimensions
1. Create new scorer class following existing patterns
2. Add endpoint in `app/routers/prediction.py`
3. Integrate into ensemble endpoint
4. Update `total_components` and weight parameters

## Development & Testing

### Key Files
- `app/services/*_scorer.py`: Individual scoring implementations
- `app/routers/prediction.py`: API endpoints
- `build_*_model.py`: Model construction scripts
- `gameplay_pipeline.py`: End-to-end demonstration

### Validation Pipeline
- Individual scorer unit tests
- Ensemble integration tests
- Full gameplay workflow validation
- Performance benchmarking

## Future Enhancements

### Potential 4th+ Dimensions
- **Letter Frequency Rarity**: Rare letters (Q,X,Z,J) bonus
- **Spatial Challenge**: Character distribution and spacing
- **Morphological Complexity**: Prefix/suffix/root analysis
- **Phonetic Challenge**: Sound pattern difficulty
- **Semantic Distance**: Meaning relation to plate letters

### Corpus Improvements
- Larger vocabulary (100k+ words)
- Multiple frequency sources (books, news, social media)
- Domain-specific scoring (technical, literary, etc.)
- Multi-language support

---

*Last Updated: Simplified to 3-dimensional system during comprehensive analysis of all 17,576 possible plates*
