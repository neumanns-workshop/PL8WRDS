import plateData from '../data/plateData.js';

class GameState {
    constructor() {
        this.resetState();
        this.loadLifetimeStats();
    }

    resetState() {
        // Core game state
        this.currentWord = '';
        this.score = 0;
        this.basePoints = 0;
        this.timeLeft = 90;
        this.gameActive = false;
        this.currentPlate = '';
        this.gameDataReady = false;

        // Screen state
        this.currentScreen = 'main-menu';

        // Tracking sets
        this.usedWords = new Set();
        this.rareWords = new Set();
        this.seenPlates = new Set();

        // Game stats tracking
        this.maxBase = 0;
        this.maxMultiplier = 1;
        this.maxCombo = 0;

        // Combo tracking
        this.comboPoints = 0;
        this.combo = 0;
        this.maxComboPoints = 0;

        // Rare word tracking by difficulty
        this.rarestWordsByDifficulty = {
            veryeasy: { word: '', frequency: Infinity },
            easy: { word: '', frequency: Infinity },
            medium: { word: '', frequency: Infinity },
            hard: { word: '', frequency: Infinity },
            veryhard: { word: '', frequency: Infinity },
            impossible: { word: '', frequency: Infinity }
        };
    }

    // Lifetime stats management
    loadLifetimeStats() {
        const savedStats = localStorage.getItem('pl8wrds_stats');
        if (savedStats) {
            const parsed = JSON.parse(savedStats);
            this.lifetimeStats = {
                gamesPlayed: parsed.gamesPlayed || 0,
                totalScore: parsed.totalScore || 0,
                bestScore: parsed.bestScore || 0,
                uniquePlates: new Set(parsed.uniquePlates || []),
                bestCombo: parsed.bestCombo || 0,
                bestMultiplier: parsed.bestMultiplier || 1,
                topPlates: new Map(Array.isArray(parsed.topPlates) ? parsed.topPlates.map(([plate, info]) => [
                    plate,
                    {
                        ...info,
                        isNewBest: false,
                        previousBest: info.score
                    }
                ]) : []),
                scoreHistory: Array.isArray(parsed.scoreHistory) ? parsed.scoreHistory : [],
                hiddenRares: new Map(Array.isArray(parsed.hiddenRares) ? parsed.hiddenRares : [])
            };
        } else {
            this.resetLifetimeStats();
        }
    }

    resetLifetimeStats() {
        this.lifetimeStats = {
            gamesPlayed: 0,
            totalScore: 0,
            bestScore: 0,
            uniquePlates: new Set(),
            bestCombo: 0,
            bestMultiplier: 1,
            topPlates: new Map(),
            scoreHistory: [],
            hiddenRares: new Map()
        };
        localStorage.removeItem('pl8wrds_stats');
    }

    saveLifetimeStats() {
        const serialized = {
            gamesPlayed: this.lifetimeStats.gamesPlayed,
            totalScore: this.lifetimeStats.totalScore,
            bestScore: this.lifetimeStats.bestScore,
            uniquePlates: Array.from(this.lifetimeStats.uniquePlates),
            bestCombo: this.lifetimeStats.bestCombo,
            bestMultiplier: this.lifetimeStats.bestMultiplier,
            topPlates: Array.from(this.lifetimeStats.topPlates),
            scoreHistory: this.lifetimeStats.scoreHistory,
            hiddenRares: Array.from(this.lifetimeStats.hiddenRares)
        };
        localStorage.setItem('pl8wrds_stats', JSON.stringify(serialized));
    }

    // Game state updates
    updateScore(plateScore) {
        this.score += plateScore;
        if (plateScore > 0) {
            this.seenPlates.add(this.currentPlate);
        }
    }

    updateCombo() {
        this.combo++;
        if (this.combo > 1) {
            this.comboPoints += this.combo;
        }
        this.maxCombo = Math.max(this.maxCombo, this.combo);
    }

    updateMultiplier(multiplier) {
        this.maxMultiplier = Math.max(this.maxMultiplier, multiplier);
    }

    resetCombo() {
        if (this.comboPoints > 0) {
            this.maxComboPoints += this.comboPoints;
        }
        this.combo = 0;
        this.comboPoints = 0;
    }

    addUsedWord(word, wordInfo) {
        this.usedWords.add(word);
        if (wordInfo.frequency === 0.0) {
            this.rareWords.add(word);
            this.updateRarestWord(word, wordInfo);
        }
        this.basePoints += 10;
        this.maxBase = Math.max(this.maxBase, this.basePoints);
    }

    updateRarestWord(word, wordInfo) {
        const difficulty = this.getCurrentPlateDifficulty();
        if (difficulty && wordInfo.frequency === 0.0) {
            // Update per-game tracking
            if (!this.rarestWordsByDifficulty[difficulty].word || 
                this.rarestWordsByDifficulty[difficulty].frequency !== 0.0) {
                this.rarestWordsByDifficulty[difficulty] = {
                    word: word,
                    frequency: wordInfo.frequency
                };
            }

            // Update lifetime hidden rares - add all rare words we find
            let raresList = this.lifetimeStats.hiddenRares.get(difficulty);
            
            // Initialize or convert to array format
            if (!raresList || !Array.isArray(raresList)) {
                // Convert old format to array if it exists
                const oldRare = raresList?.word ? [{
                    word: raresList.word,
                    frequency: raresList.frequency
                }] : [];
                raresList = oldRare;
                this.lifetimeStats.hiddenRares.set(difficulty, raresList);
            }
            
            // Add new rare word if not already present
            if (!raresList.some(rare => rare.word === word)) {
                raresList.push({
                    word: word,
                    frequency: wordInfo.frequency
                });
                this.saveLifetimeStats();
            }
        }
    }

    // Game state queries
    isWordUsed(word) {
        return this.usedWords.has(word);
    }

    getCurrentPlateDifficulty() {
        return plateData?.getPlateDifficulty(this.currentPlate);
    }

    // Screen management
    setCurrentScreen(screenId) {
        this.currentScreen = screenId;
    }

    // End game updates
    updateLifetimeStats() {
        this.lifetimeStats.gamesPlayed++;
        this.lifetimeStats.totalScore += this.score;
        this.lifetimeStats.bestScore = Math.max(this.lifetimeStats.bestScore, this.score);
        this.lifetimeStats.bestCombo = Math.max(this.lifetimeStats.bestCombo, this.maxCombo);
        this.lifetimeStats.bestMultiplier = Math.max(this.lifetimeStats.bestMultiplier, this.maxMultiplier);
        this.lifetimeStats.scoreHistory.push(this.score);
        
        // Update plates tracking
        this.seenPlates.forEach(plate => {
            // Add to unique plates
            this.lifetimeStats.uniquePlates.add(plate);

            // Update top plates
            const plateScore = plateData.getPlateScore(plate);
            if (plateScore) {
                const plateInfo = plateData.getPlate(plate);
                this.lifetimeStats.topPlates.set(plate, {
                    score: plateScore.score,
                    difficulty: plateInfo.difficulty,
                    rarestWord: plateScore.rarestWord,
                    isNewBest: plateScore.isNewBest,
                    previousBest: plateScore.previousBest
                });
            }
        });

        this.saveLifetimeStats();
    }
}

// Create and export singleton instance
const gameState = new GameState();
export default gameState;
