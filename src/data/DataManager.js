/**
 * DataManager - Efficient access layer for PL8WRDS modular data
 * Handles lazy loading, caching, and search operations
 */

class DataManager {
    constructor() {
        this.cache = {
            words: null,
            pronunciations: new Map(),
            frequencies: new Map(),
            definitions: new Map(),
            etymologies: new Map(),
            semanticRelationships: new Map(),
            curatedMemberships: new Map(),
            syllableCounts: new Map(),
            rhymeGroups: new Map(),
            _plateData: null,
        };
        
        this.metadata = {};
        this.loadPromises = new Map();
        this.isInitialized = false;
    }

    /**
     * Initialize with basic word list - fast startup
     */
    async initialize() {
        if (this.isInitialized) return;
        
        try {
            const wordsData = await this.loadJSON('modular_data/words.json');
            this.cache.words = wordsData.words;
            this.metadata.words = wordsData.metadata;
            this.isInitialized = true;
            console.log(`DataManager initialized with ${this.cache.words.length} words`);
        } catch (error) {
            console.error('Failed to initialize DataManager:', error);
            throw error;
        }
    }

    /**
     * Get all words (already loaded during init)
     */
    getWords() {
        if (!this.isInitialized) {
            throw new Error('DataManager not initialized. Call initialize() first.');
        }
        return this.cache.words;
    }

    /**
     * Get pronunciation for a word (lazy loaded)
     */
    async getPronunciation(word) {
        if (this.cache.pronunciations.has(word)) {
            return this.cache.pronunciations.get(word);
        }

        await this.ensureDataLoaded('pronunciations');
        return this.cache.pronunciations.get(word) || null;
    }

    /**
     * Get frequency data for a word (lazy loaded)
     */
    async getFrequency(word) {
        if (this.cache.frequencies.has(word)) {
            return this.cache.frequencies.get(word);
        }

        await this.ensureDataLoaded('frequencies');
        return this.cache.frequencies.get(word) || null;
    }

    /**
     * Get definitions for a word (lazy loaded)
     */
    async getDefinitions(word) {
        if (this.cache.definitions.has(word)) {
            return this.cache.definitions.get(word);
        }

        await this.ensureDataLoaded('definitions');
        return this.cache.definitions.get(word) || null;
    }

    /**
     * Get etymologies for a word (lazy loaded)
     */
    async getEtymologies(word) {
        if (this.cache.etymologies.has(word)) {
            return this.cache.etymologies.get(word);
        }

        await this.ensureDataLoaded('etymologies');
        return this.cache.etymologies.get(word) || null;
    }

    /**
     * Get semantic relationships for a word (lazy loaded)
     */
    async getSemanticRelationships(word) {
        if (this.cache.semanticRelationships.has(word)) {
            return this.cache.semanticRelationships.get(word);
        }

        await this.ensureDataLoaded('semanticRelationships');
        return this.cache.semanticRelationships.get(word) || null;
    }

    /**
     * Get curated list memberships for a word (lazy loaded)
     */
    async getCuratedMemberships(word) {
        if (this.cache.curatedMemberships.has(word)) {
            return this.cache.curatedMemberships.get(word);
        }

        await this.ensureDataLoaded('curatedMemberships');
        return this.cache.curatedMemberships.get(word) || null;
    }

    /**
     * Get syllable count for a word (lazy loaded)
     */
    async getSyllableCount(word) {
        if (this.cache.syllableCounts.has(word)) {
            return this.cache.syllableCounts.get(word);
        }

        await this.ensureDataLoaded('syllableCounts');
        return this.cache.syllableCounts.get(word) || null;
    }

    /**
     * Get rhyming words for a word (lazy loaded)
     */
    async getRhymingWords(word, rhymeType = 'perfect') {
        await this.ensureDataLoaded('rhymeGroups');
        
        const rhymingWords = [];
        for (const [rhymeKey, words] of this.cache.rhymeGroups) {
            if (rhymeKey.startsWith(`${rhymeType}:`) && words.includes(word)) {
                // Return other words in the same rhyme group
                rhymingWords.push(...words.filter(w => w !== word));
                break;
            }
        }
        return rhymingWords;
    }

