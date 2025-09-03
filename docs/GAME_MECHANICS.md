# PL8WRDS Game Mechanics

## Core Game Rules

### License Plate Word Matching
Players must find words that contain the license plate letters **in the correct order** but not necessarily consecutive.

#### Valid Examples for plate "CAR"
- ✅ `car` - Direct match (C-A-R)
- ✅ `card` - C-A-R-d (letters in order)
- ✅ `scar` - s-C-A-R (letters in order)  
- ✅ `careful` - C-A-R-eful (letters in order, gaps allowed)
- ✅ `scarab` - s-C-A-R-ab (multiple gaps allowed)

#### Invalid Examples for plate "CAR"
- ❌ `arc` - Wrong order (A-R-C, not C-A-R)
- ❌ `race` - Wrong order (R-A-C, not C-A-R)
- ❌ `crab` - Missing A before R

## Collectible System

### Plate Collection
- **15,715+ unique plates** with sequential IDs
- **Difficulty ratings** based on solution count (fewer solutions = harder)
- **Real ensemble scores** with 3-dimensional scoring system

### Difficulty Tiers (Based on Solution Count)
```
Ultra Hard (90-100)  - Very few solutions (< 25 words)
Very Hard (80-89)    - Limited solutions (25-50 words)  
Hard (60-79)         - Moderate solutions (50-100 words)
Medium (30-59)       - Good selection (100-200 words)
Easy (0-29)          - Many solutions (200+ words)
```

## Scoring System

### 3-Dimensional Ensemble Scoring
Every word-plate combination includes real mathematical scoring:
- **Ensemble Score**: Average of all three components (0-100)
- **Vocabulary Sophistication**: Word frequency and rarity in corpus (0-100)
- **Information Content**: Contextual surprisal given plate constraints (0-100)
- **Orthographic Complexity**: Letter pattern complexity and visual difficulty (0-100)

### Scoring Interpretation
- **90-100**: Exceptional discoveries (top tier vocabulary)
- **70-89**: Excellent solutions (very impressive words)
- **50-69**: Good solutions (above average complexity)
- **30-49**: Fair solutions (moderate difficulty)
- **0-29**: Basic solutions (common/simple words)

## Progression Mechanics

### Discovery Progression
1. **Starter Plates**: Easy plates with many solutions (200+ words)
2. **Skill Building**: Medium plates with good selection (100-200 words)
3. **Challenge Mode**: Hard plates requiring deeper thinking (50-100 words)
4. **Master Tier**: Very hard plates for experienced players (25-50 words)
5. **Legend Status**: Ultra hard plates for completionists (< 25 words)

### Achievement System
- **Plate Collector**: Collect X plates of each difficulty tier
- **Word Master**: Find high-scoring solutions for challenging plates
- **Perfect Solver**: Complete 100% of solutions for hard plates
- **Speed Runner**: Find solutions under time pressure
- **Score Hunter**: Discover words with exceptional ensemble scores

## Game Modes

### Solo Collection
- **Free Play**: Explore any discovered plate
- **Daily Challenge**: Featured plate with global leaderboard
- **Progression Mode**: Unlock plates by difficulty tier
- **Time Attack**: Find solutions under time pressure

### Competitive Elements  
- **Leaderboards**: Solution count, speed, high-scoring discoveries
- **Trading System**: Share/trade plate discoveries
- **Achievement Comparison**: Compare progress with friends
- **Seasonal Events**: Limited-time featured plates

## Implementation Considerations

### Progressive Difficulty
Use the solution count-based difficulty system to create smooth progression curves.

### Reward Distribution
Balance easy plates (frequent positive feedback) with challenging discoveries (memorable achievements).

### Educational Value
The ensemble scoring system provides insight into English vocabulary sophistication, encouraging learning through:
- **Vocabulary expansion**: Discovering less common words
- **Pattern recognition**: Understanding orthographic complexity
- **Context awareness**: Learning how word information density varies