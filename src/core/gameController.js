import wordData from '/PL8WRDS/src/data/wordData.js';
import plateData from '/PL8WRDS/src/data/plateData.js';
import hintData from '/PL8WRDS/src/data/hintData.js';
import scoreFactory from '/PL8WRDS/src/core/scoreFactory.js';
import gameState from '/PL8WRDS/src/core/gameState.js';
import uiManager from '/PL8WRDS/src/ui/uiManager.js';
import eventHandler from '/PL8WRDS/src/ui/eventHandler.js';
import statusManager from '/PL8WRDS/src/utils/statusManager.js';

class GameController {
    constructor() {
        this.loadingInterval = null;
    }

    async initialize() {
        console.log('%c PL8WRDS Initializing...', 'color: blue; font-weight: bold');

        // Show main menu first with loading state
        uiManager.showScreen('main-menu');

        // Initialize plate text animation after DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            const plateText = document.getElementById('plate-text');
            if (plateText) {
                plateText.classList.remove('start-plate');
                void plateText.offsetWidth;
                plateText.classList.add('start-plate');
            }
        });

        // Start initialization with loading animation
        this.startLoadingAnimation();

        try {
            // Load modules in parallel
            const [wordDataSuccess, plateDataSuccess, hintDataSuccess] = await Promise.all([
                wordData.loadData(),
                plateData.loadData(),
                hintData.loadData()
            ]);
            
            if (!wordDataSuccess) throw new Error('Failed to load word data');
            if (!plateDataSuccess) throw new Error('Failed to load plate data');
            if (!hintDataSuccess) throw new Error('Failed to load hint data');
            
            // Set game data ready and update UI
            gameState.gameDataReady = true;
            console.log('Game data ready for use');
            
            // Log statistics
            this.logGameStats();
            
            // Update input placeholder with actual word length limits
            const wordInput = document.getElementById('word-input');
            wordInput.placeholder = `Type a guess here...`;

            // Update loading status and enable play button
            const gameStatus = document.querySelector('.menu-screen .status-message');
            const playButton = document.querySelector('.menu-button[data-screen="game-screen"]');
            
            if (gameStatus) {
                statusManager.showMessage(gameStatus, 'Ready!');
            }
            if (playButton) {
                playButton.disabled = false;
            }

            // Load lifetime stats
            gameState.loadLifetimeStats();
            
            // Sync plateData scores with lifetimeStats
            gameState.lifetimeStats.topPlates.forEach((info, plate) => {
                plateData.plateScores.set(plate, {
                    score: info.score,
                    rarestWord: info.rarestWord,
                    previousBest: info.previousBest,
                    isNewBest: false // Reset isNewBest flag on load
                });
            });

            // Return true to indicate successful initialization
            return true;
            
        } catch (error) {
            console.error('Error initializing game:', error);
            throw error;
        } finally {
            this.stopLoadingAnimation();
        }
    }

    startLoadingAnimation() {
        const loadingDots = ['Loading', 'Loading.', 'Loading..', 'Loading...'];
        let loadingIndex = 0;
        this.loadingInterval = setInterval(() => {
            const gameStatus = document.querySelector('.menu-screen .status-message');
            if (gameStatus && !gameState.gameDataReady) {
                gameStatus.textContent = loadingDots[loadingIndex];
                loadingIndex = (loadingIndex + 1) % loadingDots.length;
            } else {
                this.stopLoadingAnimation();
            }
        }, 500);
    }

    stopLoadingAnimation() {
        if (this.loadingInterval) {
            clearInterval(this.loadingInterval);
            this.loadingInterval = null;
        }
    }

    logGameStats() {
        const wordStats = wordData.getStats();
        console.log('%c Word List Stats:', 'color: blue; font-weight: bold');
        console.table({
            'Total Words': wordStats.totalWords,
            'Min Length': Math.min(...wordStats.wordLengths),
            'Max Length': Math.max(...wordStats.wordLengths),
            'Frequency Ranges': wordStats.frequencyRanges.length
        });

        const plateStats = plateData.getStats();
        console.log('%c Plate Stats:', 'color: blue; font-weight: bold');
        console.table({
            'Total Plates': plateStats.totalPlates,
            'By Difficulty': plateStats.platesByDifficulty
        });
        
        console.log('%c Game data ready for use', 'color: green; font-weight: bold');
    }
}

// Create and export singleton instance
const gameController = new GameController();
export default gameController;
