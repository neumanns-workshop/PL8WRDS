import BaseScreen from './BaseScreen.js';
import gameState from '../../core/gameState.js';
import statusManager from '../../utils/statusManager.js';

export default class GameScreen extends BaseScreen {
    constructor() {
        super('game-screen');
        this.wordInput = document.getElementById('word-input');
        this.scoreDisplay = document.getElementById('score');
        this.timeDisplay = document.getElementById('time');
        this.plateText = document.getElementById('plate-text');
        this.basePointsDisplay = document.getElementById('base-points');
        this.comboDisplay = document.getElementById('combo');
        this.multiplierDisplay = document.getElementById('multiplier');
        this.wordsScroll = document.querySelector('.words-scroll');
    }

    initialize(previousScreen) {
        // Only initialize if coming from main menu or game over
        const gameOver = document.getElementById('game-over');
        const fromGameOver = gameOver?.classList.contains('active');
        const fromMainMenu = previousScreen === 'main-menu';
        
        if (fromMainMenu || fromGameOver) {
            this.resetGame();
        }
    }

    resetGame() {
        // Store current values
        const wasDataReady = gameState.gameDataReady;
        
        // Reset game state
        gameState.resetState();
        
        // Restore values that shouldn't be reset
        gameState.gameDataReady = wasDataReady;
        gameState.timeLeft = 90;  // Reset timer explicitly
        
        // Reset all score displays
        this.scoreDisplay.textContent = '0';
        this.basePointsDisplay.textContent = '0';
        this.comboDisplay.textContent = '';
        this.multiplierDisplay.textContent = '';
        this.timeDisplay.textContent = '1:30';
        
        // Reset plate text and ensure animation class is added
        if (this.plateText) {
            this.plateText.classList.remove('start-plate');
            this.plateText.textContent = 'Press SPACE to start/refresh';
            void this.plateText.offsetWidth;
            this.plateText.classList.add('start-plate');
        }
        
        // Ensure input is hidden initially
        const textEntry = document.querySelector('.text-entry');
        if (textEntry) {
            textEntry.classList.remove('visible');
        }
        if (this.wordInput) {
            this.wordInput.setAttribute('readonly', true);
            this.wordInput.value = '';
        }
        
        // Clear any existing messages
        const gameStatus = document.querySelector('.game-screen .status-message');
        if (gameStatus) {
            statusManager.clearMessages(gameStatus);
        }

        // Clear combo words
        if (this.wordsScroll) {
            this.wordsScroll.innerHTML = '';
        }
    }

    updateWordDisplay(currentWord) {
        if (this.wordInput) {
            this.wordInput.value = currentWord;
        }
    }

    updateTimer(timeLeft) {
        if (this.timeDisplay) {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            this.timeDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    updatePlateDisplay(plate) {
        if (this.plateText) {
            if (!plate) {
                // Opening instruction - apply animation
                this.plateText.classList.remove('start-plate');
                this.plateText.textContent = 'Press SPACE to start/refresh';
                void this.plateText.offsetWidth;
                this.plateText.classList.add('start-plate');
            } else {
                // Plate letters - no animation
                this.plateText.classList.remove('start-plate');
                this.plateText.textContent = plate;
            }
        }
    }

    updateScoreDisplays(score, basePoints, comboPoints, maxComboPoints, multiplier) {
        // Update main score
        this.scoreDisplay.textContent = score.toString();
        
        // Update base points
        this.basePointsDisplay.textContent = basePoints;
        
        // Update combo display with animation
        this.comboDisplay.classList.remove('combo-points');
        void this.comboDisplay.offsetWidth;
        this.comboDisplay.textContent = maxComboPoints + comboPoints > 0 ? 
            `+${maxComboPoints + comboPoints}` : '';
        this.comboDisplay.classList.add('combo-points');
        
        // Update multiplier display with animation (only show if > 1.0)
        this.multiplierDisplay.classList.remove('multiplier-points');
        void this.multiplierDisplay.offsetWidth;
        this.multiplierDisplay.textContent = multiplier > 1.0 ? `×${multiplier.toFixed(2)}` : '';
        if (multiplier > 1.0) {
            this.multiplierDisplay.classList.add('multiplier-points');
        }
    }

    updateInputState(gameActive) {
        const textEntry = document.querySelector('.text-entry');
        if (gameActive) {
            this.wordInput?.removeAttribute('readonly');
            textEntry?.classList.add('visible');
        } else {
            this.wordInput?.setAttribute('readonly', true);
            textEntry?.classList.remove('visible');
        }
    }

    updateComboWords(newWord, isRare = false) {
        if (!this.wordsScroll) return;

        // Add new word to display
        const wordElement = document.createElement('div');
        wordElement.className = 'word';
        if (isRare) {
            wordElement.classList.add('rare');
        }
        wordElement.textContent = newWord.toUpperCase();
        this.wordsScroll.appendChild(wordElement);

        // Scroll to show the new word
        this.wordsScroll.scrollLeft = this.wordsScroll.scrollWidth;

        // Set up arrow controls
        const leftArrow = this.wordsScroll.previousElementSibling;
        const rightArrow = this.wordsScroll.nextElementSibling;

        if (leftArrow && rightArrow) {
            leftArrow.onclick = () => {
                this.wordsScroll.scrollBy({ left: -100, behavior: 'smooth' });
            };
            rightArrow.onclick = () => {
                this.wordsScroll.scrollBy({ left: 100, behavior: 'smooth' });
            };
        }
    }

    clearComboWords() {
        if (this.wordsScroll) {
            this.wordsScroll.innerHTML = '';
        }
    }

    cleanup() {
        // Clear any game state when leaving the screen
        if (this.wordInput) {
            this.wordInput.value = '';
            this.wordInput.setAttribute('readonly', true);
        }
        if (this.wordsScroll) {
            this.wordsScroll.innerHTML = '';
        }
    }
}