    /**
     * Get all rhyme groups containing a word
     */
    async getAllRhymeGroups(word) {
        await this.ensureDataLoaded('rhymeGroups');
        
        const groups = {};
        for (const [rhymeKey, words] of this.cache.rhymeGroups) {
            if (words.includes(word)) {
                const [type, pattern] = rhymeKey.split(':', 2);
                if (!groups[type]) groups[type] = [];
                groups[type].push({
                    pattern,
                    words: words.filter(w => w !== word)
                });
            }
        }
        return groups;
    }

    /**
     * Check if word belongs to specific curated list
     */
    async isInCuratedList(word, listName) {
        const memberships = await this.getCuratedMemberships(word);
        return memberships && memberships[listName] === true;
    }

    /**
     * Get words from specific curated list
     */
    async getWordsFromCuratedList(listName) {
        await this.ensureDataLoaded('curatedMemberships');
        
        const wordsInList = [];
        for (const [word, memberships] of this.cache.curatedMemberships) {
            if (memberships[listName] === true) {
                wordsInList.push(word);
            }
        }
        return wordsInList;
    }

    /**
     * Search words by pattern or criteria
     */
    searchWords(criteria) {
        if (!this.isInitialized) {
            throw new Error('DataManager not initialized');
        }

        const { 
            pattern, 
            minLength, 
            maxLength, 
            startsWith, 
            endsWith, 
            contains,
            limit = 1000 
        } = criteria;

        let results = this.cache.words;

        // Apply filters
        if (minLength) results = results.filter(w => w.length >= minLength);
        if (maxLength) results = results.filter(w => w.length <= maxLength);
        if (startsWith) results = results.filter(w => w.startsWith(startsWith.toLowerCase()));
        if (endsWith) results = results.filter(w => w.endsWith(endsWith.toLowerCase()));
        if (contains) results = results.filter(w => w.includes(contains.toLowerCase()));
        if (pattern) {
            const regex = new RegExp(pattern, 'i');
            results = results.filter(w => regex.test(w));
        }

        return results.slice(0, limit);
    }

    /**
     * Get random words with optional criteria
     */
    async getRandomWords(count = 10, criteria = {}) {
        let pool = this.getWords();
        
        // Apply criteria filters
        if (criteria.minLength) pool = pool.filter(w => w.length >= criteria.minLength);
        if (criteria.maxLength) pool = pool.filter(w => w.length <= criteria.maxLength);
        if (criteria.hasFrequency) {
            await this.ensureDataLoaded('frequencies');
            pool = pool.filter(w => this.cache.frequencies.has(w));
        }
        if (criteria.hasPronunciation) {
            await this.ensureDataLoaded('pronunciations');
            pool = pool.filter(w => this.cache.pronunciations.has(w));
        }
        if (criteria.curatedList) {
            const listWords = await this.getWordsFromCuratedList(criteria.curatedList);
            pool = pool.filter(w => listWords.includes(w));
        }

        // Shuffle and return random selection
        const shuffled = this.shuffleArray([...pool]);
        return shuffled.slice(0, count);
    }

    /**
     * Get all data for a plate (difficulty, solution count, etc.)
     */
    async getPlateData(plate) {
        if (!this.cache._plateData) {
            await this.loadPlateData();
        }
        return this.cache._plateData.get(plate.toUpperCase()) || null;
    }

    /**
     * Loads and processes the plate difficulty/metadata.
     */
    async loadPlateData() {
        if (this.cache._plateData) return;

        console.log('Loading plate data...');
        const rawData = await this.loadJSON('data/game_difficulty_data.json');
        
        const dataMap = new Map();
        for (const [level, plates] of Object.entries(rawData.difficulty_levels)) {
            const capitalizedLevel = level.charAt(0).toUpperCase() + level.slice(1);
            for (const plateInfo of plates) {
                dataMap.set(plateInfo.plate, { ...plateInfo, difficulty: capitalizedLevel });
            }
        }
        
        this.cache._plateData = dataMap;
        console.log(`Plate data loaded for ${this.cache._plateData.size} plates.`);
    }

