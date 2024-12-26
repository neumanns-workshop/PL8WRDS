import gameState from '/PL8WRDS/src/core/gameState.js';
import uiManager from '/PL8WRDS/src/ui/uiManager.js';
import statusManager from '/PL8WRDS/src/utils/statusManager.js';
import wordData from '/PL8WRDS/src/data/wordData.js';
import plateData from '/PL8WRDS/src/data/plateData.js';
import scoreFactory from '/PL8WRDS/src/core/scoreFactory.js';
import hintData from '/PL8WRDS/src/data/hintData.js';

class EventHandler {
    constructor() {
        this.timer = null;
        this.hintTimer = null;
        this.loadingInterval = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Keyboard input handling
        document.addEventListener('keydown', this.handleKeydown.bind(this));

        // Menu navigation
        document.querySelectorAll('.menu-button').forEach(button => {
            button.addEventListener('click', () => {
                const targetScreen = button.getAttribute('data-screen');
                if (this.timer) {
                    clearInterval(this.timer);
                    this.timer = null;
                }
                if (this.hintTimer) {
                    clearInterval(this.hintTimer);
                    this.hintTimer = null;
                }
                gameState.gameActive = false;
                uiManager.showScreen(targetScreen);
            });
        });

        // Title click handler
        document.querySelector('.title')?.addEventListener('click', () => {
            if (this.timer) {
                clearInterval(this.timer);
                this.timer = null;
            }
            if (this.hintTimer) {
                clearInterval(this.hintTimer);
                this.hintTimer = null;
            }
            if (gameState.currentScreen === 'game-screen') {
                this.clearGameState();
            }
            gameState.gameActive = false;
            uiManager.showScreen('main-menu');
        });

        // Stats reset handler
        document.getElementById('reset-stats')?.addEventListener('click', () => {
            if (confirm('Are you sure you want to reset all stats? This cannot be undone.')) {
                gameState.resetLifetimeStats();
                uiManager.updateStatsDisplay(gameState.lifetimeStats);
                const gameStatus = document.querySelector('.stats-screen .status-message');
                statusManager.showMessage(gameStatus, 'Stats reset successfully!');
            }
        });

        // About screen carousel
        this.setupAboutCarousel();
    }

    handleKeydown(event) {
        // Always prevent default browser behavior for game controls
        if (['Space', 'Enter', 'Backspace'].includes(event.code) ||
            (event.key.length === 1 && event.key.match(/[a-zA-Z]/))) {
            event.preventDefault();
        }

        // Handle Space key specially since it can start the game
        if (event.code === 'Space') {
            this.handleSpaceKey();
            return;
        }

        // For all other keys, check if game is active
        if (!gameState.gameActive) {
            console.log('Game not active, ignoring input:', event.code);
            return;
        }

        switch (event.code) {
            case 'Enter':
                this.submitWord();
                break;
            case 'Backspace':
                gameState.currentWord = gameState.currentWord.slice(0, -1);
                uiManager.updateWordDisplay(gameState.currentWord);
                break;
            default:
                if (event.key.length === 1 && event.key.match(/[a-zA-Z]/)) {
                    if (wordData && gameState.currentWord.length < wordData.getMaxWordLength()) {
                        gameState.currentWord += event.key.toUpperCase();
                        uiManager.updateWordDisplay(gameState.currentWord);
                    }
                }
        }
    }

