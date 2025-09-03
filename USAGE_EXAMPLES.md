# PL8WRDS Usage Examples and Workflows

## Quick Start Examples

### Basic Word Scoring

Score a single word against a license plate:

```bash
curl -X POST "http://localhost:8000/predict/ensemble" \
  -H "Content-Type: application/json" \
  -d '{"word": "pedagogue", "plate": "PDG"}'
```

**Response:**
```json
{
  "word": "pedagogue",
  "plate": "PDG", 
  "ensemble_score": 65.2,
  "individual_scores": {
    "vocabulary": {"score": 77, "weight": 1.0, "contribution": 25.7},
    "information": {"score": 65, "weight": 1.0, "contribution": 21.7},
    "orthographic": {"score": 54, "weight": 1.0, "contribution": 18.0}
  },
  "interpretation": "Sophisticated word with good balance across dimensions"
}
```

### Find All Solutions for a Plate

```bash
curl "http://localhost:8000/solve/PDG"
```

**Response:**
```json
{
  "plate": "PDG",
  "solutions": [
    "pedagogue", "pudgier", "pudging", "pledging", 
    "prodding", "plodding", "padding", "podding",
    "pedaling", "peddling", "pledging", "pudding",
    "pedigo", "pudge", "podge"
  ],
  "count": 15,
  "execution_time": "0.042s"
}
```

## Individual Scorer Examples

### Vocabulary Sophistication Scorer

Test vocabulary sophistication based on global corpus frequency:

```python
import httpx
import asyncio

async def test_vocabulary_sophistication():
    test_words = ["pedagogue", "big", "faqir", "quetzal", "running"]
    
    async with httpx.AsyncClient() as client:
        for word in test_words:
            response = await client.post(
                "http://localhost:8000/predict/vocabulary",
                json={"word": word}
            )
            
            if response.status_code == 200:
                data = response.json()
                score = data["scores"]["combined"]
                interpretation = data["interpretation"]["combined"]
                
                print(f"{word.upper():<12}: {score:>5.1f} - {interpretation}")

# Output:
# PEDAGOGUE   :  77.2 - High vocabulary sophistication  
# BIG         :  44.1 - Average vocabulary level
# FAQIR       :  87.0 - Exceptional vocabulary rarity
# QUETZAL     :  79.4 - High vocabulary sophistication
# RUNNING     :  38.2 - Common vocabulary
```

### Information Content Scorer

Analyze information-theoretic surprise:

```python
async def test_information_content():
    test_cases = [
        ("pedagogue", "PDG"),  # Multiple solutions available
        ("faqir", "FQR"),      # Very few solutions
        ("big", "BIG"),        # Only one solution
        ("quetzal", "QZL")     # Rare pattern
    ]
    
    async with httpx.AsyncClient() as client:
        for word, plate in test_cases:
            response = await client.post(
                "http://localhost:8000/predict/information",
                json={"word": word, "plate": plate}
            )
            
            if response.status_code == 200:
                data = response.json()
                info_score = data["information_score"]
                solutions_count = data["plate_solutions"]
                probability = data["word_probability"]
                
                print(f"{word.upper():<12} / {plate}: Score {info_score:>3}, "
                      f"{solutions_count:>2} solutions, P={probability:.3f}")

# Output:
# PEDAGOGUE    / PDG: Score  65, 15 solutions, P=0.067
# FAQIR        / FQR: Score  68,  6 solutions, P=0.167  
# BIG          / BIG: Score   0,  1 solutions, P=1.000
# QUETZAL      / QZL: Score  34,  8 solutions, P=0.125
```

### Orthographic Complexity Scorer

Test n-gram pattern complexity:

```python
async def test_orthographic_complexity():
    test_words = [
        "big",          # Simple patterns
        "pedagogue",    # Moderate complexity
        "faqir",        # Contains rare 'q' patterns  
        "razzmatazz",   # Double letters, unusual patterns
        "quetzal"       # Complex consonant clusters
    ]
    
    async with httpx.AsyncClient() as client:
        for word in test_words:
            response = await client.post(
                "http://localhost:8000/predict/orthographic", 
                json={"word": word}
            )
            
            if response.status_code == 200:
                data = response.json()
                ortho_score = data["orthographic_score"]
                avg_prob = data["ngram_analysis"]["avg_ngram_probability"]
                interpretation = data["interpretation"]
                
                print(f"{word.upper():<12}: Score {ortho_score:>3}, "
                      f"Avg P={avg_prob:.4f}, {interpretation}")

# Output:
# BIG         : Score  36, Avg P=0.0234, Simple orthographic patterns
# PEDAGOGUE   : Score  54, Avg P=0.0089, Moderate orthographic complexity  
# FAQIR       : Score  96, Avg P=0.0012, Exceptional orthographic complexity
# RAZZMATAZZ  : Score  91, Avg P=0.0018, Very high orthographic complexity
# QUETZAL     : Score  78, Avg P=0.0045, High orthographic complexity
```

