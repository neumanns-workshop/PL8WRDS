// Score calculation and tracking
export default {
    // Get bonus value based on standardized frequency ranges
    getWordBonus(frequency) {

        // Map frequency ranges directly to bonus values
        if (frequency > 0.01) return 0.0;          // Ultra Common (e.g. "the")
        if (frequency > 0.001) return 0.05;         // Very Common (e.g. "man")
        if (frequency > 0.0001) return 0.10;        // Common (e.g. "happy")
        if (frequency > 0.00001) return 0.25;       // Moderately Common (e.g. "hypothesis")
        if (frequency > 0.000001) return 0.50;      // Uncommon (e.g. "orchard")
        if (frequency > 0.0000001) return 0.75;     // Rare (e.g. "zeugma")
        return 1.0;                                // Very Rare (e.g. "absquatulate")
    },

    // Calculate plate multiplier by summing bonuses from all words
    getBestMultiplier(words, wordData) {
        // Start with base 1.0x multiplier
        let plateMultiplier = 1.0;
        
        // Track which words we've counted to avoid duplicates
        const countedWords = new Set();
        
        words.forEach(word => {
            // Skip if we've already counted this word's bonus
            if (countedWords.has(word)) return;
            
            const wordInfo = wordData.getWord(word);
            if (wordInfo) {
                // Add this word's bonus to the plate total
                plateMultiplier += this.getWordBonus(wordInfo.frequency);
                // Mark word as counted
                countedWords.add(word);
            }
        });
        
        return plateMultiplier;
    },

    // Calculate final score for a plate
    getPlateScore(basePoints, comboPoints, words, wordData) {
        const subtotal = basePoints + comboPoints;
        const multiplier = this.getBestMultiplier(words, wordData);
        return {
            score: Math.floor(subtotal * multiplier),
            multiplier: multiplier
        };
    }
};