    /**
     * Get statistics about the loaded data
     */
    getStats() {
        const stats = {
            totalWords: this.cache.words?.length || 0,
            loadedModules: []
        };

        if (this.cache.pronunciations.size > 0) stats.loadedModules.push('pronunciations');
        if (this.cache.frequencies.size > 0) stats.loadedModules.push('frequencies');
        if (this.cache.definitions.size > 0) stats.loadedModules.push('definitions');
        if (this.cache.etymologies.size > 0) stats.loadedModules.push('etymologies');
        if (this.cache.semanticRelationships.size > 0) stats.loadedModules.push('semanticRelationships');
        if (this.cache.curatedMemberships.size > 0) stats.loadedModules.push('curatedMemberships');
        if (this.cache.syllableCounts.size > 0) stats.loadedModules.push('syllableCounts');
        if (this.cache.rhymeGroups.size > 0) stats.loadedModules.push('rhymeGroups');

        return stats;
    }

    /**
     * Ensure specific data type is loaded (public method for analysis)
     */
    async ensureDataLoaded(dataType) {
        if (this.loadPromises.has(dataType)) {
            return this.loadPromises.get(dataType);
        }

        const promise = this.loadDataType(dataType);
        this.loadPromises.set(dataType, promise);
        return promise;
    }

    // Private methods

    async loadDataType(dataType) {
        const fileMap = {
            pronunciations: 'modular_data/pronunciations.json',
            frequencies: 'modular_data/frequencies.json',
            definitions: 'modular_data/definitions.json',
            etymologies: 'modular_data/etymologies.json',
            semanticRelationships: 'modular_data/semantic_relationships.json',
            curatedMemberships: 'modular_data/curated_list_memberships.json',
            syllableCounts: 'modular_data/derived/syllable_counts.json',
            rhymeGroups: 'modular_data/derived/rhyme_groups.json'
        };

        const filePath = fileMap[dataType];
        if (!filePath) {
            throw new Error(`Unknown data type: ${dataType}`);
        }

        try {
            console.log(`Loading ${dataType}...`);
            const data = await this.loadJSON(filePath);
            
            // Convert to Map for O(1) lookups
            const dataKey = this.getDataKey(dataType);
            const sourceData = data[dataKey];
            
            for (const [word, wordData] of Object.entries(sourceData)) {
                this.cache[dataType].set(word, wordData);
            }
            
            this.metadata[dataType] = data.metadata;
            console.log(`Loaded ${dataType}: ${this.cache[dataType].size} entries`);
            
        } catch (error) {
            console.error(`Failed to load ${dataType}:`, error);
            throw error;
        }
    }

    getDataKey(dataType) {
        const keyMap = {
            pronunciations: 'pronunciations',
            frequencies: 'frequencies',
            definitions: 'definitions',
            etymologies: 'etymologies',
            semanticRelationships: 'relationships',
            curatedMemberships: 'memberships',
            syllableCounts: 'syllable_counts',
            rhymeGroups: 'rhyme_groups'
        };
        return keyMap[dataType];
    }

    async loadJSON(filePath) {
        // Environment detection - use appropriate loading method
        if (typeof process !== 'undefined' && process.versions && process.versions.node) {
            // Node.js environment
            const fs = await import('fs');
            const path = await import('path');
            try {
                const fullPath = path.resolve(filePath);
                const data = fs.readFileSync(fullPath, 'utf8');
                return JSON.parse(data);
            } catch (error) {
                throw new Error(`Failed to load ${filePath}: ${error.message}`);
            }
        } else {
            // Browser environment
            const response = await fetch(filePath);
            if (!response.ok) {
                throw new Error(`Failed to load ${filePath}: ${response.statusText}`);
            }
            return response.json();
        }
    }

    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
}

// Export for use in other modules
export default DataManager; 