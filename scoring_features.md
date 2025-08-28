# Scoring Features Inventory

A comprehensive catalog of scorable dimensions for license plate word games.

## Frequency-Based Features

### Term Frequency (TF)
**Definition**: How common is this word among all words that match this plate?
```python
tf_score = word_frequency / sum(all_frequencies_for_plate)
surprisal_tf = -log2(tf_score)
```
**Example**: "ambulance" for "abc" has high frequency → low surprisal
**Range**: 0 to ∞ (higher = more surprising)

### Inverse Document Frequency (IDF)  
**Definition**: How many different plates contain this word?
```python
plates_containing_word = count_plates_with_word(word)
idf_score = log2(total_possible_plates / plates_containing_word)
```
**Example**: "the" appears in many plates → low IDF, "concatenate" appears in few → high IDF
**Range**: 0 to log2(total_plates)

## Pattern-Based Features

### Non-Consecutiveness Score
**Definition**: How spread out are the plate letters within the word?
```python
def calculate_gaps(plate, word):
    positions = find_plate_letter_positions(plate, word)
    total_gaps = sum(pos[i+1] - pos[i] - 1 for i in range(len(pos)-1))
    return total_gaps / len(word)  # Normalized by word length
```
**Example**: 
- "abc" → "abc" = 0 gaps
- "abc" → "ambulance" = 6 intervening letters
**Range**: 0 to 1 (higher = more spread out)

### Positional Entropy
**Definition**: How evenly distributed are the pattern matches?
```python
def positional_entropy(plate, word):
    positions = find_plate_letter_positions(plate, word)
    relative_positions = [pos / len(word) for pos in positions]
    # Calculate entropy of position distribution
    return entropy(relative_positions)
```
**Range**: 0 to log2(len(plate)) (higher = more evenly spread)

### Pattern Density
**Definition**: What percentage of the word is "used" by the pattern?
```python
pattern_density = len(plate) / len(word)
```
**Example**: "abc" in "ambulance" = 3/9 = 0.33
**Range**: 0 to 1 (higher = more efficient use of letters)

## Linguistic Features

### Length Efficiency 
**Definition**: Shorter words are harder to find - they use the pattern more efficiently
```python
# Invert length - shorter words score higher
max_reasonable_length = 15  # Reasonable upper bound
length_efficiency = (max_reasonable_length - len(word)) / max_reasonable_length
# Or pattern efficiency: how much of the word is the pattern?
pattern_efficiency = len(plate) / len(word)
```
**Example**: "cat" for "cat" = very efficient, "ambulance" for "abc" = less efficient
**Range**: 0 to 1 (higher = more efficient/harder to find)

### Syllable Density
**Definition**: Syllable density - more syllables in shorter words is harder
```python
syllable_count = count_syllables(word)
syllable_density = syllable_count / len(word)  # Syllables per character
# Note: This may correlate with difficulty but needs validation
```
**Range**: 0 to ~0.5 (higher = more syllables per character, unclear if harder)

### Affix Penalty
**Definition**: Letters appearing in common affixes make finding words easier ("cheating")
```python
def affix_penalty(plate, word):
    penalty = 0
    # Check if plate letters appear in common prefixes/suffixes
    common_prefixes = ['pre', 'un', 'dis', 're', 'in', 'im', 'non']
    common_suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'ness']
    
    for affix in common_prefixes + common_suffixes:
        if any(letter in affix for letter in plate):
            if affix in word:
                penalty += 1
    return penalty

# Lower penalty = harder find (pattern in root, not affixes)
difficulty_bonus = max(0, 3 - affix_penalty(plate, word))
```
**Example**: "ing" pattern in "singing" = high penalty (easy), "cat" in "delicate" = low penalty (harder)
**Range**: 0 to 3 (higher = more difficult, pattern not in obvious affixes)

### Part of Speech Rarity
**Definition**: How common is this part of speech?
```python
pos_weights = {
    'noun': 1.0,
    'verb': 1.2, 
    'adjective': 1.5,
    'adverb': 2.0,
    'proper_noun': 2.5
}
pos_score = pos_weights.get(get_pos(word), 1.0)
```

## Discovery Features

### Semantic Surprise
**Definition**: How unexpected is this word's meaning/domain?
```python
# Could use word embeddings or domain classification
domain_rarity = {
    'common': 1.0,
    'technical': 1.5,
    'academic': 2.0,
    'archaic': 2.5,
    'specialized': 3.0
}
semantic_score = domain_rarity.get(classify_domain(word), 1.0)
```

### Phonetic Surprise
**Definition**: Unusual pronunciation patterns, silent letters
```python
def phonetic_surprise(word):
    score = 0
    score += count_silent_letters(word) * 0.5
    score += unusual_letter_combinations(word) * 0.3
    score += pronunciation_difficulty(word)
    return score
```

### Edit Distance
**Definition**: How different is the word from the plate?
```python
edit_distance_score = edit_distance(plate, word) / max(len(plate), len(word))
```
**Range**: 0 to 1 (higher = more different)

## Meta Features

### Player Discovery Rate
**Definition**: How often do players find this word for this plate?
```python
discovery_rate = times_found / times_plate_played
rarity_bonus = -log2(discovery_rate + epsilon)  # Avoid log(0)
```
**Note**: Requires gameplay data

### Time to Discovery
**Definition**: Average time players take to find this word
```python
time_difficulty = average_discovery_time / baseline_time
```
**Note**: Requires gameplay data

### Historical Performance
**Definition**: How this word has performed in past games
```python
historical_score = (total_points_awarded / times_found) / average_points_per_word
```

## Composite Scoring Examples

### Basic Surprisal (Current Implementation)
```python
basic_score = surprisal_tf  # Just term frequency surprisal
```

### Enhanced TF-IDF  
```python
enhanced_score = surprisal_tf + idf_score
```

### Full Composite Score
```python
composite_score = (
    surprisal_tf * 0.4 +           # Base frequency surprise
    idf_score * 0.3 +              # Cross-plate rarity  
    pattern_efficiency * 0.2 +     # Efficient use of pattern (harder)
    length_efficiency * 0.1        # Shorter words are harder
    # Note: Removed morphological complexity - often makes words easier
)
```

### Game Mode Variations
```python
# Speed mode: Emphasize quick discovery
speed_score = surprisal_tf * 0.8 + pattern_density * 0.2

# Scholar mode: Emphasize rare/semantic finds  
scholar_score = semantic_surprise * 0.4 + idf_score * 0.3 + surprisal_tf * 0.3

# Explorer mode: Emphasize efficient pattern usage
explorer_score = pattern_efficiency * 0.4 + idf_score * 0.3 + surprisal_tf * 0.3
```

## Implementation Notes

### Data Requirements
- **Dictionary with frequencies**: ✅ Already have
- **Plate enumeration**: Need to generate all possible plates
- **Cross-plate word mapping**: Need to build word→plates index
- **Linguistic features**: Optional, can add incrementally
- **Gameplay data**: Future enhancement

### Performance Considerations
- **Pre-compute IDF scores** for all words
- **Cache pattern analysis** for common words
- **Lazy load** expensive linguistic features
- **Batch process** composite scores

### Extensibility
- **Modular design**: Each feature as separate function
- **Configurable weights**: Allow different scoring profiles
- **A/B testing**: Easy to compare different scoring approaches
- **Player preferences**: Let users weight features differently