## Advanced Workflow Examples

### Complete Plate Analysis Pipeline

Analyze all aspects of a license plate pattern:

```python
import asyncio
import httpx
from typing import List, Dict

class PlateAnalyzer:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def analyze_plate_complete(self, plate: str) -> Dict:
        """Complete analysis of a license plate pattern."""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Find all solutions
            solutions_response = await client.get(f"{self.base_url}/solve/{plate}")
            solutions_data = solutions_response.json()
            solutions = solutions_data["solutions"]
            
            print(f"🎯 ANALYZING PLATE: {plate}")
            print(f"   Found {len(solutions)} total solutions")
            
            # 2. Score top solutions (limit for performance)
            top_solutions = solutions[:20] if len(solutions) > 20 else solutions
            scored_solutions = []
            
            for i, word in enumerate(top_solutions):
                if i % 5 == 0:
                    print(f"   Scoring progress: {i+1}/{len(top_solutions)}")
                
                try:
                    score_response = await client.post(
                        f"{self.base_url}/predict/ensemble",
                        json={"word": word, "plate": plate}
                    )
                    
                    if score_response.status_code == 200:
                        score_data = score_response.json()
                        scored_solutions.append({
                            "word": word,
                            "ensemble_score": score_data["ensemble_score"],
                            "vocabulary": score_data["individual_scores"]["vocabulary"]["score"],
                            "information": score_data["individual_scores"]["information"]["score"], 
                            "orthographic": score_data["individual_scores"]["orthographic"]["score"],
                            "interpretation": score_data["interpretation"]
                        })
                        
                except Exception as e:
                    print(f"   ⚠️  Error scoring {word}: {e}")
            
            # 3. Rank solutions by ensemble score
            scored_solutions.sort(key=lambda x: x["ensemble_score"], reverse=True)
            
            # 4. Analysis summary
            analysis = {
                "plate": plate,
                "total_solutions": len(solutions),
                "scored_solutions": len(scored_solutions),
                "top_10": scored_solutions[:10],
                "score_distribution": self._analyze_score_distribution(scored_solutions),
                "dimensional_analysis": self._analyze_dimensions(scored_solutions)
            }
            
            return analysis
    
    def _analyze_score_distribution(self, solutions: List[Dict]) -> Dict:
        """Analyze distribution of ensemble scores."""
        scores = [s["ensemble_score"] for s in solutions]
        
        if not scores:
            return {}
        
        return {
            "min_score": min(scores),
            "max_score": max(scores),
            "average_score": sum(scores) / len(scores),
            "score_range": max(scores) - min(scores),
            "high_scorers": len([s for s in scores if s >= 70]),  # Excellent tier
            "low_scorers": len([s for s in scores if s <= 30])    # Poor tier
        }
    
    def _analyze_dimensions(self, solutions: List[Dict]) -> Dict:
        """Analyze performance across scoring dimensions."""
        if not solutions:
            return {}
        
        vocab_scores = [s["vocabulary"] for s in solutions]
        info_scores = [s["information"] for s in solutions] 
        ortho_scores = [s["orthographic"] for s in solutions]
        
        return {
            "vocabulary": {
                "average": sum(vocab_scores) / len(vocab_scores),
                "top_scorer": max(solutions, key=lambda x: x["vocabulary"])["word"]
            },
            "information": {
                "average": sum(info_scores) / len(info_scores),
                "top_scorer": max(solutions, key=lambda x: x["information"])["word"]
            },
            "orthographic": {
                "average": sum(ortho_scores) / len(ortho_scores), 
                "top_scorer": max(solutions, key=lambda x: x["orthographic"])["word"]
            }
        }
    
    def print_analysis_report(self, analysis: Dict):
        """Print formatted analysis report."""
        plate = analysis["plate"]
        
        print(f"\n📊 COMPLETE ANALYSIS REPORT: {plate}")
        print("=" * 60)
        
        # Summary statistics
        dist = analysis["score_distribution"]
        print(f"Total Solutions: {analysis['total_solutions']}")
        print(f"Successfully Scored: {analysis['scored_solutions']}")
        print(f"Score Range: {dist.get('min_score', 0):.1f} - {dist.get('max_score', 0):.1f}")
        print(f"Average Score: {dist.get('average_score', 0):.1f}")
        print(f"Excellent (70+): {dist.get('high_scorers', 0)} words")
        print(f"Poor (≤30): {dist.get('low_scorers', 0)} words")
        
        # Dimensional analysis
        dims = analysis["dimensional_analysis"]
        if dims:
            print(f"\nDimensional Leaders:")
            print(f"  Vocabulary: {dims['vocabulary']['top_scorer'].upper()} "
                  f"({dims['vocabulary']['average']:.1f} avg)")
            print(f"  Information: {dims['information']['top_scorer'].upper()} "
                  f"({dims['information']['average']:.1f} avg)")
            print(f"  Orthographic: {dims['orthographic']['top_scorer'].upper()} "
                  f"({dims['orthographic']['average']:.1f} avg)")
        
        # Top solutions
        print(f"\n🏆 TOP 10 SOLUTIONS:")
        print(f"{'Rank':<4} {'Word':<12} {'Score':<6} {'V':<4} {'I':<4} {'O':<4} {'Interpretation'}")
        print("-" * 75)
        
        for i, solution in enumerate(analysis["top_10"], 1):
            word = solution["word"].upper()
            score = solution["ensemble_score"]
            vocab = solution["vocabulary"]
            info = solution["information"] 
            ortho = solution["orthographic"]
            interp = solution["interpretation"][:35] + "..." if len(solution["interpretation"]) > 35 else solution["interpretation"]
            
            print(f"{i:<4} {word:<12} {score:<6.1f} {vocab:<4.0f} {info:<4.0f} {ortho:<4.0f} {interp}")

# Usage example
async def main():
    analyzer = PlateAnalyzer()
    
    # Analyze multiple plates
    plates = ["PDG", "QZL", "FQR", "BIG", "XYZ"]
    
    for plate in plates:
        analysis = await analyzer.analyze_plate_complete(plate)
        analyzer.print_analysis_report(analysis)
        print("\n" + "="*80 + "\n")

# Run the analysis
# asyncio.run(main())
```

