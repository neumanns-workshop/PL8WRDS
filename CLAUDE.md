# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development Server
```bash
# Start the FastAPI development server
uvicorn app.main:app --reload --port 8000

# Access the API documentation
# - Interactive docs: http://127.0.0.1:8000/docs
# - Alternative docs: http://127.0.0.1:8000/redoc
```

### CLI Tools
```bash
# Score a single word using the CLI tool
python run_scoring.py score "ambulance" "abc" --models granite mistral

# Generate dataset for model training
python run_scoring.py dataset --plates 100 --words 5 --models granite mistral deepseek --output new_dataset.json

# Check system status
python run_scoring.py check
```

### Model Training
```bash
# Train a new regression model (requires feature cache)
python -m app.services.regression_trainer

# Trigger feature cache generation (computationally expensive)
curl -X POST http://127.0.0.1:8000/corpus/features/rebuild
```

### Testing
```bash
# Health check for prediction service
curl http://127.0.0.1:8000/predict/health

# Test prediction endpoint
curl -X POST "http://127.0.0.1:8000/predict/score" \
  -H "Content-Type: application/json" \
  -d '{"word": "ambulance", "plate": "ABC"}'
```

## Architecture Overview

### Core Components

**FastAPI Application** (`app/main.py`):
- Entry point that initializes services and includes all routers
- Handles startup tasks including prediction service initialization

**Service Layer** (`app/services/`):
- `prediction_service.py`: ML prediction using trained Ridge regression model
- `feature_extraction.py`: Comprehensive linguistic feature extraction for words
- `scoring_service.py`: LLM-based scoring using Ollama
- `solver_service.py`: Word discovery algorithms for license plate patterns
- `word_service.py`: Dictionary and frequency lookups
- `regression_trainer.py`: Model training pipeline

**API Routes** (`app/routers/`):
- `prediction.py`: ML-based scoring predictions (primary feature)
- `corpus.py`: Corpus statistics and feature cache management
- `scoring.py`: LLM-based scoring endpoints
- `solver.py`: Word finding algorithms
- `dataset.py`: Dataset generation and management

**Data Models** (`app/models/`):
- Pydantic models for request/response validation

### Key Data Flow

1. **Word Discovery**: `solver_service` finds words matching license plate patterns using subsequence matching
2. **Feature Extraction**: `feature_extraction` computes linguistic features (TF-IDF, n-grams, positional entropy, etc.)
3. **ML Prediction**: `prediction_service` uses trained Ridge regression to predict word impressiveness scores
4. **LLM Scoring**: `scoring_service` optionally uses language models for human-like evaluations

### Model Architecture

The system uses a **Ridge regression model** trained to mimic LLM judge panels. Features include:
- **Corpus Statistics**: TF-IDF, plate difficulty, word rarity
- **Linguistic Features**: Character n-grams, vowel/consonant ratios, word length
- **Positional Features**: Entropy of license plate letter positions within words
- **Frequency Features**: Word frequency from dictionary corpus

## Important File Locations

- **Trained Model**: `models/word_scoring_ridge_v3.joblib`
- **Feature Cache**: `cache/corpus_features.json` (auto-generated, large file)
- **Corpus Stats**: `cache/corpus_stats.json` (auto-generated)
- **Word Dictionary**: `data/words_with_freqs.json`
- **CLI Tool**: `run_scoring.py`

## Development Notes

### Cache Management
- Feature extraction is computationally expensive and cached automatically
- Cache files can be several hundred MB
- Use `/corpus/features/rebuild` API endpoint to regenerate cache
- Prediction service requires feature cache to be available on startup

### Model Training Workflow
1. Generate labeled dataset using LLM judges (`run_scoring.py dataset`)
2. Build feature cache for all word-plate pairs (expensive, one-time)
3. Train regression model (`app.services.regression_trainer`)
4. Deploy new model by replacing `models/word_scoring_ridge_v3.joblib`

### Performance Considerations
- First-time cache generation takes several minutes
- Feature cache enables fast predictions after initial build
- Memory usage can be high during feature extraction
- Use corpus statistics API endpoints for bulk operations

### Game Rules Implementation
Words must contain license plate letters **in correct order** but not necessarily consecutive:
- ✅ "ambulance" for "ABC" (A-m-B-u-l-a-n-C-e)  
- ❌ "cabin" for "ABC" (wrong order: C-A-B-i-n)

The scoring system evaluates cleverness, difficulty, satisfaction, and word quality to predict human-like impressiveness ratings.