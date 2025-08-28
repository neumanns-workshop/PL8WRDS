# PL8WRDS: License Plate Word Game API

A sophisticated word game API that finds words matching license plate letter combinations and scores them using machine learning models trained to mimic human-like LLM judge evaluations. The system combines dictionary lookup, feature extraction, and trained regression models to predict word impressiveness scores.

## Project Overview

PL8WRDS implements the classic license plate word game where players find words containing license plate letters **in the correct order** (but not necessarily consecutive). The system provides:

- **Word Discovery**: Find words that match license plate patterns using various algorithms
- **ML-Based Scoring**: Predict word impressiveness using Ridge regression models trained to mimic LLM judge panels
- **Feature-Rich Analysis**: Extract linguistic and phonetic features for comprehensive word analysis
- **Corpus Statistics**: Pre-computed statistics across all possible 3-letter combinations
- **FastAPI Interface**: Modern REST API with automatic documentation

## Setup and Installation

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### 1. Clone and Setup Environment

```bash
git clone https://github.com/your-username/PL8WRDS.git
cd PL8WRDS

# Create virtual environment
python -m venv pl8wrds-env
source pl8wrds-env/bin/activate  # On Windows: pl8wrds-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Data and Models

```bash
# The application will automatically initialize required data on first startup
# This includes loading the trained regression model: word_scoring_ridge_v3.joblib
```

### 3. Start the Application

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --port 8000

# The API will be available at:
# - API: http://127.0.0.1:8000
# - Interactive Docs: http://127.0.0.1:8000/docs
# - Alternative Docs: http://127.0.0.1:8000/redoc
```

## Core API Endpoints Guide

### Prediction (Primary Feature)

The main functionality - predict word impressiveness scores using the trained ML model:

```bash
# Score a single word for a license plate
curl -X POST "http://127.0.0.1:8000/predict/score" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "ambulance",
    "plate": "ABC"
  }'

# Response:
{
  "word": "ambulance",
  "plate": "ABC", 
  "predicted_score": 85.3,
  "model_version": "ridge_v3"
}
```

**Health Check:**
```bash
curl http://127.0.0.1:8000/predict/health
```

**Feature Interpretability:**
```bash
# Get the most important features from the trained model
curl http://127.0.0.1:8000/predict/feature-importance?top_k=15

# Explain a specific prediction - see which features contributed most
curl -X POST "http://127.0.0.1:8000/predict/explain" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "ambulance",
    "plate": "ABC"
  }' | jq '.explanation.top_contributing_features[:5]'
```

### Data & Features

These endpoints provide corpus statistics and feature extraction. **Warning: First-time generation is computationally expensive and may take several minutes.**

```bash
# Get corpus statistics (generates cache on first run)
curl http://127.0.0.1:8000/corpus/stats

# Get corpus summary (lighter version)
curl http://127.0.0.1:8000/corpus/stats/summary

# Get comprehensive features (very large file, generates cache on first run)
curl http://127.0.0.1:8000/corpus/features

# Check cache status
curl http://127.0.0.1:8000/corpus/stats/cache-info
curl http://127.0.0.1:8000/corpus/features/cache-info
```

### LLM Scoring (Optional)

If you have Ollama installed and running, you can use LLM-based scoring:

```bash
# Check scoring system status
curl http://127.0.0.1:8000/scoring/status

# Score a single word with LLMs (requires Ollama)
curl -X POST "http://127.0.0.1:8000/scoring/score-word" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "ambulance",
    "combination": "abc", 
    "models": ["granite3.3:8b"]
  }'
```

## Model Training & Retraining Guide

This section explains how to retrain the regression model with new data:

### 1. (Optional) Generate New Labeled Dataset

Use the LLM scoring system to create a labeled dataset where multiple language models act as judges to score words:

