# PL8WRDS API Reference

## Data Structures

### Game Data Object
Complete game dataset loaded from `pl8wrds_complete.json.gz`.

```typescript
interface GameData {
  plates: PlateData[];                 // Array of all plate data
  metadata: {
    total_plates: number;
    total_solutions: number;
    generation_date: string;
  };
}
```

### Word Dictionary Entry
Separate file `words/dictionary.json` containing word properties.

```typescript
interface WordDictionary {
  [wordId: string]: {
    word: string;                      // The actual word text
    frequency_score: number;           // Vocabulary sophistication score (0-100)
    orthographic_score: number;       // Letter pattern complexity score (0-100)
  };
}
```

### Plate Data Entry
```typescript
interface PlateData {
  letters: string[];                   // Array of 3 letters ["A", "B", "C"]
  solutions: {                         // Object mapping word IDs to info scores
    [wordId: string]: number;          // wordId -> information_score (0-100)
  };
}
```

### Computed Plate Object (Frontend)
```typescript
interface Plate {
  id: string;                          // Plate index as string
  letters: string;                     // Letters as joined string "ABC"
  difficulty: number;                  // Based on solution count (0-100)
  solution_count: number;              // Total solutions available
  solutions: Solution[];               // Array of computed solutions
}

interface Solution {
  word: string;                        // Resolved word text
  wordId: number;                      // Word ID reference
  ensemble_score: number;              // Average of all three components
  vocabulary_score: number;            // From word dictionary
  information_score: number;           // From plate data
  orthographic_score: number;          // From word dictionary
  found: boolean;                      // Whether player found it
}
```

## Helper Functions

### Data Loading
```javascript
// Load and decompress main game data
async function loadGameData() {
  const response = await fetch('/pl8wrds_complete.json.gz');
  const compressed = await response.arrayBuffer();
  const decompressed = pako.inflate(compressed, { to: 'string' });
  return JSON.parse(decompressed);
}

// Load word dictionary
async function loadWordDictionary() {
  const response = await fetch('/words/dictionary.json');
  return await response.json();
}
```

### Word Resolution
```javascript
function createSolution(wordId, infoScore, wordDictionary) {
  const wordData = wordDictionary[wordId];
  if (!wordData) return null;
  
  return {
    word: wordData.word,
    wordId: parseInt(wordId),
    vocabulary_score: wordData.frequency_score,
    information_score: infoScore,
    orthographic_score: wordData.orthographic_score,
    ensemble_score: Math.round(
      (wordData.frequency_score + infoScore + wordData.orthographic_score) / 3
    ),
    found: false
  };
}
```

### Difficulty Classification  
```javascript
function getDifficultyTier(solutionCount) {
  if (solutionCount <= 10) return 'ultra_hard';    // 95 difficulty
  if (solutionCount <= 25) return 'very_hard';     // 85 difficulty  
  if (solutionCount <= 50) return 'hard';          // 70 difficulty
  if (solutionCount <= 100) return 'medium';       // 50 difficulty
  if (solutionCount <= 200) return 'easy';         // 30 difficulty
  return 'very_easy';                              // 5 difficulty
}

function calculateDifficulty(solutionCount) {
  if (solutionCount <= 10) return 95;
  if (solutionCount <= 25) return 85;
  if (solutionCount <= 50) return 70;
  if (solutionCount <= 100) return 50;
  if (solutionCount <= 200) return 30;
  if (solutionCount <= 400) return 15;
  return 5;
}
```

### Plate Access
```javascript
// Get plate by index
function getPlate(plateIndex, gameData, wordDictionary) {
  const plateData = gameData.plates[plateIndex];
  if (!plateData) return null;
  
  return createPlateFromData(plateIndex.toString(), plateData, wordDictionary);
}

// Create full plate object with computed solutions
function createPlateFromData(id, plateData, wordDictionary) {
  const solutions = Object.entries(plateData.solutions).map(([wordId, infoScore]) => {
    return createSolution(wordId, infoScore, wordDictionary);
  }).filter(Boolean);
  
  const solutionCount = solutions.length;
  const difficulty = calculateDifficulty(solutionCount);
  
  return {
    id,
    letters: plateData.letters.join('').toUpperCase(),
    difficulty,
    solution_count: solutionCount,
    solutions
  };
}
```

### Score Analysis
```javascript
// Calculate score statistics for a plate
function getPlateScoreStats(plate) {
  const ensembleScores = plate.solutions.map(s => s.ensemble_score);
  
  return {
    averageScore: ensembleScores.reduce((a, b) => a + b, 0) / ensembleScores.length,
    maxScore: Math.max(...ensembleScores),
    minScore: Math.min(...ensembleScores),
    scoreRange: Math.max(...ensembleScores) - Math.min(...ensembleScores)
  };
}

// Find top-scoring solutions
function getTopSolutions(plate, count = 5) {
  return plate.solutions
    .sort((a, b) => b.ensemble_score - a.ensemble_score)
    .slice(0, count);
}
```

## Performance Notes

- **Pre-computed Scores**: Vocabulary and orthographic scores are pre-computed and stored in the word dictionary
- **Runtime Assembly**: Only information scores are plate-specific; other components are looked up
- **Efficient Storage**: Words stored once and referenced by ID to minimize data size
- **Compressed Delivery**: Main data file is gzip compressed for fast loading