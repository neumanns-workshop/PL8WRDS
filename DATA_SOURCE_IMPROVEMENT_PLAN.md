# 📊 PL8WRDS Data Source Improvement Plan

## 🔍 Current State Analysis

**Current Source**: SUBTLEX US Corpus
- **Total words**: 74,286
- **Frequency range**: 1 - 2,134,713
- **Coverage**: Good mainstream vocabulary
- **Strengths**: Real usage frequencies, solid coverage of common words
- **Gaps**: Missing specialized vocabulary, limited proper nouns, older frequency data

## 🚀 Improvement Strategies

### 1. **ENHANCED WORD COVERAGE** 🎯

**Priority: HIGH**

**Current Gaps:**
- Scientific/technical terms (only ~6,500 12+ char words)
- Proper nouns (geographic, personal names) 
- Modern slang and internet vocabulary
- Domain-specific jargon (medical, legal, academic)
- Variant spellings and inflections

**Improvement Plan:**
```
📚 TARGET SOURCES:
- Wiktionary (comprehensive, multiple languages)
- Google Books Ngram Corpus (historical perspective)
- Reddit/Twitter corpora (modern usage)
- Academic paper abstracts (technical terms)
- Geographic databases (place names)
- Medical/legal dictionaries
```

**Target**: Expand to **150,000+ words** with better rare word coverage

### 2. **MULTI-DIMENSIONAL FREQUENCY DATA** 📈

**Priority: MEDIUM**

**Current**: Single frequency value
**Enhanced**: Multiple frequency contexts

```json
{
  "word": "pedagogue",
  "frequencies": {
    "general": 5,           // Current SUBTLEX
    "academic": 150,        // Higher in academic texts
    "news": 8,             // News corpora
    "books": 45,           // Literature
    "social": 2            // Social media
  },
  "frequency_contexts": ["education", "formal_writing"],
  "recency_score": 0.3    // How recently used (0-1)
}
```

**Benefits**: Context-aware scoring, better vocabulary sophistication detection

### 3. **ENHANCED METADATA** 🏷️

**Priority: HIGH**

**Current**: Just word + frequency
**Enhanced**: Rich linguistic metadata

```json
{
  "word": "zugzwang",
  "frequency": 1,
  "metadata": {
    "part_of_speech": ["noun"],
    "etymology": "german",
    "semantic_fields": ["chess", "strategy"],
    "difficulty_level": 9.2,     // 1-10 scale
    "pronunciation_difficulty": 8.1,
    "letter_rarity_score": 9.5,
    "morphological_complexity": 6.8,
    "register": "formal",        // formal/informal/technical
    "domain": "games",
    "syllable_count": 2,
    "stress_pattern": "SW"       // Strong-Weak
  }
}
```

**New Scoring Dimensions Enabled:**
- Etymology sophistication (Latin/Greek roots = higher scores)
- Domain expertise (medical/legal terms = complexity boost)
- Morphological complexity (compound words, rare affixes)
- Phonological difficulty (pronunciation challenge)

### 4. **QUALITY IMPROVEMENTS** ✨

**Priority: MEDIUM**

**Issues Found:**
- Some low-quality entries ('s', single letters)
- Inconsistent capitalization
- Missing common sophisticated words
- OCR artifacts from digitization

**Improvement Plan:**
```
🔧 CLEANUP TASKS:
1. Remove artifacts (OCR errors, non-words)
2. Standardize capitalization rules
3. Add missing common sophisticated vocabulary
4. Validate against multiple dictionaries
5. Remove inappropriate content
6. Add inflections for rare words
```

### 5. **DYNAMIC UPDATING SYSTEM** 🔄

**Priority: LOW**

**Vision**: Self-updating corpus that learns from gameplay

```python
# Future capability
class AdaptiveCorpus:
    def learn_from_gameplay(self, word, plate, human_rating):
        """Update word metadata based on human gameplay feedback"""
        
    def suggest_missing_words(self, plate_patterns):
        """Identify gaps in coverage for specific plate patterns"""
        
    def refresh_frequencies(self, new_corpus_data):
        """Update frequencies from newer corpora"""
```

## 🎯 Implementation Priority

### Phase 1: **Quick Wins** (1-2 weeks)
1. **Wiktionary Integration**: Add 30k+ specialized words
2. **Quality Cleanup**: Remove artifacts, standardize format
3. **Basic Metadata**: Add etymology flags, difficulty estimates

### Phase 2: **Enhanced Intelligence** (2-4 weeks)  
1. **Multi-frequency Data**: Academic, news, books corpora
2. **Semantic Tagging**: Domain, register, complexity scores
3. **Pronunciation Data**: Syllables, stress patterns

### Phase 3: **Advanced Features** (1-2 months)
1. **Dynamic Learning**: Gameplay feedback integration
2. **Specialized Corpora**: Medical, legal, scientific terms
3. **Real-time Updates**: Modern slang, new terminology

## 📊 Expected Impact

**Current Top Scores**: FAQIR, ZUGZWANG ~96.6/100
**With Enhanced Data**: 
- More 95+ scoring words (currently ~100 → target ~500)
- Better discrimination in 80-95 range
- More nuanced vocabulary sophistication
- Domain-specific scoring (medical terms, legal jargon)
- Cultural sophistication (etymology, register)

## 🛠️ Technical Implementation

### Quick Start: Enhanced SUBTLEX
```python
# Immediate improvement: enrich existing data
def enhance_current_corpus():
    # Add basic metadata to existing 74k words
    # Classify by difficulty, etymology, domain
    # ~2-3x scoring sophistication improvement
```

### Full Implementation: Multi-Source Corpus
```python
# Complete overhaul with multiple data sources
class EnhancedCorpus:
    def __init__(self):
        self.subtlex = load_subtlex()
        self.wiktionary = load_wiktionary() 
        self.academic = load_academic_corpus()
        self.news = load_news_corpus()
        
    def get_word_profile(self, word):
        # Return comprehensive word intelligence
```

## 💡 Specific Recommendations

**Immediate Actions:**
1. **Start with Wiktionary**: Free, comprehensive, structured data
2. **Add etymology flags**: Latin/Greek/Germanic/etc classification  
3. **Domain tagging**: Medical, legal, scientific, literary
4. **Difficulty scoring**: Based on frequency + complexity metrics

**Data Sources to Explore:**
- Wiktionary XML dumps (free, comprehensive)
- Google Books Ngram (historical frequencies)
- Academic paper abstracts (specialized terms)
- Urban Dictionary (modern slang - filtered)
- Medical Subject Headings (MeSH) 
- Legal term databases

Would you like me to start implementing any of these improvements? The Wiktionary integration would be a great first step!