```bash
# First, ensure Ollama is running and models are available
ollama serve

# Download required models
ollama pull granite3.3:8b
ollama pull mistral:7b
ollama pull deepseek-r1:8b

# Generate dataset using the CLI tool
python run_scoring.py dataset \
  --plates 100 \
  --words 5 \
  --models granite mistral deepseek \
  --output new_dataset.json \
  --sampling frequency_weighted
```

### 2. Generate Feature Cache

**Important**: This is computationally expensive and should be run when you have sufficient time and resources:

```bash
# Trigger feature cache generation via API
curl -X POST http://127.0.0.1:8000/corpus/features/rebuild
```

Or let it generate automatically when needed.

### 3. Train New Model

```bash
# Run the training script to produce a new model
python -m app.services.regression_trainer

# This will:
# - Load the LLM-judged labeled dataset 
# - Load the feature cache (corpus_features.json) 
# - Train a new Ridge regression model to predict LLM judge scores
# - Save the model as word_scoring_ridge_v3.joblib
# - Evaluate performance and display metrics comparing predicted vs LLM scores
```

### 4. Deploy New Model

The application automatically loads `models/word_scoring_ridge_v3.joblib` on startup. Replace this file with your newly trained model and restart the application.

## Project Structure Overview

```
PL8WRDS/
├── app/                          # FastAPI application
│   ├── main.py                   # Application entry point
│   ├── models/                   # Pydantic models
│   │   ├── scoring.py           # LLM scoring models
│   │   └── ...
│   ├── routers/                  # API route handlers
│   │   ├── prediction.py        # ML prediction endpoints  
│   │   ├── corpus.py            # Corpus statistics & features
│   │   ├── scoring.py           # LLM scoring endpoints
│   │   └── ...
│   └── services/                 # Business logic
│       ├── prediction_service.py # ML prediction service
│       ├── feature_extraction.py # Feature computation
│       ├── regression_trainer.py # Model training
│       └── ...
├── models/                       # Trained ML models
│   └── word_scoring_ridge_v3.joblib
├── cache/                        # Generated cache files
│   ├── corpus_stats.json        # Corpus statistics cache  
│   ├── corpus_features.json     # Feature extraction cache
│   └── ...
├── data/                         # Base datasets
│   └── words_with_freqs.json    # Word frequency data
├── run_scoring.py               # CLI tool for dataset generation
└── requirements.txt             # Python dependencies
```

### Key Directories & Responsibilities

- **`app/routers/`**: API endpoint definitions and request handling
- **`app/services/`**: Core business logic, feature extraction, ML operations  
- **`app/models/`**: Pydantic models for request/response validation
- **`models/`**: Trained machine learning model files
- **`cache/`**: Generated cache files (can be large, auto-created)
- **`data/`**: Base datasets and dictionaries

## How the Game Works

### Game Rules
Players find words containing license plate letters **in the correct order** (but not necessarily consecutive).

**✅ Valid Examples for plate "CAR":**
- "car" - Direct match (C-A-R)
- "card" - C-A-R-d (letters in order)  
- "scar" - s-C-A-R (letters in order)
- "careful" - C-A-R-eful (letters in order, gaps allowed)

**❌ Invalid Examples for plate "CAR":**
- "arc" - Wrong order (A-R-C, not C-A-R)
- "race" - Wrong order (R-A-C, not C-A-R)

### ML Scoring System

The trained Ridge regression model is designed to mimic the aggregate scoring behavior of a panel of LLM judges. It predicts word impressiveness scores (0-100) by learning from human-like evaluations provided by multiple language models (granite3.3:8b, mistral:7b, deepseek-r1:8b, etc.) that assess words based on:

- **Cleverness**: How creative and non-obvious is the word choice?
- **Difficulty**: How hard would this be for a human to spot?
- **Satisfaction**: How rewarding does this discovery feel?
- **Word Quality**: Is this an elegant, well-known word?

The regression model extracts linguistic features from words and learns to predict these LLM-judged scores:

- **Word characteristics**: Length, frequency, syllable count
- **Pattern matching**: How well the word fits the license plate
- **Linguistic features**: Phonetic properties, morphology  
- **Context features**: Combination difficulty, word uniqueness

