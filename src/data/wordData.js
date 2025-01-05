class WordData {
    constructor() {
        this.words = new Map(); // Main word storage: word -> {word, word_length, frequency, definitions, etc}
        this.lengthIndex = new Map(); // Index by length: length -> Set of words
        this.loaded = false;
    }

    async loadData() {
        try {
            const response = await fetch('data/wordlist_v1.jsonl');
            if (!response.ok) throw new Error('Network response was not ok');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let processedWords = 0;
            const loadingStatus = document.getElementById('loading-status');

            while (true) {
                const {value, done} = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\n');
                
                // Process all complete lines
                for (let i = 0; i < lines.length - 1; i++) {
                    if (lines[i].trim() === '') continue;
                    this.processLine(lines[i]);
                    processedWords++;
                    
                    // Update loading status every 1000 words
                    if (processedWords % 1000 === 0 && loadingStatus) {
                        loadingStatus.textContent = `Loading word data... (${processedWords} words)`;
                    }
                }
                
                // Keep the last partial line in buffer
                buffer = lines[lines.length - 1];
            }

            // Process any remaining data
            if (buffer.trim()) {
                this.processLine(buffer);
                processedWords++;
            }

            if (loadingStatus) {
                loadingStatus.textContent = `Loaded ${processedWords} words successfully`;
            }

            this.loaded = true;
            console.log(`Loaded ${processedWords} words successfully`);
            return true;
        } catch (error) {
            console.error('Error loading word data:', error);
            return false;
        }
    }

    processLine(line) {
        try {
            const data = JSON.parse(line);
            const {
                word,
                word_length,
                frequency,
                definitions,
                synonyms,
                rhyming_words
            } = data;

            // Store complete word data
            this.words.set(word, {
                word,
                word_length,
                frequency,
                definitions,
                synonyms,
                rhyming_words
            });
            
            // Index by length for gameplay
            if (!this.lengthIndex.has(word_length)) {
                this.lengthIndex.set(word_length, new Set());
            }
            this.lengthIndex.get(word_length).add(word);
        } catch (error) {
            console.warn('Error processing line:', error);
        }
    }

    // Core word lookup
    getWord(word) {
        const lowercaseWord = word.toLowerCase();
        return this.words.get(lowercaseWord);
    }

    // Length-based queries
    getWordsByLength(length) {
        const words = this.lengthIndex.get(length);
        if (!words) return [];
        return Array.from(words).map(word => this.words.get(word));
    }

    // Advanced search with multiple criteria
    searchWords(criteria = {}) {
        const results = [];
        for (const wordData of this.words.values()) {
            if (this.matchesCriteria(wordData, criteria)) {
                results.push(wordData);
            }
            // Limit results for performance
            if (results.length >= 100) break;
        }
        return results;
    }

    matchesCriteria(wordData, criteria) {
        for (const [key, value] of Object.entries(criteria)) {
            if (!wordData.hasOwnProperty(key)) return false;
            
            if (Array.isArray(wordData[key])) {
                // For arrays (definitions, synonyms, rhyming_words)
                if (Array.isArray(value)) {
                    // If criteria is array, check if any value matches
                    if (!value.some(v => wordData[key].includes(v))) return false;
                } else {
                    // If criteria is single value, check if it exists in array
                    if (!wordData[key].includes(value)) return false;
                }
            } else if (typeof value === 'object' && value !== null) {
                // For range queries on numeric values
                if (value.min !== undefined && wordData[key] < value.min) return false;
                if (value.max !== undefined && wordData[key] > value.max) return false;
            } else {
                // Direct comparison for primitive values
                if (wordData[key] !== value) return false;
            }
        }
        return true;
    }

    // Utility methods
    isLoaded() {
        return this.loaded;
    }

    getRandomWord(length) {
        const words = this.lengthIndex.get(length);
        if (!words || words.size === 0) return null;
        const randomIndex = Math.floor(Math.random() * words.size);
        const word = Array.from(words)[randomIndex];
        return this.words.get(word);
    }

    // Word length constraints
    getMinWordLength() {
        return Math.min(...this.lengthIndex.keys());
    }

    getMaxWordLength() {
        return Math.max(...this.lengthIndex.keys());
    }

    // Statistics and metadata
    getStats() {
        // Calculate frequency ranges from word data
        const frequencies = new Set();
        for (const wordData of this.words.values()) {
            frequencies.add(Math.floor(wordData.frequency * 10) / 10);
        }
        
        return {
            totalWords: this.words.size,
            minLength: this.getMinWordLength(),
            maxLength: this.getMaxWordLength(),
            wordLengths: Array.from(this.lengthIndex.keys()).sort((a, b) => a - b),
            frequencyRanges: Array.from(frequencies).sort((a, b) => b - a)
        };
    }
}

// Create and export singleton instance
const wordData = new WordData();
export default wordData;