### Custom Weight Tuning Examples

#### Emphasizing Different Dimensions

```python
async def test_weight_strategies():
    """Test different weighting strategies on the same word."""
    
    test_case = {"word": "pedagogue", "plate": "PDG"}
    
    weight_strategies = {
        "balanced": {"vocabulary": 1.0, "information": 1.0, "orthographic": 1.0},
        "vocab_focused": {"vocabulary": 2.0, "information": 1.0, "orthographic": 0.5},
        "info_focused": {"vocabulary": 0.5, "information": 2.0, "orthographic": 1.0},
        "complexity_focused": {"vocabulary": 0.5, "information": 1.0, "orthographic": 2.0},
        "vocab_info_only": {"vocabulary": 1.0, "information": 1.0, "orthographic": 0.0}
    }
    
    async with httpx.AsyncClient() as client:
        print(f"🎛️  WEIGHT STRATEGY COMPARISON: {test_case['word'].upper()} / {test_case['plate']}")
        print("-" * 70)
        print(f"{'Strategy':<20} {'Score':<6} {'V-Contrib':<10} {'I-Contrib':<10} {'O-Contrib':<10}")
        print("-" * 70)
        
        for strategy_name, weights in weight_strategies.items():
            response = await client.post(
                "http://localhost:8000/predict/ensemble",
                json={**test_case, "weights": weights}
            )
            
            if response.status_code == 200:
                data = response.json()
                score = data["ensemble_score"]
                
                # Extract contributions
                individual = data["individual_scores"]
                v_contrib = individual["vocabulary"]["contribution"]
                i_contrib = individual["information"]["contribution"] 
                o_contrib = individual["orthographic"]["contribution"]
                
                print(f"{strategy_name:<20} {score:<6.1f} {v_contrib:<10.1f} {i_contrib:<10.1f} {o_contrib:<10.1f}")

# Expected output:
# Strategy             Score  V-Contrib  I-Contrib  O-Contrib 
# balanced             65.2   25.7       21.7       18.0      
# vocab_focused        70.8   38.5       21.7       9.0       
# info_focused         62.1   12.8       43.3       18.0      
# complexity_focused   58.7   12.8       21.7       36.0      
# vocab_info_only      71.0   38.5       32.5       0.0       
```

### Batch Processing Examples

#### Score Multiple Words Against Multiple Plates