### Example Predictions

Real predictions from the system:
- **"ambulance" for "ABC"**: 85.3/100 (strong medical term, good pattern)
- **"careful" for "CAR"**: 78.9/100 (common word, clear pattern)  
- **"syzygy" for "SGY"**: 92.1/100 (rare astronomy term, perfect match)

## Advanced Usage

### Batch Processing

Use the CLI tool for bulk operations:

```bash
# Generate random word dataset
python run_scoring.py random-words \
  --target 1000 \
  --models granite mistral \
  --output random_dataset.json

# Check system status
python run_scoring.py check
```

### Cache Management

Control cache files via API:

```bash
# Clear corpus statistics cache
curl -X DELETE http://127.0.0.1:8000/corpus/stats/cache

# Force rebuild corpus features
curl -X POST http://127.0.0.1:8000/corpus/features/rebuild

# Check cache information
curl http://127.0.0.1:8000/corpus/stats/cache-info
```

### API Health Monitoring

```bash
# Check prediction service health
curl http://127.0.0.1:8000/predict/health

# Check corpus service health  
curl http://127.0.0.1:8000/corpus/health

# Check LLM scoring status
curl http://127.0.0.1:8000/scoring/status
```

### Model Interpretability

Understand how the ML model makes predictions:

```bash
# View the most important features globally
curl "http://127.0.0.1:8000/predict/feature-importance?top_k=20"

# Explain a specific prediction 
curl -X POST "http://127.0.0.1:8000/predict/explain" \
  -H "Content-Type: application/json" \
  -d '{"word": "syzygy", "plate": "SGY"}'
```

The `/predict/explain` endpoint shows:
- **Feature contributions**: How much each linguistic feature contributed to the final score
- **Verification**: Mathematical proof that contributions sum to the predicted score
- **Active features**: Which features were non-zero for this specific word-plate pair

> **💡 Game Feature Idea**: The explanation endpoint would make an excellent "Rubric" feature for players! After they guess a word for a license plate, show them not just their score, but *why* they got that score - was it the word's rarity? Length? Phonetic properties? This educational feedback could help players understand what makes a great PL8WRDS discovery and improve their gameplay strategy. It's also a perfect example of **AI explainability in action** - making machine learning predictions transparent and understandable to users!

## Development and Extension

### Adding New Features

1. **New endpoints**: Add route handlers in `app/routers/`
2. **Business logic**: Implement services in `app/services/`
3. **Data models**: Define Pydantic models in `app/models/`

### Model Improvements

1. **Feature engineering**: Modify `app/services/feature_extraction.py`
2. **Training pipeline**: Update `app/services/regression_trainer.py`
3. **Model architecture**: Experiment with different sklearn models

### Testing

```bash
# Run the prediction service health check
curl http://127.0.0.1:8000/predict/health

# Test with sample predictions
curl -X POST "http://127.0.0.1:8000/predict/score" \
  -H "Content-Type: application/json" \
  -d '{"word": "test", "plate": "TST"}'
```

## Troubleshooting

### Model Loading Issues
- **Error**: "Model not loaded" → Ensure `models/word_scoring_ridge_v3.joblib` exists
- **Error**: "Prediction service not initialized" → Check application startup logs

### Cache Generation Issues  
- **Slow performance**: Cache generation is CPU-intensive, be patient on first run
- **Memory errors**: Reduce batch sizes or clear existing caches
- **Disk space**: Feature cache can be several hundred MB

### API Errors
- **503 Service Unavailable**: Service initialization failed, check logs
- **500 Internal Server Error**: Check application logs for specific error details
- **404 Not Found**: Verify endpoint paths match API documentation

### Performance Optimization
- **Use caching**: Let the system cache corpus statistics and features
- **Monitor memory**: Feature extraction can be memory-intensive
- **Check disk space**: Cache files can grow large over time

## License

MIT License - see LICENSE file for details.