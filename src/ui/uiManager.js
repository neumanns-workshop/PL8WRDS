import ScreenManager from './screens/ScreenManager.js';

class UIManager {
    constructor() {
        this.screenManager = new ScreenManager();
        this.scorePopup = document.getElementById('score-popup');
    }

    showScreen(screenId) {
        this.screenManager.showScreen(screenId);
    }
            
    showScorePopup(points) {
        if (this.scorePopup) {
            this.scorePopup.textContent = `+${points}`;
            this.scorePopup.classList.remove('show');
            void this.scorePopup.offsetWidth;
            this.scorePopup.classList.add('show');
        }
    }

    // Delegate methods to appropriate screen manager
    updateWordDisplay(currentWord) {
        const gameScreen = this.screenManager.getScreen('game-screen');
        gameScreen?.updateWordDisplay(currentWord);
    }

    updateTimer(timeLeft) {
        const gameScreen = this.screenManager.getScreen('game-screen');
        gameScreen?.updateTimer(timeLeft);
    }

    updatePlateDisplay(plate) {
        const gameScreen = this.screenManager.getScreen('game-screen');
        gameScreen?.updatePlateDisplay(plate);
    }

    updateScoreDisplays(score, basePoints, comboPoints, maxComboPoints, multiplier) {
        const gameScreen = this.screenManager.getScreen('game-screen');
        gameScreen?.updateScoreDisplays(score, basePoints, comboPoints, maxComboPoints, multiplier);
    }

    updateComboWords(newWord, isRare = false) {
        const gameScreen = this.screenManager.getScreen('game-screen');
        gameScreen?.updateComboWords(newWord, isRare);
    }

    clearComboWords() {
        const gameScreen = this.screenManager.getScreen('game-screen');
        gameScreen?.clearComboWords();
    }

    updateInputState(gameActive) {
        const gameScreen = this.screenManager.getScreen('game-screen');
        gameScreen?.updateInputState(gameActive);
    }

    showGameOver(gameState, plateData) {
        const gameOver = document.getElementById('game-over');
        if (!gameOver) return;

        const content = document.createElement('div');
        content.className = 'game-over-content';
        content.innerHTML = `
            <div class="game-over-header">
                <h2>Game Over!</h2>
                <div class="stat major">
                    <span class="stat-label">Final Score</span>
                    <span class="stat-value highlight">${gameState.score}</span>
                </div>
            </div>

            <div class="stats-container">
                <div class="stat-row">
                    <div class="stat">
                        <span class="stat-label">Best Combo</span>
                        <span class="stat-value">+${gameState.maxCombo}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Best Base</span>
                        <span class="stat-value">${gameState.maxBase}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Best Mult</span>
                        <span class="stat-value">×${gameState.maxMultiplier.toFixed(1)}</span>
                    </div>
                </div>

                <div class="stats-section">
                    <h3>Plates Collected</h3>
                    <div class="plates-carousel">
                        <button class="carousel-arrow left" type="button">←</button>
                        <div class="plates-scroll">
                            ${this.generateGameOverPlatesHTML(gameState, plateData)}
                        </div>
                        <button class="carousel-arrow right" type="button">→</button>
                    </div>
                </div>

                <div class="button-container">
                    <button class="menu-button back-button" data-screen="main-menu">Menu</button>
                    <button class="menu-button back-button" data-screen="game-screen">Play Again</button>
                </div>
            </div>
        `;

        gameOver.innerHTML = '';
        gameOver.appendChild(content);
        gameOver.classList.add('active');

        this.setupGameOverCarousel(gameOver);
        this.setupGameOverButtons(gameOver);
    }

    generateGameOverPlatesHTML(gameState, plateData) {
        const difficultyOrder = {
            'Impossible': 6,
            'Very Hard': 5,
            'Hard': 4,
            'Medium': 3,
            'Easy': 2,
            'Very Easy': 1
        };

        return Array.from(gameState.seenPlates)
            .map(plate => ({
                plate,
                info: plateData.getPlate(plate),
                score: plateData.getPlateScore(plate)
            }))
            .sort((a, b) => {
                if (b.score?.score !== a.score?.score) return (b.score?.score || 0) - (a.score?.score || 0);
                return difficultyOrder[b.info?.difficulty] - difficultyOrder[a.info?.difficulty];
            })
            .map(({plate, info, score}) => {
                const difficulty = info?.difficulty?.replace(/\s+/g, '-').toLowerCase() || 'unknown';
                const plateScore = score?.score || 0;
                const rarestWord = score?.rarestWord || 'None';
                
                return `
                    <div class="plate-display" 
                         data-difficulty="${difficulty}" 
                         title="Score: ${plateScore}
Difficulty: ${info?.difficulty || 'Unknown'}
Hidden Rare: ${rarestWord}">
                        <div class="plate-content">
                            <span class="plate-text">${plate}</span>
                            <span class="plate-score">${plateScore}</span>
                            ${!score?.previousBest ? '<span class="plate-new">NEW!</span>' :
                              score?.isNewBest ? '<span class="plate-best">BEST!</span>' : ''}
                        </div>
                        <div class="plate-details">
                            <span class="plate-difficulty">${info?.difficulty || 'Unknown'}</span>
                            ${rarestWord !== 'None' ? `<span class="plate-rare">★ ${rarestWord}</span>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
    }

    setupGameOverCarousel(gameOver) {
        const platesScroll = gameOver.querySelector('.plates-scroll');
        if (!platesScroll) return;

        const checkArrows = () => {
            const leftArrow = gameOver.querySelector('.carousel-arrow.left');
            const rightArrow = gameOver.querySelector('.carousel-arrow.right');
            if (leftArrow && rightArrow) {
                leftArrow.style.visibility = platesScroll.scrollLeft <= 0 ? 'hidden' : 'visible';
                rightArrow.style.visibility = 
                    platesScroll.scrollLeft + platesScroll.clientWidth >= platesScroll.scrollWidth 
                    ? 'hidden' : 'visible';
            }
        };

        gameOver.querySelectorAll('.plates-carousel .carousel-arrow').forEach(arrow => {
            arrow.addEventListener('click', () => {
                const isLeft = arrow.classList.contains('left');
                const targetScroll = isLeft ?
                    Math.max(0, platesScroll.scrollLeft - platesScroll.clientWidth) :
                    Math.min(
                        platesScroll.scrollWidth - platesScroll.clientWidth,
                        platesScroll.scrollLeft + platesScroll.clientWidth
                    );
                platesScroll.scrollTo({ left: targetScroll, behavior: 'smooth' });
            });
        });

        platesScroll.addEventListener('scroll', checkArrows);
        setTimeout(checkArrows, 100);
    }

    setupGameOverButtons(gameOver) {
        gameOver.querySelectorAll('.menu-button').forEach(button => {
            const handleNav = () => {
                gameOver.classList.remove('active');
                const targetScreen = button.getAttribute('data-screen');
                if (!targetScreen) return;
                this.showScreen(targetScreen);
            };

            button.addEventListener('click', handleNav);
            button.addEventListener('touchend', (event) => {
                event.preventDefault();
                handleNav();
            });
        });
    }
}

// Create and export singleton instance
const uiManager = new UIManager();
export default uiManager;