    handleSpaceKey() {
        console.log('handleSpaceKey called', {
            currentScreen: gameState.currentScreen,
            gameDataReady: gameState.gameDataReady,
            gameActive: gameState.gameActive
        });

        // Only handle Space key on game screen
        if (gameState.currentScreen !== 'game-screen') {
            console.log('Not on game screen');
            return;
        }

        // Check if game data is ready
        if (!gameState.gameDataReady) {
            console.log('Game data not ready yet');
            const gameStatus = document.querySelector('.game-screen .status-message');
            if (gameStatus) {
                statusManager.showMessage(gameStatus, 'Loading game data...');
            }
            return;
        }

        console.log('Starting game...');

        // Handle active game state
        if (gameState.gameActive) {
            console.log('Game already active, changing plate');
            this.handleActivePlateChange();
        }

        // Generate and display new plate
        gameState.currentPlate = plateData.generatePlate();
        uiManager.updatePlateDisplay(gameState.currentPlate);

        // Set game active and start/restart timer
        gameState.gameActive = true;
        if (this.timer) clearInterval(this.timer);
        this.timer = setInterval(this.updateTimer.bind(this), 1000);
        uiManager.updateInputState(true);

        // Reset plate-specific state
        this.resetPlateState();
        
        // Start hint cycle
        this.startHintCycle();
    }

    handleActivePlateChange() {
        const gameStatus = document.querySelector('.game-screen .status-message');
        
        // Bank any remaining combo points
        if (gameState.comboPoints > 0) {
            gameState.maxComboPoints += gameState.comboPoints;
            statusManager.showMessage(gameStatus, `+${gameState.comboPoints} combo points banked! (Total: ${gameState.maxComboPoints})`);
            gameState.comboPoints = 0;
        }

        // Calculate final plate score
        const { score: plateScore, multiplier } = scoreFactory.getPlateScore(
            gameState.basePoints, 
            gameState.maxComboPoints, 
            Array.from(gameState.usedWords), 
            wordData
        );
        gameState.updateMultiplier(multiplier);
        
        // Get rarest word for this plate
        const rarestWord = Array.from(gameState.rareWords)
            .sort((a, b) => {
                const freqA = wordData.getWord(a).frequency;
                const freqB = wordData.getWord(b).frequency;
                return freqA - freqB;
            })[0] || '';

        // Update plate score
        plateData.updatePlateScore(gameState.currentPlate, plateScore, rarestWord);
        gameState.updateScore(plateScore);
        
        // Show score message
        statusManager.showMessage(gameStatus, `+${plateScore} points from plate!`);
    }

    resetPlateState() {
        gameState.basePoints = 0;
        gameState.combo = 0;
        gameState.comboPoints = 0;
        gameState.maxComboPoints = 0;
        gameState.rareWords.clear();
        gameState.usedWords.clear();
        
        uiManager.clearComboWords();
        
        // Reset all score displays
        document.getElementById('base-points').textContent = '0';
        document.getElementById('combo').textContent = '';
        document.getElementById('multiplier').textContent = '';
        uiManager.updateScoreDisplays(
            gameState.score,
            gameState.basePoints,
            gameState.comboPoints,
            gameState.maxComboPoints,
            1.0
        );

        // Clear any existing hints/messages
        const gameStatus = document.querySelector('.game-screen .status-message');
        statusManager.clearMessages(gameStatus);
    }

    submitWord() {
        if (!gameState.gameActive) {
            console.warn('%c Cannot submit word - game not active', 'color: orange');
            return;
        }

        const gameStatus = document.querySelector('.game-screen .status-message');
        const word = gameState.currentWord.toLowerCase();

        // Validate word
        if (!this.validateWord(word, gameStatus)) {
            gameState.currentWord = '';
            uiManager.updateWordDisplay(gameState.currentWord);
            return;
        }

        // Word is valid - process it
        const wordInfo = wordData.getWord(word);
        gameState.addUsedWord(word, wordInfo);
        gameState.updateCombo();
        uiManager.updateComboWords(word, wordInfo.frequency === 0.0);

        // Update displays
        const { multiplier } = scoreFactory.getPlateScore(
            gameState.basePoints,
            gameState.comboPoints,
            Array.from(gameState.usedWords),
            wordData
        );
        gameState.updateMultiplier(multiplier);
        
        uiManager.updateScoreDisplays(
            gameState.score,
            gameState.basePoints,
            gameState.comboPoints,
            gameState.maxComboPoints,
            multiplier
        );
        
        uiManager.showScorePopup(10);
        
        // Calculate current score preview
        const { score: previewScore } = scoreFactory.getPlateScore(
            gameState.basePoints,
            gameState.comboPoints,
            Array.from(gameState.usedWords),
            wordData
        );
        statusManager.showMessage(gameStatus, `Current Score: ${previewScore}`);
        
        gameState.currentWord = '';
        uiManager.updateWordDisplay(gameState.currentWord);
    }

