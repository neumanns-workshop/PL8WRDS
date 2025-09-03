# PL8WRDS Client Game Data

This directory contains the complete, optimized game data for PL8WRDS with real ensemble scoring.

## Files Overview

### `pl8wrds_complete.json.gz` (~25MB)
**Complete game dataset** - Everything needed for full offline gameplay.

```javascript
{
  "plates": [
    {
      "letters": ["A", "A", "A"],
      "solutions": {
        "1940": 67,  // word_id: 1940, information_score: 67
        "2841": 52,  // word_id: 2841, information_score: 52
        // ... more word_id -> info_score mappings
      }
    },
    // ... 15,715+ more plates
  ],
  "metadata": {
    "total_plates": 15715,
    "generation_date": "2024-XX-XX",
    "version": "5.0"
  }
}
```

### `words/dictionary.json` (~5MB)
**Word dictionary with pre-computed scores** - Load once, reference everywhere.

```javascript
{
  "1940": {
    "word": "advantage",
    "frequency_score": 78,      // Vocabulary sophistication (0-100)
    "orthographic_score": 42    // Letter pattern complexity (0-100)
  },
  "2841": {
    "word": "area",
    "frequency_score": 89,
    "orthographic_score": 23
  }
  // ... 103,949 more words
}
```

### `manifests/collection.json` (1KB)  
**Collection metadata** - Difficulty tiers, achievement targets, starter recommendations.

```javascript
{
  "collection_info": {
    "name": "PL8WRDS Complete Collection",
    "total_plates": 15715,
    "total_solutions": 7000000,
    "unique_words": 103949
  },
  "difficulty_system": {
    "type": "solution_count_based",
    "tiers": {
      "ultra_hard": "< 25 solutions",
      "very_hard": "25-50 solutions",
      "hard": "50-100 solutions",
      "medium": "100-200 solutions",
      "easy": "200+ solutions"
    }
  },
  "starter_collection": {
    "recommended_first_10": [1234, 2456, 3678],
    "beginner_friendly": [...]
  }
}
```

## Data Structure

### Ensemble Scoring System
Each word-plate combination has three scoring components:

1. **Vocabulary Sophistication** (pre-computed per word)
   - Based on corpus frequency and rarity
   - Stored in `words/dictionary.json` as `frequency_score`

2. **Information Content** (computed per word-plate pair)
   - Contextual surprisal given plate constraints
   - Stored in main data as `solutions[word_id]`

3. **Orthographic Complexity** (pre-computed per word)
   - Letter pattern complexity and visual difficulty
   - Stored in `words/dictionary.json` as `orthographic_score`

**Ensemble Score** = Average of all three components

### Difficulty Rating
Plates are rated by solution count (fewer = harder):
- **Ultra Hard (90-100)**: < 25 solutions
- **Very Hard (80-89)**: 25-50 solutions  
- **Hard (60-79)**: 50-100 solutions
- **Medium (30-59)**: 100-200 solutions
- **Easy (0-29)**: 200+ solutions

## Usage Patterns

### Pattern 1: Complete Load (Recommended)
```javascript
// Load main game data
const response = await fetch('pl8wrds_complete.json.gz');
const compressed = await response.arrayBuffer();
const gameData = JSON.parse(pako.inflate(compressed, { to: 'string' }));

// Load word dictionary
const wordDict = await fetch('words/dictionary.json').then(r => r.json());

// Create full solution objects
const plate = gameData.plates[1234];
const solutions = Object.entries(plate.solutions).map(([wordId, infoScore]) => {
  const word = wordDict[wordId];
  return {
    word: word.word,
    wordId: parseInt(wordId),
    vocabulary_score: word.frequency_score,
    information_score: infoScore,
    orthographic_score: word.orthographic_score,
    ensemble_score: Math.round((word.frequency_score + infoScore + word.orthographic_score) / 3)
  };
});
```

### Pattern 2: Progressive Load
```javascript
// Load dictionary first (for word resolution)
const wordDict = await fetch('words/dictionary.json').then(r => r.json());

// Load collection manifest for metadata
const manifest = await fetch('manifests/collection.json').then(r => r.json());

// Load main game data when needed
const gameData = await loadCompressedJSON('pl8wrds_complete.json.gz');
```

## Data Optimization Features

- **Split Architecture**: Word properties separate from context-dependent scores
- **Efficient Storage**: `{word_id: info_score}` instead of full objects  
- **Pre-computed Components**: Frequency and orthographic scores bundled with dictionary
- **Runtime Assembly**: Only information scores computed per plate-word pair
- **Compression**: Gzip compressed with optimal JSON structure
- **Zero Redundancy**: Each word stored once, referenced by ID

## Performance Notes

- **Generation Time**: 23 seconds total (ultra-optimized pipeline)
- **Data Size**: ~25MB compressed, ~150MB uncompressed
- **Loading Speed**: Progressive decompression with pako
- **Memory Usage**: Efficient word ID references minimize memory footprint
- **Score Accuracy**: Real mathematical models, no approximations

## Integration Guidelines

1. **Word Resolution**: Always resolve word IDs using the dictionary
2. **Plate Access**: Use array indexing (`gameData.plates[index]`)
3. **Score Assembly**: Combine three components for ensemble score
4. **Difficulty Calculation**: Base on `Object.keys(plate.solutions).length`
5. **Error Handling**: Check for missing word IDs in dictionary