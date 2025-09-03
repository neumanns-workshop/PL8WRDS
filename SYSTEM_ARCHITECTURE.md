# PL8WRDS System Architecture

## Overview

PL8WRDS is a FastAPI-based word game scoring system that evaluates the impressiveness of word solutions for license plate patterns using a sophisticated 3-dimensional scoring approach.

## Architecture Pattern

The system follows **Clean Architecture** principles with **Domain-Driven Design (DDD)**:

```
┌─────────────────────────────────────────┐
│             Presentation Layer          │
│  (FastAPI Routes, HTTP Handlers)        │
├─────────────────────────────────────────┤
│            Application Layer            │
│  (Use Cases, Services, Orchestration)   │
├─────────────────────────────────────────┤
│              Domain Layer               │
│  (Entities, Value Objects, Rules)       │
├─────────────────────────────────────────┤
│           Infrastructure Layer          │
│  (Repositories, External Services)      │
└─────────────────────────────────────────┘
```

## Directory Structure

```
app/
├── main.py                    # FastAPI application entry point
├── routers/                   # HTTP route handlers
│   ├── prediction.py         # Scoring endpoints
│   ├── solver.py             # Word solving endpoints
│   ├── corpus.py             # Corpus statistics
│   ├── dataset.py            # System status
│   └── monitoring.py         # Health checks
├── services/                  # Business logic services
│   ├── frequency_scorer.py   # Vocabulary sophistication
│   ├── information_scorer.py # Information theory scoring
│   ├── orthographic_scorer.py# N-gram complexity scoring
│   ├── prediction_service.py # Ensemble coordination
│   ├── solver_service.py     # Word pattern matching
│   └── word_service.py       # Corpus management
├── domain/                    # Domain entities
│   ├── entities.py           # Core business objects
│   └── value_objects.py      # Immutable domain values
├── application/              # Application services
│   ├── interfaces.py         # Abstract interfaces
│   ├── services.py          # Application services
│   └── use_cases.py         # Business use cases
├── infrastructure/          # External integrations
│   ├── repositories.py      # Data access
│   └── external_services.py # Third-party APIs
├── core/                   # Configuration
│   ├── config.py          # Settings management
│   └── container.py       # Dependency injection
└── monitoring/            # Observability
    ├── logger.py         # Structured logging
    ├── metrics.py        # Prometheus metrics
    └── health.py         # Health checks
```

## Core Components

### 1. Scoring System Architecture

#### 3-Dimensional Scoring Model

```mermaid
graph TB
    W[Word + Plate] --> F[Frequency Scorer]
    W --> I[Information Scorer]  
    W --> O[Orthographic Scorer]
    
    F --> |Vocabulary Score| E[Ensemble Combiner]
    I --> |Information Score| E
    O --> |Orthographic Score| E
    
    E --> |Weighted Average| R[Final Score 0-100]
    
    subgraph "Frequency Scorer"
        F1[Global Corpus Frequency]
        F2[Percentile Ranking]
        F3[Z-Score Analysis]
    end
    
    subgraph "Information Scorer"
        I1[Shannon Information Content]
        I2[-log₂(P(word|plate))]
        I3[Solution Probability]
    end
    
    subgraph "Orthographic Scorer" 
        O1[N-gram Decomposition]
        O2[Pattern Probabilities]
        O3[Cognitive Complexity]
    end
```

#### Scoring Pipeline

```python
# Simplified scoring flow
async def score_word(word: str, plate: str, weights: dict) -> dict:
    # 1. Parallel scoring across dimensions
    vocab_score = await frequency_scorer.score_word(word)
    info_score = await information_scorer.score_word_plate(word, plate)
    ortho_score = await orthographic_scorer.score_word(word)
    
    # 2. Weighted ensemble combination
    ensemble_score = calculate_weighted_average([
        (vocab_score['combined'], weights['vocabulary']),
        (info_score['information_score'], weights['information']),
        (ortho_score['orthographic_score'], weights['orthographic'])
    ])
    
    return {
        "ensemble_score": ensemble_score,
        "individual_scores": {...},
        "interpretation": generate_interpretation(ensemble_score)
    }
```

### 2. Data Architecture

#### Corpus Management

**Primary Corpus**: WordNet-Filtered Hermit Dave
- **Raw Source**: Hermit Dave frequency lists (1.08M words)
- **Filter**: NLTK WordNet English lexicon
- **Result**: 103,949 verified English words (90.4% reduction)
- **Quality**: Eliminates typos, foreign words, nonsense entries

**Corpus Structure**:
```json
[
  {
    "word": "pedagogue",
    "frequency": 60
  },
  {
    "word": "faqir", 
    "frequency": 12
  }
]
```

#### Model Storage

**Information Content Model** (`models/information_model.json`):
```json
{
  "PDG": {
    "solutions": ["pedagogue", "pudging", ...],
    "solution_count": 15,
    "probabilities": {
      "pedagogue": 0.0667,
      "pudging": 0.0667,
      ...
    }
  }
}
```

