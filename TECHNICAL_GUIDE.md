# PL8WRDS Technical Implementation Guide

## Model Building Pipeline

### Overview

The PL8WRDS scoring system requires two machine learning models that must be built offline before deployment:

1. **Information Content Model**: Calculates solution probabilities for all plate patterns
2. **Orthographic Complexity Model**: Analyzes n-gram patterns across the entire corpus

### Prerequisites

```bash
# Install required dependencies
pip install nltk scikit-learn numpy

# Download WordNet data
python -c "import nltk; nltk.download('wordnet')"
```

### Complete Model Build Process

Use the automated pipeline script:

```bash
python rebuild_all_models.py
```

This script will:
1. Load the WordNet-filtered corpus (103,949 words)
2. Build the Information Content Model (~2-3 minutes)
3. Build the Orthographic Complexity Model (~5-10 minutes) 
4. Save both models to the `models/` directory
5. Validate model integrity

### Manual Model Building

#### 1. Information Content Model

```python
# build_information_model.py
import json
from app.services.word_service import word_service
from app.services.solver_service import solver_service

def build_information_model():
    """Build complete information content model for all plate patterns."""
    
    print("🔄 Building Information Content Model...")
    
    # Generate all possible 3-letter plates (17,576 combinations)
    plates = generate_all_plates(length=3)
    
    model = {}
    total_plates = len(plates)
    
    for i, plate in enumerate(plates):
        if i % 1000 == 0:
            print(f"   Progress: {i}/{total_plates} ({i/total_plates*100:.1f}%)")
            
        # Find all solutions for this plate
        solutions = solver_service.solve_plate(plate)
        
        if solutions:
            solution_count = len(solutions)
            probability = 1.0 / solution_count
            
            model[plate] = {
                "solutions": solutions,
                "solution_count": solution_count,
                "probabilities": {word: probability for word in solutions}
            }
    
    # Save model
    with open("models/information_model.json", "w") as f:
        json.dump(model, f)
    
    print(f"✅ Information model built: {len(model)} plates, {sum(len(p['solutions']) for p in model.values())} word-plate pairs")

def generate_all_plates(length=3):
    """Generate all possible plate combinations."""
    import itertools
    return [''.join(combo) for combo in itertools.product('ABCDEFGHIJKLMNOPQRSTUVWXYZ', repeat=length)]
```

#### 2. Orthographic Complexity Model

```python
# build_orthographic_model.py
import json
from collections import defaultdict, Counter
from app.services.word_service import word_service

def build_orthographic_model():
    """Build n-gram probability model from entire corpus."""
    
    print("🔄 Building Orthographic Complexity Model...")
    
    trigram_counts = defaultdict(int)
    quartet_counts = defaultdict(int)
    total_trigrams = 0
    total_quartets = 0
    
    # Analyze all words in corpus
    for word in word_service.words.keys():
        word = word.lower()
        
        # Extract trigrams (3-letter sequences)
        for i in range(len(word) - 2):
            trigram = word[i:i+3]
            trigram_counts[trigram] += 1
            total_trigrams += 1
        
        # Extract quartets (4-letter sequences) 
        for i in range(len(word) - 3):
            quartet = word[i:i+4]
            quartet_counts[quartet] += 1
            total_quartets += 1
    
    # Convert counts to probabilities
    trigram_probs = {
        ngram: count / total_trigrams 
        for ngram, count in trigram_counts.items()
    }
    
    quartet_probs = {
        ngram: count / total_quartets
        for ngram, count in quartet_counts.items()
    }
    
    # Build complete model
    model = {
        "trigrams": trigram_probs,
        "quartets": quartet_probs,
        "stats": {
            "total_ngrams": total_trigrams + total_quartets,
            "unique_trigrams": len(trigram_probs),
            "unique_quartets": len(quartet_probs),
            "corpus_size": len(word_service.words)
        }
    }
    
    # Save model
    with open("models/orthographic_model.json", "w") as f:
        json.dump(model, f)
    
    print(f"✅ Orthographic model built:")
    print(f"   Trigrams: {len(trigram_probs):,}")
    print(f"   Quartets: {len(quartet_probs):,}")
    print(f"   Total n-grams analyzed: {total_trigrams + total_quartets:,}")
```

### Model Validation

After building models, validate their integrity:

