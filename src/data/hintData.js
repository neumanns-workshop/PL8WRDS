class HintData {
    constructor() {
        this.loaded = false;
        this.HINT_TYPES = {
            LEXICAL: 'lexical',
            SEMANTIC: 'semantic',
            PHONETIC: 'phonetic'
        };
    }

    async loadData() {
        this.loaded = true;
        return true;
    }

    // Get a random hint type with equal probability
    getRandomHintType() {
        const types = Object.values(this.HINT_TYPES);
        return types[Math.floor(Math.random() * types.length)];
    }

    // Count rare words for a plate
    countRareWords(possibleWords, wordData) {
        const rareWords = possibleWords.filter(word => {
            const wordInfo = wordData.getWord(word);
            return !wordInfo.is_lemmatized && wordInfo.frequency === 0;
        });
        
        if (rareWords.length > 0) {
            console.log('%c Example rare word:', 'color: purple; font-weight: bold', {
                'word': rareWords[0],
                'definition': wordData.getWord(rareWords[0]).definitions[0]
            });
        }
        
        return rareWords.length;
    }

    // Generate a lexical hint (coverage percentage, difficulty, or rare word count)
    generateLexicalHint(possibleWords, totalWords, plateInfo, wordData) {
        const random = Math.random();
        if (random < 0.33) {
            const percentage = ((possibleWords.length / totalWords) * 100).toFixed(2);
            return `Coverage: ${percentage}%`;
        } else if (random < 0.67) {
            return `Difficulty: ${plateInfo.difficulty}`;
        } else {
            const rareCount = this.countRareWords(possibleWords, wordData);
            return rareCount > 0 ? `Rare words: ${rareCount}` : `Rare words: 0`;
        }
    }

    // Generate a semantic hint (definition or synonym)
    generateSemanticHint(possibleWords, wordData, plateRegex) {
        let bestHint = null;
        let bestLength = Infinity;
        
        // Try up to 5 random words
        for (let i = 0; i < 5; i++) {
            const randomWord = possibleWords[Math.floor(Math.random() * possibleWords.length)];
            const wordInfo = wordData.getWord(randomWord);
            
            // Check definition
            if (wordInfo.definitions?.length > 0) {
                const def = wordInfo.definitions[0];
                if (def.length < bestLength && def.length <= 60) {
                    bestHint = def;
                    bestLength = def.length;
                }
            }
            
            // Check synonym - ensure it doesn't match the plate pattern
            if (wordInfo.synonyms?.length > 0) {
                for (const syn of wordInfo.synonyms) {
                    if (syn.length <= 20 && syn.length < bestLength && !plateRegex.test(syn)) {
                        bestHint = `Related: ${syn}`;
                        bestLength = syn.length;
                        break;
                    }
                }
            }
        }
        
        return bestHint;
    }

    // Generate a phonetic hint (rhyming word)
    generatePhoneticHint(possibleWords, wordData, plateRegex) {
        let bestRhyme = null;
        let bestLength = Infinity;
        
        // Try up to 5 random words
        for (let i = 0; i < 5; i++) {
            const randomWord = possibleWords[Math.floor(Math.random() * possibleWords.length)];
            const wordInfo = wordData.getWord(randomWord);
            
            if (wordInfo.rhyming_words?.length > 0) {
                for (const rhyme of wordInfo.rhyming_words) {
                    if (rhyme.length <= 20 && rhyme.length < bestLength && !plateRegex.test(rhyme)) {
                        bestRhyme = rhyme;
                        bestLength = rhyme.length;
                        break;
                    }
                }
            }
        }
        
        return bestRhyme ? `♪ ${bestRhyme} ♪` : null;
    }

    // Main hint generation function
    generateHint(plate, possibleWords, wordData, plateData) {
        if (!this.loaded || !wordData || !plateData) {
            console.log('Cannot generate hint - missing data');
            return null;
        }

        if (possibleWords.length === 0) return null;

        const plateInfo = plateData.getPlate(plate);
        if (!plateInfo) return null;

        const plateRegex = new RegExp(`^.*${plate[0]}.*${plate[1]}.*${plate[2]}.*$`, 'i');
        const totalWords = wordData.words.size;
        const hintType = this.getRandomHintType();

        switch (hintType) {
            case this.HINT_TYPES.LEXICAL:
                return this.generateLexicalHint(possibleWords, totalWords, plateInfo, wordData);

            case this.HINT_TYPES.SEMANTIC: {
                const hint = this.generateSemanticHint(possibleWords, wordData, plateRegex);
                if (hint) return hint;
                // Fallback to lexical hint if no semantic hint found
                return this.generateLexicalHint(possibleWords, totalWords, plateInfo, wordData);
            }

            case this.HINT_TYPES.PHONETIC: {
                const hint = this.generatePhoneticHint(possibleWords, wordData, plateRegex);
                if (hint) return hint;
                // Fallback to lexical hint if no phonetic hint found
                return this.generateLexicalHint(possibleWords, totalWords, plateInfo, wordData);
            }
        }
    }

    // Get possible words for a plate
    getPossibleWords(plate, wordData, usedWords) {
        const regex = new RegExp(`^.*${plate[0]}.*${plate[1]}.*${plate[2]}.*$`, 'i');
        return Array.from(wordData.words.keys())
            .filter(word => regex.test(word) && !usedWords.has(word));
    }
}

// Create and export singleton instance
const hintData = new HintData();
export default hintData;
