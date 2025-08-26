/**
 * GameAPI - Simple data access layer for PL8WRDS
 * Provides easy word validation and comprehensive linguistic data access
 */

class GameAPI {
    constructor(dataManager, solver) {
        this.dataManager = dataManager;
        this.solver = solver;
        this.gameCache = new Map(); // Cache for expensive operations
    }

    /**
     * WORD VALIDATION - Core game mechanic
     */
    
    /**
     * Validate if a word is valid for a license plate
     * Returns validation result with access to all linguistic data
     */
    async validateWord(word, plateLetters) {
        const normalizedWord = word.toLowerCase();
        const normalizedPlate = plateLetters.toUpperCase();
        
        // Check if word exists in our dictionary
        const isValidWord = this.dataManager.getWords().includes(normalizedWord);
        if (!isValidWord) {
            return {
                valid: false,
                reason: 'not_in_dictionary',
                word: normalizedWord,
                plateLetters: normalizedPlate
            };
        }
        
        // Check if word can be made from plate letters
        const canMake = this.solver.canMakeWord(normalizedWord.toUpperCase(), normalizedPlate);
        if (!canMake) {
            return {
                valid: false,
                reason: 'cannot_make_from_letters',
                word: normalizedWord,
                plateLetters: normalizedPlate
            };
        }
        
        // Valid word! Return with all available data
        const wordData = await this.getCompleteWordData(normalizedWord);
        
        return {
            valid: true,
            word: normalizedWord,
            plateLetters: normalizedPlate,
            ...wordData
        };
    }
    
    /**
     * Get ALL available linguistic data for a word
     */
    async getCompleteWordData(word) {
        const cacheKey = `complete_${word}`;
        if (this.gameCache.has(cacheKey)) {
            return this.gameCache.get(cacheKey);
        }
        
        // Load ALL available data types in parallel
        const [
            frequency, 
            pronunciation, 
            definitions,
            etymologies,
            semanticRelationships,
            memberships, 
            syllableCount, 
            rhymeGroups
        ] = await Promise.all([
            this.dataManager.getFrequency(word),
            this.dataManager.getPronunciation(word),
            this.dataManager.getDefinitions(word),
            this.dataManager.getEtymologies(word),
            this.dataManager.getSemanticRelationships(word),
            this.dataManager.getCuratedMemberships(word),
            this.dataManager.getSyllableCount(word),
            this.dataManager.getAllRhymeGroups(word)
        ]);
        
        const data = {
            // Basic properties
            length: word.length,
            
            // Frequency data
            frequency: frequency?.frequency || null,
            frequencyRank: frequency ? this.getFrequencyTier(frequency.frequency) : 'unknown',
            
            // Phonetic data
            pronunciation: pronunciation?.arpabet || pronunciation?.ipa || null,
            syllables: syllableCount || null,
            rhymeGroups: rhymeGroups || {},
            
            // Semantic data
            definitions: definitions || null,
            etymologies: etymologies || null,
            semanticRelationships: semanticRelationships || null,
            
            // Categorization
            lists: this.extractCuratedLists(memberships),
            sentiment: memberships?.afinn_score || null
        };
        
        this.gameCache.set(cacheKey, data);
        return data;
    }
    
    /**
     * HINT SYSTEM - Game assistance
     */
    
    /**
     * Generate contextual hints for a license plate
     */
    async generateHints(plateLetters, hintsRequested = 3) {
        const hints = [];
        
        // Get some solutions for hint generation
        const solutions = await this.solver.solve(plateLetters, { maxResults: 100 });
        if (solutions.words.length === 0) {
            return [{ type: 'no_solutions', message: 'No valid words found for these letters!' }];
        }
        
        // Hint 1: Length suggestion
        const lengthStats = this.analyzeLengthDistribution(solutions.words);
        hints.push({
            type: 'length_suggestion',
            message: `Try ${lengthStats.mostCommon} letter words - there are ${lengthStats.count} possibilities!`,
            data: { suggestedLength: lengthStats.mostCommon, count: lengthStats.count }
        });
        
        // Hint 2: Rhyme hint (if we have rhyming words)
        const rhymeHint = await this.generateRhymeHint(solutions.words.slice(0, 20));
        if (rhymeHint) hints.push(rhymeHint);
        
        // Hint 3: Syllable hint
        const syllableHint = await this.generateSyllableHint(solutions.words.slice(0, 20));
        if (syllableHint) hints.push(syllableHint);
        
        // Hint 4: Category hint (curated lists)
        const categoryHint = await this.generateCategoryHint(solutions.words.slice(0, 30));
        if (categoryHint) hints.push(categoryHint);
        
        // Hint 5: Letter pattern hint
        const patternHint = this.generatePatternHint(plateLetters, solutions.words.slice(0, 10));
        if (patternHint) hints.push(patternHint);
        
        return hints.slice(0, hintsRequested);
    }
    
    /**
     * Get a word that rhymes with player's input (for rhyme-based hints)
     */
    async getRhymingHint(playerWord) {
        const rhymingWords = await this.dataManager.getRhymingWords(playerWord, 'perfect');
        if (rhymingWords.length > 0) {
            const randomRhyme = rhymingWords[Math.floor(Math.random() * rhymingWords.length)];
            return {
                type: 'rhyme_hint',
                message: `"${playerWord}" rhymes with "${randomRhyme}"`,
                data: { playerWord, rhyme: randomRhyme, allRhymes: rhymingWords }
            };
        }
        return null;
    }
    
    /**
     * DATA ACCESS HELPERS - Easy access to specific data types
     */
    
    /**
     * Get just the definitions for a word
     */
    async getDefinitions(word) {
        return await this.dataManager.getDefinitions(word);
    }
    