**Orthographic Model** (`models/orthographic_model.json`):
```json
{
  "trigrams": {
    "ped": 0.0023,
    "eda": 0.0012,
    ...
  },
  "quartets": {
    "peda": 0.0008,
    "edag": 0.0003,
    ...
  },
  "stats": {
    "total_ngrams": 486532,
    "unique_trigrams": 12847,
    "unique_quartets": 31242
  }
}
```

### 3. Service Architecture

#### Word Service (Corpus Management)
```python
class WordService:
    """Central corpus management and word validation."""
    
    def __init__(self):
        self.words: Dict[str, int]  # word -> frequency mapping
        self._load_corpus()
        
    def get_frequency(self, word: str) -> int
    def is_valid_word(self, word: str) -> bool
    def get_corpus_stats() -> dict
```

#### Solver Service (Pattern Matching)
```python
class SolverService:
    """License plate pattern solving."""
    
    async def solve_plate(self, plate: str) -> List[str]:
        """Find all words matching plate pattern."""
        # Efficient pattern matching algorithm
        # Returns sorted list of solutions
```

#### Prediction Service (Ensemble Coordination)
```python
class PredictionService:
    """Orchestrates the 3D scoring system."""
    
    async def predict_ensemble(
        self, 
        word: str, 
        plate: str, 
        weights: dict
    ) -> dict:
        """Coordinate all scoring dimensions."""
```

## Deployment Architecture

### Development Setup
```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
```

### Production Deployment
```yaml
# docker-compose.prod.yml  
services:
  api:
    image: pl8wrds:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf
  
  monitoring:
    image: prometheus:latest
    ports:
      - "9090:9090"
```

## Performance Architecture

### Caching Strategy
- **Corpus**: Loaded once at startup, kept in memory
- **Models**: Lazy-loaded on first use, cached indefinitely  
- **Scoring Results**: No caching (real-time computation)
- **Solution Sets**: No caching (lightweight computation)

### Scaling Considerations
- **Horizontal Scaling**: Stateless API design allows multiple replicas
- **Memory Requirements**: 2GB+ per instance (models + corpus)
- **CPU Intensive**: N-gram analysis and ensemble computation
- **I/O Minimal**: All data pre-loaded, minimal file system access

### Bottlenecks
1. **Model Loading**: 655MB information model load time
2. **N-gram Computation**: Complex orthographic analysis
3. **Ensemble Coordination**: Multiple scorer coordination
4. **Memory Usage**: Large model files in memory

## Monitoring Architecture

### Health Checks
```python
@router.get("/health")
async def health_check():
    """System health verification."""
    checks = {
        "corpus": len(word_service.words) > 100000,
        "models": information_model.loaded and orthographic_model.loaded,
        "api": True  # If we respond, API is up
    }
    return {"healthy": all(checks.values()), "checks": checks}
```

### Metrics Collection
- **Request latency**: P50, P95, P99 response times
- **Error rates**: 4xx, 5xx error percentages
- **Model performance**: Scoring computation times
- **Resource usage**: Memory, CPU utilization

### Logging Strategy
```python
import structlog

logger = structlog.get_logger()

# Structured logging for analysis
logger.info(
    "word_scored",
    word=word,
    plate=plate,
    ensemble_score=score,
    latency_ms=duration,
    user_id=user_id
)
```

## Security Architecture

### Input Validation
- **Plate patterns**: 3-8 characters, letters only
- **Word inputs**: ASCII letters, length limits
- **Weight parameters**: Numeric validation, range checking
- **Request size**: Body size limits, timeout protection

### API Security
- **CORS**: Configured for known domains
- **Rate limiting**: To be implemented
- **Input sanitization**: All user inputs validated
- **Error handling**: No sensitive data in error responses

## Testing Architecture

### Test Structure
```
tests/
├── unit/                  # Individual component tests
│   ├── domain/           # Domain logic tests
│   └── services/         # Service layer tests
├── integration/          # Component integration tests
├── api/                  # API endpoint tests
├── e2e/                  # End-to-end workflow tests
└── performance/          # Load and performance tests
```

### Test Types
- **Unit Tests**: Individual scorer components
- **Integration Tests**: Service interactions
- **API Tests**: HTTP endpoint validation
- **E2E Tests**: Complete workflow testing
- **Performance Tests**: Load testing, latency measurement

## Data Flow Architecture

### Request Processing Flow
```
1. HTTP Request → Router
2. Router → Validation  
3. Validation → Service Layer
4. Service → Multiple Scorers (parallel)
5. Scorers → Model Lookups
6. Results → Ensemble Combiner
7. Combiner → Response Formatter
8. Formatter → HTTP Response
```

### Model Training Flow (Offline)
```
1. Corpus Loading → Word Service
2. Pattern Generation → All Possible Plates
3. Solution Finding → Solver Service  
4. Probability Calculation → Information Model
5. N-gram Analysis → Orthographic Model
6. Model Serialization → JSON Files
7. Model Deployment → Production System
```

---

*System designed for high performance, reliability, and maintainability*
*Architecture supports horizontal scaling and observability*