    validateWord(word, gameStatus) {
        // Check minimum length
        if (!wordData || word.length < wordData.getMinWordLength()) {
            statusManager.showMessage(gameStatus, `Word too short (minimum ${wordData?.getMinWordLength()} letters)`);
            this.handleComboLost();
            return false;
        }

        // Check if word exists
        const wordInfo = wordData.getWord(word);
        if (!wordInfo) {
            statusManager.showMessage(gameStatus, 'Word not found');
            this.handleComboLost();
            return false;
        }

        // Check if word contains plate letters
        if (!plateData.isValidWithPlate(word, gameState.currentPlate)) {
            statusManager.showMessage(gameStatus, `Must use letters ${gameState.currentPlate} in order`);
            this.handleComboLost();
            return false;
        }

        // Check if word has been used
        if (gameState.isWordUsed(word)) {
            statusManager.showMessage(gameStatus, 'Word already used');
            this.handleComboLost();
            return false;
        }

        return true;
    }

    handleComboLost() {
        if (gameState.combo > 0) {
            const gameStatus = document.querySelector('.game-screen .status-message');
            
            gameState.resetCombo();
            uiManager.clearComboWords();
            
            // Update displays
            const { multiplier } = scoreFactory.getPlateScore(
                gameState.basePoints,
                gameState.maxComboPoints,
                Array.from(gameState.usedWords),
                wordData
            );
            gameState.updateMultiplier(multiplier);
            
            uiManager.updateScoreDisplays(
                gameState.score,
                gameState.basePoints,
                gameState.comboPoints,
                gameState.maxComboPoints,
                multiplier
            );
            
            statusManager.showMessage(gameStatus, 'Combo lost!');
        }
    }

    updateTimer() {
        if (gameState.currentScreen !== 'game-screen') return;
        
        if (gameState.timeLeft < 0) {
            this.endGame();
            return;
        }
        
        uiManager.updateTimer(gameState.timeLeft);
        gameState.timeLeft--;
    }

    startHintCycle() {
        if (this.hintTimer) {
            clearInterval(this.hintTimer);
            this.hintTimer = null;
        }
        
        if (!gameState.gameActive) return;
        
        // Show initial hint after a delay
        setTimeout(() => {
            if (gameState.gameActive) {
                const initialHint = this.getNextHint();
                this.showHint(initialHint);
            }
        }, 2000);
        
        // Cycle through different hints periodically
        this.hintTimer = setInterval(() => {
            if (gameState.gameActive) {
                const nextHint = this.getNextHint();
                this.showHint(nextHint);
            } else {
                clearInterval(this.hintTimer);
                this.hintTimer = null;
            }
        }, 6000);
    }

    getNextHint() {
        if (!gameState.currentPlate || !wordData || !plateData || !hintData) {
            console.log('Cannot generate hint - missing data');
            return null;
        }
        
        const possibleWords = hintData.getPossibleWords(
            gameState.currentPlate,
            wordData,
            gameState.usedWords
        );
        
        return hintData.generateHint(
            gameState.currentPlate,
            possibleWords,
            wordData,
            plateData
        );
    }

    showHint(message) {
        if (!message || !gameState.gameActive) return;

        const activeScreen = document.querySelector('.screen.active, .menu-screen.active');
        if (!activeScreen) return;
        
        const gameStatus = activeScreen.querySelector('.status-message');
        if (!gameStatus) return;

        statusManager.showMessage(gameStatus, message);
    }

