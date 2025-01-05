class PlateData {
    constructor() {
        this.combinations = new Map(); // Main storage: combination -> {combination, word_count, difficulty}
        this.difficultyIndex = new Map(); // Index by difficulty: difficulty -> Set of combinations
        this.usedPlates = new Set();
        this.loaded = false;
        this.plateScores = new Map(); // Track best scores: combination -> {score, rarestWord, isNewBest, previousBest}

        // Difficulty weights for random selection
        this.DIFFICULTY_WEIGHTS = {
            'Very Easy': 0.15,
            'Easy': 0.25,
            'Medium': 0.35,
            'Hard': 0.15,
            'Very Hard': 0.08,
            'Impossible': 0.02
        };
    }

    async loadData() {
        try {
            const response = await fetch('data/letter_combinations_with_possibilities_and_difficulties.jsonl');
            if (!response.ok) throw new Error('Network response was not ok');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let processedCombinations = 0;

            while (true) {
                const {value, done} = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\n');
                
                // Process all complete lines
                for (let i = 0; i < lines.length - 1; i++) {
                    if (lines[i].trim() === '') continue;
                    this.processLine(lines[i]);
                    processedCombinations++;
                }
                
                // Keep the last partial line in buffer
                buffer = lines[lines.length - 1];
            }

            // Process any remaining data
            if (buffer.trim()) {
                this.processLine(buffer);
                processedCombinations++;
            }

            this.loaded = true;
            console.log(`Loaded ${processedCombinations} plate combinations successfully`);
            return true;
        } catch (error) {
            console.error('Error loading plate data:', error);
            return false;
        }
    }

    processLine(line) {
        try {
            const data = JSON.parse(line);
            const { combination, word_count, difficulty } = data;

            // Store complete combination data
            this.combinations.set(combination, {
                combination,
                word_count,
                difficulty
            });
            
            // Index by difficulty for gameplay
            if (!this.difficultyIndex.has(difficulty)) {
                this.difficultyIndex.set(difficulty, new Set());
            }
            this.difficultyIndex.get(difficulty).add(combination);
        } catch (error) {
            console.warn('Error processing line:', error);
        }
    }

    // Get a random difficulty based on weights
    getRandomDifficulty() {
        const difficulties = Object.keys(this.DIFFICULTY_WEIGHTS);
        const weights = difficulties.map(d => this.DIFFICULTY_WEIGHTS[d]);
        const totalWeight = weights.reduce((a, b) => a + b, 0);
        let random = Math.random() * totalWeight;
        
        for (let i = 0; i < difficulties.length; i++) {
            random -= weights[i];
            if (random <= 0) {
                return difficulties[i];
            }
        }
        return difficulties[difficulties.length - 1];
    }

    // Generate a new plate
    generatePlate() {
        if (!this.loaded || this.combinations.size === 0) {
            console.warn('%c Plate combinations not loaded yet! Using default plate.', 'color: orange; font-weight: bold');
            return 'AAA';
        }

        // Get random difficulty using weights, but allow impossible plates to be generated
        const targetDifficulty = this.getRandomDifficulty();
        console.log(`%c Selected difficulty: ${targetDifficulty}`, 'color: blue');
        
        // Get available combinations for this difficulty
        const difficultyPlates = this.difficultyIndex.get(targetDifficulty);
        if (!difficultyPlates) return 'AAA';

        // Filter out used plates
        const availablePlates = Array.from(difficultyPlates)
            .filter(plate => !this.usedPlates.has(plate));

        // If no unused plates in this difficulty, reset used plates for this difficulty
        if (availablePlates.length === 0) {
            console.log(`%c Resetting used plates for difficulty: ${targetDifficulty}`, 'color: orange');
            difficultyPlates.forEach(plate => {
                this.usedPlates.delete(plate);
            });
            return this.generatePlate(); // Try again with reset plates
        }

        // Select random plate from available ones
        const randomIndex = Math.floor(Math.random() * availablePlates.length);
        const selectedPlate = availablePlates[randomIndex];
        const plateInfo = this.combinations.get(selectedPlate);
        
        // Mark as used
        this.usedPlates.add(selectedPlate);
        
        console.log(`%c Selected plate: ${plateInfo.combination} (${plateInfo.word_count} possible words)`, 'color: green; font-weight: bold');
        return plateInfo.combination;
    }

    // Reset used plates
    resetUsedPlates() {
        this.usedPlates.clear();
    }

    // Check if a word contains the plate letters in order
    isValidWithPlate(word, plate) {
        const regex = new RegExp(`^.*${plate[0]}.*${plate[1]}.*${plate[2]}.*$`, 'i');
        return regex.test(word);
    }

    // Utility methods
    isLoaded() {
        return this.loaded;
    }

    // Get plate info
    getPlate(combination) {
        return this.combinations.get(combination);
    }

    // Get plate difficulty
    getPlateDifficulty(combination) {
        const plateInfo = this.combinations.get(combination);
        if (!plateInfo) return null;
        
        // Return the normalized difficulty key
        return plateInfo.difficulty.toLowerCase().replace(/\s+/g, '');
    }

    // Statistics and metadata
    getStats() {
        const stats = {
            totalPlates: this.combinations.size,
            platesByDifficulty: {}
        };

        for (const [difficulty, plates] of this.difficultyIndex) {
            stats.platesByDifficulty[difficulty] = plates.size;
        }

        return stats;
    }

    // Score tracking methods
    updatePlateScore(plate, score, rarestWord) {
        const currentBest = this.plateScores.get(plate);
        const isNewBest = !currentBest || score > currentBest.score;
        const previousBest = currentBest?.score;
        
        // Always update the score to track latest attempt
        this.plateScores.set(plate, { 
            score, 
            rarestWord,
            previousBest, // Store the previous best score
            isNewBest    // Store whether this was a new best score
        });
        
        return {
            isNewBest,
            previousBest
        };
    }

    getPlateScore(plate) {
        return this.plateScores.get(plate);
    }
}

// Create and export singleton instance
const plateData = new PlateData();
export default plateData;