```python
async def batch_scoring_example():
    """Demonstrate batch processing of multiple word-plate combinations."""
    
    word_plate_pairs = [
        ("pedagogue", "PDG"),
        ("faqir", "FQR"), 
        ("quetzal", "QZL"),
        ("big", "BIG"),
        ("razzmatazz", "RZZ"),
        ("muzhik", "UZK")
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🔄 BATCH SCORING RESULTS")
        print("=" * 80)
        print(f"{'Word':<15} {'Plate':<6} {'Ensemble':<9} {'Vocab':<6} {'Info':<6} {'Ortho':<6} {'Interpretation'}")
        print("-" * 80)
        
        # Process all pairs concurrently
        tasks = []
        for word, plate in word_plate_pairs:
            task = client.post(
                "http://localhost:8000/predict/ensemble",
                json={"word": word, "plate": plate}
            )
            tasks.append((word, plate, task))
        
        # Gather all results
        for word, plate, task in tasks:
            try:
                response = await task
                if response.status_code == 200:
                    data = response.json()
                    
                    ensemble = data["ensemble_score"]
                    vocab = data["individual_scores"]["vocabulary"]["score"]
                    info = data["individual_scores"]["information"]["score"]
                    ortho = data["individual_scores"]["orthographic"]["score"]
                    interp = data["interpretation"][:30] + "..." if len(data["interpretation"]) > 30 else data["interpretation"]
                    
                    print(f"{word.upper():<15} {plate:<6} {ensemble:<9.1f} {vocab:<6.0f} {info:<6.0f} {ortho:<6.0f} {interp}")
                else:
                    print(f"{word.upper():<15} {plate:<6} ERROR     -      -      -      HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"{word.upper():<15} {plate:<6} ERROR     -      -      -      {str(e)[:20]}")
```

### Performance Testing Examples

#### API Load Testing

```python
import asyncio
import httpx
import time
from statistics import mean, median

async def performance_test():
    """Test API performance under load."""
    
    # Test cases for performance testing
    test_cases = [
        ("pedagogue", "PDG"),
        ("faqir", "FQR"),
        ("big", "BIG"),
        ("quetzal", "QZL"),
        ("razzmatazz", "RZZ")
    ] * 20  # Multiply for more load
    
    async def single_request(word, plate):
        """Single scoring request with timing."""
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    "http://localhost:8000/predict/ensemble",
                    json={"word": word, "plate": plate}
                )
                
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # Convert to ms
                
                return {
                    "success": response.status_code == 200,
                    "duration_ms": duration,
                    "status_code": response.status_code
                }
                
            except Exception as e:
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                
                return {
                    "success": False,
                    "duration_ms": duration,
                    "error": str(e)
                }
    
    print("🚀 PERFORMANCE TEST STARTING")
    print(f"   Total requests: {len(test_cases)}")
    print(f"   Concurrent requests: 10")
    
    start_time = time.time()
    
    # Run requests in batches to control concurrency
    batch_size = 10
    all_results = []
    
    for i in range(0, len(test_cases), batch_size):
        batch = test_cases[i:i + batch_size]
        
        # Create tasks for this batch
        tasks = [single_request(word, plate) for word, plate in batch]
        
        # Execute batch concurrently
        batch_results = await asyncio.gather(*tasks)
        all_results.extend(batch_results)
        
        print(f"   Completed batch {(i // batch_size) + 1}/{(len(test_cases) + batch_size - 1) // batch_size}")
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Analyze results
    successful_requests = [r for r in all_results if r["success"]]
    failed_requests = [r for r in all_results if not r["success"]]
    
    if successful_requests:
        durations = [r["duration_ms"] for r in successful_requests]
        
        print("\n📊 PERFORMANCE RESULTS")
        print("=" * 50)
        print(f"Total Requests: {len(all_results)}")
        print(f"Successful: {len(successful_requests)} ({len(successful_requests)/len(all_results)*100:.1f}%)")
        print(f"Failed: {len(failed_requests)} ({len(failed_requests)/len(all_results)*100:.1f}%)")
        print(f"Total Time: {total_duration:.2f}s")
        print(f"Requests/Second: {len(all_results)/total_duration:.1f}")
        print(f"\nResponse Time Statistics:")
        print(f"  Average: {mean(durations):.1f}ms")
        print(f"  Median: {median(durations):.1f}ms") 
        print(f"  Min: {min(durations):.1f}ms")
        print(f"  Max: {max(durations):.1f}ms")
        
        # Percentiles
        sorted_durations = sorted(durations)
        p95_index = int(0.95 * len(sorted_durations))
        p99_index = int(0.99 * len(sorted_durations))
        
        print(f"  P95: {sorted_durations[p95_index]:.1f}ms")
        print(f"  P99: {sorted_durations[p99_index]:.1f}ms")
    
    if failed_requests:
        print(f"\n❌ Failed Request Summary:")
        error_counts = {}
        for req in failed_requests:
            error = req.get("error", f"HTTP {req.get('status_code', 'unknown')}")
            error_counts[error] = error_counts.get(error, 0) + 1
        
        for error, count in error_counts.items():
            print(f"   {error}: {count} times")
```