    endGame() {
        // Handle any remaining combo points
        if (gameState.comboPoints > 0) {
            gameState.maxComboPoints += gameState.comboPoints;
            gameState.comboPoints = 0;
        }

        // Calculate final plate score if needed
        if (gameState.basePoints > 0 || gameState.usedWords.size > 0) {
            const { score: plateScore, multiplier } = scoreFactory.getPlateScore(
                gameState.basePoints,
                gameState.maxComboPoints,
                Array.from(gameState.usedWords),
                wordData
            );
            gameState.updateMultiplier(multiplier);
            
            const rarestWord = Array.from(gameState.rareWords)
                .sort((a, b) => {
                    const freqA = wordData.getWord(a).frequency;
                    const freqB = wordData.getWord(b).frequency;
                    return freqA - freqB;
                })[0] || '';

            plateData.updatePlateScore(gameState.currentPlate, plateScore, rarestWord);
            gameState.updateScore(plateScore);
        }

        // Update lifetime stats
        gameState.updateLifetimeStats();
        
        // Show game over screen
        uiManager.showGameOver(gameState, plateData);
        
        // Clear game state
        this.clearGameState();
    }

    clearGameState() {
        // Clear timers
        if (this.timer) clearInterval(this.timer);
        if (this.hintTimer) clearInterval(this.hintTimer);
        this.timer = null;
        this.hintTimer = null;
        
        // Clear any existing messages
        const gameStatus = document.querySelector('.game-screen .status-message');
        if (gameStatus) {
            statusManager.clearMessages(gameStatus);
        }
        
        // Store current values
        const wasDataReady = gameState.gameDataReady;
        const currentScreen = gameState.currentScreen;
        
        // Reset game state
        gameState.resetState();
        
        // Restore values that shouldn't be reset
        gameState.gameDataReady = wasDataReady;
        gameState.currentScreen = currentScreen;
        
        uiManager.updateInputState(false);
        
        // Reset plate display
        uiManager.updatePlateDisplay();
        uiManager.clearComboWords();
        
        // Reset score displays
        uiManager.updateScoreDisplays(0, 0, 0, 0, 1.0);
    }

    setupAboutCarousel() {
        const slides = ['gameplay', 'example', 'controls', 'scoring', 'credits'];
        let currentSlideIndex = 0;

        document.querySelectorAll('.label').forEach((label, index) => {
            label.addEventListener('click', () => {
                currentSlideIndex = index;
                this.updateCarousel(currentSlideIndex, slides);
            });
        });

        document.querySelector('.about-screen .carousel-arrow.left')?.addEventListener('click', () => {
            currentSlideIndex = (currentSlideIndex - 1 + slides.length) % slides.length;
            this.updateCarousel(currentSlideIndex, slides);
        });

        document.querySelector('.about-screen .carousel-arrow.right')?.addEventListener('click', () => {
            currentSlideIndex = (currentSlideIndex + 1) % slides.length;
            this.updateCarousel(currentSlideIndex, slides);
        });
    }

    updateCarousel(currentSlideIndex, slides) {
        const allSlides = document.querySelectorAll('.carousel-slide');
        const allLabels = document.querySelectorAll('.label');
        
        // Update slides
        allSlides.forEach((slide, index) => {
            slide.classList.remove('active', 'prev', 'next');
            const position = (index - currentSlideIndex + slides.length) % slides.length;
            if (position === 0) {
                slide.classList.add('active');
            } else if (position === slides.length - 1) {
                slide.classList.add('prev');
            } else if (position === 1) {
                slide.classList.add('next');
            }
        });
        
        // Update labels
        allLabels.forEach((label, index) => {
            label.classList.remove('active', 'prev', 'next');
            const position = (index - currentSlideIndex + slides.length) % slides.length;
            if (position === 0) {
                label.classList.add('active');
            } else if (position === slides.length - 1) {
                label.classList.add('prev');
            } else if (position === 1) {
                label.classList.add('next');
            }
        });
    }
}

// Create and export singleton instance
const eventHandler = new EventHandler();
export default eventHandler;