    /**
     * Get just the etymologies for a word
     */
    async getEtymologies(word) {
        return await this.dataManager.getEtymologies(word);
    }
    
    /**
     * Get semantic relationships (synonyms, antonyms, etc.)
     */
    async getSemanticRelationships(word) {
        return await this.dataManager.getSemanticRelationships(word);
    }
    
    /**
     * Get rhyming words of a specific type
     */
    async getRhymes(word, rhymeType = 'perfect') {
        return await this.dataManager.getRhymingWords(word, rhymeType);
    }
    
    /**
     * Check if word exists in dictionary
     */
    isWordValid(word) {
        return this.dataManager.getWords().includes(word.toLowerCase());
    }
    
    /**
     * Check if word can be made from license plate letters
     */
    canMakeFromPlate(word, plateLetters) {
        return this.solver.canMakeWord(word.toUpperCase(), plateLetters.toUpperCase());
    }
    
    /**
     * HELPER METHODS - Internal utilities
     */
    
    analyzeLengthDistribution(words) {
        const lengths = {};
        words.forEach(w => {
            const len = w.word ? w.word.length : w.length;
            lengths[len] = (lengths[len] || 0) + 1;
        });
        
        const mostCommon = Object.keys(lengths).reduce((a, b) => 
            lengths[a] > lengths[b] ? a : b
        );
        
        return {
            mostCommon: parseInt(mostCommon),
            count: lengths[mostCommon],
            distribution: lengths
        };
    }
    
    async generateRhymeHint(words) {
        for (const wordObj of words.slice(0, 5)) {
            const word = wordObj.word || wordObj;
            const rhymes = await this.dataManager.getRhymingWords(word, 'perfect');
            if (rhymes.length > 0) {
                return {
                    type: 'rhyme_hint',
                    message: `One word rhymes with "${rhymes[0]}"`,
                    data: { rhymesWith: rhymes[0], word }
                };
            }
        }
        return null;
    }
    
    async generateSyllableHint(words) {
        const syllableCounts = {};
        for (const wordObj of words) {
            const word = wordObj.word || wordObj;
            const syllables = await this.dataManager.getSyllableCount(word);
            if (syllables) {
                syllableCounts[syllables] = (syllableCounts[syllables] || 0) + 1;
            }
        }
        
        if (Object.keys(syllableCounts).length > 0) {
            const mostCommon = Object.keys(syllableCounts).reduce((a, b) => 
                syllableCounts[a] > syllableCounts[b] ? a : b
            );
            return {
                type: 'syllable_hint',
                message: `Look for ${mostCommon}-syllable words`,
                data: { syllables: parseInt(mostCommon), count: syllableCounts[mostCommon] }
            };
        }
        return null;
    }
    
    async generateCategoryHint(words) {
        const categories = { basic: 0, core: 0, positive: 0, negative: 0 };
        
        for (const wordObj of words) {
            const word = wordObj.word || wordObj;
            const memberships = await this.dataManager.getCuratedMemberships(word);
            if (memberships) {
                if (memberships.ogden_basic_concept) categories.basic++;
                if (memberships.swadesh_core) categories.core++;
                if (memberships.afinn_score > 0) categories.positive++;
                if (memberships.afinn_score < 0) categories.negative++;
            }
        }
        
        const bestCategory = Object.keys(categories).reduce((a, b) => 
            categories[a] > categories[b] ? a : b
        );
        
        if (categories[bestCategory] > 0) {
            const messages = {
                basic: 'Try basic English words',
                core: 'Think of core vocabulary words',
                positive: 'Look for positive/happy words',
                negative: 'Consider negative/sad words'
            };
            
            return {
                type: 'category_hint',
                message: messages[bestCategory],
                data: { category: bestCategory, count: categories[bestCategory] }
            };
        }
        return null;
    }
    
    generatePatternHint(plateLetters, words) {
        // Analyze common starting patterns
        const startPatterns = {};
        words.forEach(wordObj => {
            const word = wordObj.word || wordObj;
            const start = word.substring(0, 2);
            startPatterns[start] = (startPatterns[start] || 0) + 1;
        });
        
        if (Object.keys(startPatterns).length > 0) {
            const commonStart = Object.keys(startPatterns).reduce((a, b) => 
                startPatterns[a] > startPatterns[b] ? a : b
            );
            
            return {
                type: 'pattern_hint',
                message: `Many words start with "${commonStart.toUpperCase()}"`,
                data: { pattern: commonStart, count: startPatterns[commonStart] }
            };
        }
        return null;
    }
    
    getFrequencyTier(frequency) {
        if (frequency >= 10.0) return 'very_common';
        if (frequency >= 1.0) return 'common';
        if (frequency >= 0.1) return 'uncommon';
        if (frequency >= 0.01) return 'rare';
        return 'very_rare';
    }
    
    extractCuratedLists(memberships) {
        if (!memberships) return [];
        
        const lists = [];
        if (memberships.ogden_basic_concept) lists.push('ogden_basic');
        if (memberships.swadesh_core) lists.push('swadesh_core');
        if (memberships.swadesh_extended) lists.push('swadesh_extended');
        if (memberships.stop_nltk || memberships.stop_spacy) lists.push('stop_word');
        if (memberships.roget_thesaurus) lists.push('roget_thesaurus');
        
        return lists;
    }
    
    /**
     * Get game statistics and metrics
     */
    getGameStats() {
        return {
            wordsInDictionary: this.dataManager.getWords().length,
            cacheSize: this.gameCache.size,
            solverStats: this.solver.getStats(),
            dataManagerStats: this.dataManager.getStats()
        };
    }
    
    /**
     * Clear caches for memory management
     */
    clearCache() {
        this.gameCache.clear();
        console.log('Game cache cleared');
    }
}

export default GameAPI; 