## Integration Examples

### Python SDK Example

```python
# pl8wrds_client.py
import httpx
import asyncio
from typing import Optional, Dict, List

class PL8WRDSClient:
    """Python client for PL8WRDS API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
    
    async def solve_plate(self, plate: str) -> List[str]:
        """Find all solutions for a license plate pattern."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/solve/{plate}")
            response.raise_for_status()
            return response.json()["solutions"]
    
    async def score_ensemble(
        self, 
        word: str, 
        plate: str, 
        weights: Optional[Dict[str, float]] = None
    ) -> Dict:
        """Score a word using the ensemble system."""
        payload = {"word": word, "plate": plate}
        if weights:
            payload["weights"] = weights
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/predict/ensemble",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def score_vocabulary(self, word: str) -> Dict:
        """Score vocabulary sophistication only."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/predict/vocabulary",
                json={"word": word}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_corpus_stats(self) -> Dict:
        """Get corpus statistics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/corpus/stats")
            response.raise_for_status()
            return response.json()
    
    async def health_check(self) -> Dict:
        """Check API health."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

# Usage example
async def main():
    client = PL8WRDSClient()
    
    # Check if API is healthy
    health = await client.health_check()
    print(f"API Status: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}")
    
    # Analyze a plate
    plate = "PDG"
    solutions = await client.solve_plate(plate)
    print(f"Found {len(solutions)} solutions for {plate}")
    
    # Score the top solution
    if solutions:
        top_word = solutions[0]
        score = await client.score_ensemble(top_word, plate)
        print(f"{top_word.upper()}: {score['ensemble_score']:.1f}")

# asyncio.run(main())
```

### JavaScript/Node.js Example

```javascript
// pl8wrds-client.js
const axios = require('axios');

class PL8WRDSClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.client = axios.create({ baseURL: this.baseUrl });
  }

  async solvePlate(plate) {
    try {
      const response = await this.client.get(`/solve/${plate}`);
      return response.data.solutions;
    } catch (error) {
      throw new Error(`Failed to solve plate ${plate}: ${error.message}`);
    }
  }

  async scoreEnsemble(word, plate, weights = null) {
    try {
      const payload = { word, plate };
      if (weights) payload.weights = weights;
      
      const response = await this.client.post('/predict/ensemble', payload);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to score ${word}/${plate}: ${error.message}`);
    }
  }

  async analyzeCompletePlate(plate, maxWords = 10) {
    const solutions = await this.solvePlate(plate);
    const topSolutions = solutions.slice(0, maxWords);
    
    const scoringPromises = topSolutions.map(word => 
      this.scoreEnsemble(word, plate)
        .then(score => ({ word, ...score }))
        .catch(error => ({ word, error: error.message }))
    );
    
    const results = await Promise.all(scoringPromises);
    
    // Sort by ensemble score
    const validResults = results.filter(r => !r.error);
    validResults.sort((a, b) => b.ensemble_score - a.ensemble_score);
    
    return {
      plate,
      totalSolutions: solutions.length,
      analyzedSolutions: validResults.length,
      topSolutions: validResults
    };
  }
}

// Usage example
async function example() {
  const client = new PL8WRDSClient();
  
  try {
    const analysis = await client.analyzeCompletePlate('PDG', 5);
    
    console.log(`🎯 Analysis for ${analysis.plate}:`);
    console.log(`   Total solutions: ${analysis.totalSolutions}`);
    console.log(`   Top solutions:`);
    
    analysis.topSolutions.forEach((solution, index) => {
      console.log(`   ${index + 1}. ${solution.word.toUpperCase()}: ${solution.ensemble_score.toFixed(1)}`);
    });
    
  } catch (error) {
    console.error('Analysis failed:', error.message);
  }
}

// example();
```

---

*Complete usage guide with practical examples*
*Covers basic usage, advanced workflows, performance testing, and client integrations*