```python
# validate_models.py
def validate_models():
    """Validate both models are working correctly."""
    
    from app.services.information_scorer import information_scorer
    from app.services.orthographic_scorer import orthographic_scorer
    
    test_cases = [
        ("pedagogue", "PDG"),
        ("faqir", "FQR"), 
        ("quetzal", "QZL")
    ]
    
    print("🧪 VALIDATING MODELS")
    print("-" * 50)
    
    for word, plate in test_cases:
        # Test information scorer
        try:
            info_result = information_scorer.score_word_plate(word, plate)
            info_score = info_result['information_score']
            print(f"✅ {word.upper():<12} Info: {info_score}")
        except Exception as e:
            print(f"❌ {word.upper():<12} Info: ERROR - {e}")
        
        # Test orthographic scorer
        try:
            ortho_result = orthographic_scorer.score_word(word)
            ortho_score = ortho_result['orthographic_score']  
            print(f"✅ {word.upper():<12} Ortho: {ortho_score}")
        except Exception as e:
            print(f"❌ {word.upper():<12} Ortho: ERROR - {e}")
    
    print("✅ Model validation complete!")
```

## Corpus Management

### Current Corpus: WordNet-Filtered Hermit Dave

The active corpus has been carefully curated for quality:

**Original Source**: Hermit Dave frequency lists
- Raw size: 1,083,468 words
- Quality issues: Typos, foreign words, OCR errors, single-frequency entries

**Filtering Process**: NLTK WordNet English lexicon
- Authoritative English word database
- Eliminates 90.4% of junk entries
- Final size: 103,949 verified words

### Corpus Replacement Process

To replace the corpus with a new frequency source:

1. **Prepare New Corpus**:
```python
# new_corpus_format.py
new_corpus = [
    {"word": "pedagogue", "frequency": 60},
    {"word": "faqir", "frequency": 12},
    # ... more entries
]

# Save in required format
with open("data/words_with_freqs.json", "w") as f:
    json.dump(new_corpus, f)
```

2. **Quality Validation**:
```bash
python -c "
import json
with open('data/words_with_freqs.json', 'r') as f:
    data = json.load(f)

print(f'Corpus size: {len(data):,}')
print(f'Sample entries: {data[:5]}')

# Check for proper names (should be minimal)
proper_names = [item for item in data if item['word'][0].isupper()]
print(f'Proper names: {len(proper_names)} ({len(proper_names)/len(data)*100:.1f}%)')
"
```

3. **Rebuild All Models**:
```bash
python rebuild_all_models.py
```

4. **Test System**:
```bash
python test_3d_system.py
```

## Deployment Guide

### Development Deployment

```bash
# 1. Clone repository
git clone <repository-url>
cd PL8WRDS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build models (if not already built)
python rebuild_all_models.py

# 4. Start development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Deployment

#### Docker Deployment

```bash
# 1. Build image
docker build -t pl8wrds:latest .

# 2. Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d

# 3. Verify deployment
curl http://localhost/health
```

#### Manual Production Setup

```bash
# 1. Setup virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install production dependencies
pip install -r requirements-prod.txt

# 3. Build models
python rebuild_all_models.py

# 4. Start production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Configuration

Create environment-specific configuration files:

**.env.production**:
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://yourdomain.com"]
MAX_REQUEST_SIZE=1048576
REQUEST_TIMEOUT=30
WORKER_PROCESSES=4
```

**.env.development**:
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
CORS_ORIGINS=["*"]
MAX_REQUEST_SIZE=1048576
REQUEST_TIMEOUT=60
```

## Performance Optimization

### Model Loading Optimization

The Information Content Model (655MB) can cause startup delays. Optimize with lazy loading:

```python
# app/services/information_scorer.py
class InformationScorer:
    def __init__(self):
        self._model = None  # Lazy load
        
    @property
    def model(self):
        if self._model is None:
            print("Loading information model...")
            with open("models/information_model.json") as f:
                self._model = json.load(f)
        return self._model
```

### Memory Optimization

For memory-constrained deployments:

1. **Model Compression**:
```python
# Reduce precision for probability values
probabilities = {k: round(v, 6) for k, v in probabilities.items()}
```

2. **Partial Model Loading**:
```python
# Load only common plates (3-letter patterns)
common_plates = ["THE", "AND", "FOR", ...]  # Most frequent patterns
model = {plate: data for plate, data in full_model.items() if plate in common_plates}
```

### Response Time Optimization

**Parallel Scoring**: All three scorers run concurrently:

```python
import asyncio

async def score_ensemble(word: str, plate: str) -> dict:
    # Run all scorers in parallel
    tasks = [
        frequency_scorer.score_word(word),
        information_scorer.score_word_plate(word, plate),
        orthographic_scorer.score_word(word)
    ]
    
    vocab_result, info_result, ortho_result = await asyncio.gather(*tasks)
    
    return combine_scores(vocab_result, info_result, ortho_result)
```

## Monitoring and Maintenance

### Health Monitoring

Implement comprehensive health checks:

