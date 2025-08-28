# License Plate Word Game - Python Implementation Plan

## Project Overview
A word game where players create words using license plate letters in order (non-consecutive). Scoring based on information-theoretic surprisal - how unexpected is this word given the plate combination?

## Core Game Mechanics
- Input: License plate (3-4 letters, e.g., "MMS")
- Challenge: Find words where plate letters appear in order
- Valid: "mathematics" (M-M-S appear in sequence)
- Invalid: "stems" (S-T-E-M-S has M after S)
- Scoring: Based on word surprisal/unexpectedness

## Technical Architecture

### Phase 1: Data Generation & Analysis
**Objective**: Create ground truth dataset for model training

#### 1.1 Exhaustive Word Generation
```python
# Generate all valid words for each possible plate combination
def generate_valid_words(plate_letters, dictionary):
    """Find all dictionary words matching letter ordering constraint"""
    # Implementation: dynamic programming or regex matching
    
# Target: Complete mapping of plate -> valid_words
# Example: "ABC" -> ["about", "able", "cabinet", ...]
```

#### 1.2 Surprisal Calculation
```python
def calculate_surprisal(word, plate, word_counts):
    """Calculate -log2(P(word|plate)) for ground truth scoring"""
    # P(word|plate) = count(word_for_plate) / total_words_for_plate
    
# Output: Exact surprisal scores for every plate/word combination
```

#### 1.3 Feature Engineering
```python
class FeatureExtractor:
    def extract_features(self, plate, word):
        """Extract generalizable features for model training"""
        return {
            # Plate features
            'plate_entropy': ...,
            'letter_frequencies': ...,
            'vowel_consonant_ratio': ...,
            
            # Word features  
            'word_length': len(word),
            'char_ngrams': ...,
            'phonetic_features': ...,
            'morphological_patterns': ...,
            
            # Alignment features
            'edit_distance': ...,
            'letter_usage_efficiency': ...,
            'ordering_satisfaction': ...
        }
```

### Phase 2: Model Training
**Objective**: Learn lightweight regression model for surprisal prediction

#### 2.1 Dataset Preparation
```python
# Convert exhaustive data to training examples
X = []  # Feature vectors
y = []  # Ground truth surprisal scores

for plate in all_plates:
    for word in valid_words[plate]:
        features = feature_extractor.extract_features(plate, word)
        surprisal = ground_truth_surprisal[(plate, word)]
        X.append(features)
        y.append(surprisal)
```

#### 2.2 Model Architecture Options
```python
# Option 1: Feedforward Neural Network
from sklearn.neural_network import MLPRegressor
model = MLPRegressor(hidden_layer_sizes=(128, 64), max_iter=1000)

# Option 2: Gradient Boosting (likely faster inference)
from xgboost import XGBRegressor  
model = XGBRegressor(n_estimators=100, max_depth=6)

# Option 3: Linear regression with polynomial features
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge
```

#### 2.3 Model Validation
```python
# Test generalization to unseen plates and words
def validate_model(model, test_plates, test_words):
    """Ensure model handles novel combinations gracefully"""
    # Cross-validation on plates
    # Out-of-vocabulary word testing
    # Surprisal correlation with human judgments
```

### Phase 3: Game Engine
**Objective**: Core game logic and scoring system

#### 3.1 Word Validation
```python
class GameEngine:
    def is_valid_word(self, plate_letters, word):
        """Check if word satisfies letter ordering constraint"""
        plate_idx = 0
        for char in word.lower():
            if plate_idx < len(plate_letters) and char == plate_letters[plate_idx]:
                plate_idx += 1
        return plate_idx == len(plate_letters)
    
    def is_real_word(self, word, dictionary):
        """Verify word exists in dictionary"""
        return word.lower() in dictionary
```

#### 3.2 Scoring System
```python
class ScoringSystem:
    def __init__(self, surprisal_model, feature_extractor):
        self.model = surprisal_model
        self.features = feature_extractor
    
    def score_word(self, plate, word):
        """Generate THPS-style score breakdown"""
        features = self.features.extract_features(plate, word)
        base_surprisal = self.model.predict([features])[0]
        
        return {
            'base_score': int(base_surprisal * 100),
            'bonuses': self.calculate_bonuses(plate, word),
            'multipliers': self.calculate_multipliers(),
            'total': self.calculate_total()
        }
    
    def calculate_bonuses(self, plate, word):
        """THPS-style bonus categories"""
        bonuses = {}
        if len(word) > 10:
            bonuses['Length Legend'] = 200
        if self.uses_all_letters(plate, word):
            bonuses['Full Plate Mastery'] = 300
        if self.is_rare_word(word):
            bonuses['Dictionary Deep Cut'] = 150
        return bonuses
```

### Phase 4: Web Interface
**Objective**: Browser-based game with real-time scoring

#### 4.1 Model Deployment
```python
# Convert trained model to JavaScript/WASM for browser
import onnx
import skl2onnx

# Export to ONNX format for web deployment
onnx_model = skl2onnx.convert_sklearn(trained_model, initial_types)
```

#### 4.2 Game Interface (Flask/FastAPI backend)
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/validate_word', methods=['POST'])
def validate_word():
    plate = request.json['plate']
    word = request.json['word']
    
    if game_engine.is_valid_word(plate, word):
        score_breakdown = scoring_system.score_word(plate, word)
        return jsonify({'valid': True, 'score': score_breakdown})
    else:
        return jsonify({'valid': False})

@app.route('/generate_plate', methods=['GET'])
def generate_plate():
    """Generate random license plate for gameplay"""
    return jsonify({'plate': random_plate_generator()})
```

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Dictionary loading and preprocessing
- [ ] Exhaustive word generation for 3-letter plates
- [ ] Ground truth surprisal calculation
- [ ] Basic feature extraction implementation

### Phase 2: Model Development (Weeks 3-4)  
- [ ] Feature engineering refinement
- [ ] Model training and validation
- [ ] Hyperparameter tuning
- [ ] Performance benchmarking

### Phase 3: Game Logic (Week 5)
- [ ] Core game engine implementation
- [ ] Scoring system with bonuses/multipliers
- [ ] Unit tests for game mechanics

### Phase 4: Web Deployment (Week 6)
- [ ] Model export for web inference
- [ ] REST API development
- [ ] Basic web interface
- [ ] Integration testing

## Key Dependencies
```python
# Data processing
pandas
numpy
nltk  # For dictionary and linguistic features

# Machine learning
scikit-learn
xgboost
# OR pytorch for neural networks

# Feature extraction
phonetics  # For soundex/metaphone
textdistance  # For edit distance metrics

# Web deployment
flask  # Backend API
onnx  # Model export
requests  # HTTP client

# Utilities
tqdm  # Progress bars
joblib  # Parallel processing
```

## Success Metrics
- **Model Performance**: R² > 0.8 on surprisal prediction
- **Response Time**: < 50ms for word scoring
- **Coverage**: Handle 95%+ of dictionary words
- **Generalization**: Reasonable scores for unseen plate/word combinations
- **User Experience**: Intuitive scoring that rewards discovery

## Future Enhancements
- Multiplayer competitions
- Daily challenge plates
- Photo recognition of real license plates
- Advanced difficulty modes (4+ letters, phrases)
- Social features (sharing interesting discoveries)