```python
# app/monitoring/health.py
async def detailed_health_check():
    """Comprehensive system health verification."""
    
    checks = {
        "corpus_loaded": len(word_service.words) > 100000,
        "information_model": information_scorer.model is not None,
        "orthographic_model": orthographic_scorer.model is not None,
        "solver_functional": len(solver_service.solve_plate("PDG")) > 0,
        "memory_usage": psutil.virtual_memory().percent < 90,
        "disk_space": psutil.disk_usage("/").percent < 90
    }
    
    return {
        "healthy": all(checks.values()),
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Performance Monitoring

Track key metrics:

```python
# app/monitoring/metrics.py
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('pl8wrds_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('pl8wrds_request_duration_seconds', 'Request latency')
SCORING_LATENCY = Histogram('pl8wrds_scoring_duration_seconds', 'Scoring computation time')

@REQUEST_LATENCY.time()
async def score_with_monitoring(word: str, plate: str):
    start_time = time.time()
    result = await score_ensemble(word, plate)
    SCORING_LATENCY.observe(time.time() - start_time)
    return result
```

### Maintenance Tasks

#### Weekly Maintenance
```bash
#!/bin/bash
# maintenance.sh

echo "🔄 Weekly PL8WRDS Maintenance"

# 1. Check disk space
df -h

# 2. Verify model integrity
python -c "
from app.services.information_scorer import information_scorer
from app.services.orthographic_scorer import orthographic_scorer
print('Models loaded successfully')
"

# 3. Run system health check
curl -s http://localhost:8000/health | jq

# 4. Check log files for errors
grep ERROR /var/log/pl8wrds/*.log | tail -20

echo "✅ Maintenance complete"
```

#### Model Update Process
```bash
# When corpus changes or improvements are made:

# 1. Backup current models
cp -r models/ models_backup_$(date +%Y%m%d)/

# 2. Rebuild models with new data
python rebuild_all_models.py

# 3. Test new models
python test_3d_system.py

# 4. Deploy to production (zero-downtime)
# - Rolling deployment with health checks
# - Gradual traffic migration
# - Rollback capability
```

## Troubleshooting Guide

### Common Issues

#### 1. Model Loading Failures
**Symptoms**: 500 errors on scoring endpoints
**Diagnosis**:
```bash
ls -la models/
python -c "import json; json.load(open('models/information_model.json'))"
```
**Solution**: Rebuild models with `python rebuild_all_models.py`

#### 2. Memory Exhaustion
**Symptoms**: Out of memory errors, slow responses
**Diagnosis**: Check memory usage with `htop` or `ps aux`
**Solution**: 
- Increase server memory
- Implement model compression
- Add memory limits to Docker containers

#### 3. Corpus Issues
**Symptoms**: Words not found, unexpected scores
**Diagnosis**:
```bash
python -c "
from app.services.word_service import word_service
print(f'Corpus size: {len(word_service.words)}')
print(f'Sample words: {list(word_service.words.keys())[:10]}')
"
```
**Solution**: Verify corpus integrity and rebuild if necessary

#### 4. Performance Degradation  
**Symptoms**: High response times, timeouts
**Diagnosis**: Check logs for bottlenecks, monitor CPU/memory
**Solution**:
- Scale horizontally (add more instances)
- Optimize model loading
- Implement caching where appropriate

### Debugging Tools

```python
# debug_scoring.py
def debug_word_scoring(word: str, plate: str):
    """Detailed debugging of scoring process."""
    
    print(f"🔍 DEBUGGING: {word.upper()} / {plate}")
    
    # 1. Check word exists in corpus
    if word not in word_service.words:
        print(f"❌ Word '{word}' not in corpus")
        return
    
    freq = word_service.get_frequency(word)
    print(f"✅ Word frequency: {freq:,}")
    
    # 2. Check plate solutions
    solutions = solver_service.solve_plate(plate)
    print(f"✅ Plate solutions: {len(solutions)} words")
    print(f"   Sample: {solutions[:5]}")
    
    # 3. Test each scorer individually
    try:
        vocab_result = frequency_scorer.score_word(word)
        print(f"✅ Vocabulary score: {vocab_result['scores']['combined']}")
    except Exception as e:
        print(f"❌ Vocabulary scorer error: {e}")
    
    try:
        info_result = information_scorer.score_word_plate(word, plate)
        print(f"✅ Information score: {info_result['information_score']}")
    except Exception as e:
        print(f"❌ Information scorer error: {e}")
        
    try:
        ortho_result = orthographic_scorer.score_word(word)
        print(f"✅ Orthographic score: {ortho_result['orthographic_score']}")
    except Exception as e:
        print(f"❌ Orthographic scorer error: {e}")
```

---

*Complete technical implementation guide for PL8WRDS*
*Covers model building, deployment, monitoring, and maintenance*
