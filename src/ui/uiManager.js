import gameState from '/PL8WRDS/src/core/gameState.js';
import statusManager from '/PL8WRDS/src/utils/statusManager.js';

class UIManager {
    constructor() {
        // Cache DOM elements
        this.wordInput = document.getElementById('word-input');
        this.scoreDisplay = document.getElementById('score');
        this.timeDisplay = document.getElementById('time');
        this.plateText = document.getElementById('plate-text');
        this.basePointsDisplay = document.getElementById('base-points');
        this.comboDisplay = document.getElementById('combo');
        this.multiplierDisplay = document.getElementById('multiplier');
        this.wordsScroll = document.querySelector('.words-scroll');
        this.scorePopup = document.getElementById('score-popup');
    }

    // Screen management
    showScreen(screenId) {
        console.log('Showing screen:', screenId);
        
        // Hide game over screen
        document.getElementById('game-over').classList.remove('active');
        
        // Update screen classes
        document.querySelectorAll('.screen, .menu-screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        const targetScreen = document.getElementById(screenId);
        if (targetScreen) {
            targetScreen.classList.add('active');
            gameState.currentScreen = screenId; // Set directly instead of using setCurrentScreen
            console.log('Screen state updated:', gameState.currentScreen);
        }

    // Handle screen-specific initialization
    if (screenId === 'main-menu') {
        const playButton = document.querySelector('.menu-button[data-screen="game-screen"]');
        const gameStatus = document.querySelector('.menu-screen .status-message');
        const plateText = document.getElementById('plate-text');
        
        // Set status based on game state
        if (gameStatus) {
            if (!gameState.gameDataReady) {
                statusManager.showMessage(gameStatus, 'Loading...');
                if (playButton) playButton.disabled = true;
            } else {
                statusManager.showMessage(gameStatus, 'Ready!');
                if (playButton) playButton.disabled = false;
            }
        }

        // Reset plate text animation
        if (plateText) {
            plateText.classList.remove('start-plate');
            plateText.textContent = 'Press SPACE to start/refresh';
            void plateText.offsetWidth;
            plateText.classList.add('start-plate');
        }
    } else if (screenId === 'game-screen') {
        // Store current values
        const wasDataReady = gameState.gameDataReady;
        
        // Reset game state
        gameState.resetState();
        
        // Restore values that shouldn't be reset
        gameState.gameDataReady = wasDataReady;
        gameState.currentScreen = screenId;
        gameState.timeLeft = 90;  // Reset timer explicitly
        
        // Reset all score displays
        this.scoreDisplay.textContent = '0';
        document.getElementById('base-points').textContent = '0';
        document.getElementById('combo').textContent = '';
        document.getElementById('multiplier').textContent = '';
        document.getElementById('time').textContent = '1:30';
        this.updateWordDisplay('');
        
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
        }
        
        // Clear any existing messages
        const gameStatus = document.querySelector('.game-screen .status-message');
        if (gameStatus) {
            statusManager.clearMessages(gameStatus);
        }
    } else if (screenId === 'about-screen') {
        // Initialize carousel to first slide
        const allSlides = document.querySelectorAll('.carousel-slide');
        const allLabels = document.querySelectorAll('.label');
        
        allSlides.forEach((slide, index) => {
            slide.classList.remove('active', 'prev', 'next');
            if (index === 0) slide.classList.add('active');
            else if (index === 1) slide.classList.add('next');
            else if (index === allSlides.length - 1) slide.classList.add('prev');
        });
        
        allLabels.forEach((label, index) => {
            label.classList.remove('active', 'prev', 'next');
            if (index === 0) label.classList.add('active');
            else if (index === 1) label.classList.add('next');
            else if (index === allLabels.length - 1) label.classList.add('prev');
        });
    } else if (screenId === 'stats-screen') {
        this.updateStatsDisplay(gameState.lifetimeStats);
    }
    }

    // Game screen updates
    updateWordDisplay(currentWord) {
        this.wordInput.value = currentWord;
    }

    updateTimer(timeLeft) {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        this.timeDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
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

    showScorePopup(points) {
        if (this.scorePopup) {
            this.scorePopup.textContent = `+${points}`;
            this.scorePopup.classList.remove('show');
            void this.scorePopup.offsetWidth;
            this.scorePopup.classList.add('show');
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

    // Input state management
    updateInputState(gameActive) {
        const textEntry = document.querySelector('.text-entry');
        if (gameActive) {
            this.wordInput.removeAttribute('readonly');
            textEntry?.classList.add('visible');
        } else {
            this.wordInput.setAttribute('readonly', true);
            textEntry?.classList.remove('visible');
        }
    }

    // Stats display
    updateStatsDisplay(lifetimeStats) {
        // Update basic stats
        document.getElementById('lifetime-games').textContent = lifetimeStats.gamesPlayed;
        document.getElementById('lifetime-score').textContent = lifetimeStats.totalScore;
        document.getElementById('lifetime-best-score').textContent = lifetimeStats.bestScore;
        document.getElementById('lifetime-plates').textContent = lifetimeStats.uniquePlates.size;
        document.getElementById('lifetime-combo').textContent = `+${lifetimeStats.bestCombo}`;
        document.getElementById('lifetime-multiplier').textContent = `×${lifetimeStats.bestMultiplier.toFixed(1)}`;

        this.updateHiddenRares(lifetimeStats.hiddenRares);
        this.updateTopPlatesCarousel(lifetimeStats.topPlates);
        this.updateScoreHistory(lifetimeStats.scoreHistory);
    }

    // Private helper methods for stats display
    updateHiddenRares(hiddenRares) {
        const container = document.querySelector('.stats-screen .hidden-rares');
        if (!container) return;

        const difficultyOrder = {
            'impossible': 6,
            'veryhard': 5,
            'hard': 4,
            'medium': 3,
            'easy': 2,
            'veryeasy': 1
        };

        const raresList = Array.from(hiddenRares.entries())
            .sort((a, b) => difficultyOrder[b[0]] - difficultyOrder[a[0]])
            .map(([difficulty, rares]) => {
                // Handle both old (single rare) and new (array of rares) format
                const raresArray = Array.isArray(rares) ? rares : (rares.word ? [rares] : []);
                return raresArray.map(rare => `
                    <div class="rare-word ${difficulty}">
                        <span class="word">${rare.word}</span>
                        <span class="difficulty">${difficulty.replace(/([A-Z])/g, ' $1').toLowerCase()}</span>
                    </div>
                `).join('');
            }).join('');
        
        container.innerHTML = `
            <div class="rares-grid">
                ${raresList}
            </div>
        `;
    }

    updateTopPlatesCarousel(topPlates) {
        const carousel = document.querySelector('.stats-screen .plates-carousel');
        const platesScroll = carousel?.querySelector('.plates-scroll');
        if (!platesScroll) return;

        // Clear existing event listeners
        const oldArrows = carousel.querySelectorAll('.carousel-arrow');
        oldArrows.forEach(arrow => {
            const newArrow = arrow.cloneNode(true);
            arrow.parentNode.replaceChild(newArrow, arrow);
        });

        // Update plates display
        const sortedPlates = Array.from(topPlates.entries())
            .sort(([,a], [,b]) => {
                if (b.score !== a.score) return b.score - a.score;
                const difficultyOrder = {
                    'Impossible': 6,
                    'Very Hard': 5,
                    'Hard': 4,
                    'Medium': 3,
                    'Easy': 2,
                    'Very Easy': 1
                };
                return difficultyOrder[b.difficulty] - difficultyOrder[a.difficulty];
            });

        this.renderPlatesCarousel(platesScroll, sortedPlates, carousel);
    }

    renderPlatesCarousel(platesScroll, sortedPlates, carousel) {
        platesScroll.innerHTML = sortedPlates.map(([plate, info]) => `
            <div class="plate-display" data-difficulty="${(info.difficulty?.replace(/\s+/g, '-') || 'Unknown').toLowerCase()}" 
                 title="Score: ${info.score}\nDifficulty: ${info.difficulty}\nHidden Rare: ${info.rarestWord}">
                <span class="plate-text">${plate}</span>
                <span class="plate-score">${info.score}</span>
                ${info.isNewBest ? '<span class="plate-best">BEST!</span>' : 
                  !info.previousBest ? '<span class="plate-new">NEW!</span>' : ''}
            </div>
        `).join('');

        this.setupCarouselControls(carousel, platesScroll);
    }

    setupCarouselControls(carousel, platesScroll) {
        // Calculate plates per page
        const plateWidth = platesScroll.firstElementChild?.offsetWidth ?? 100;
        const platesPerPage = Math.floor(platesScroll.clientWidth / (plateWidth + 20));
        const totalPages = Math.ceil(platesScroll.children.length / platesPerPage);
        
        // Add page indicator
        const pageIndicator = document.createElement('div');
        pageIndicator.className = 'page-indicator';
        pageIndicator.innerHTML = `<span class="current">1</span>/<span class="total">${totalPages}</span>`;
        carousel.appendChild(pageIndicator);

        // Set up navigation
        const handleScroll = () => {
            const scrollPercentage = platesScroll.scrollLeft / (platesScroll.scrollWidth - platesScroll.clientWidth);
            const currentPage = Math.round(scrollPercentage * (totalPages - 1)) + 1;
            pageIndicator.querySelector('.current').textContent = currentPage;
            
            const leftArrow = carousel.querySelector('.carousel-arrow.left');
            const rightArrow = carousel.querySelector('.carousel-arrow.right');
            if (leftArrow && rightArrow) {
                leftArrow.style.visibility = platesScroll.scrollLeft <= 0 ? 'hidden' : 'visible';
                rightArrow.style.visibility = 
                    platesScroll.scrollLeft + platesScroll.clientWidth >= platesScroll.scrollWidth - 10
                    ? 'hidden' : 'visible';
            }
        };

        platesScroll.addEventListener('scroll', handleScroll);
        setTimeout(handleScroll, 100);

        // Add navigation controls
        carousel.querySelectorAll('.carousel-arrow').forEach(arrow => {
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
    }

    updateScoreHistory(scoreHistory) {
        const container = document.getElementById('score-history');
        if (!container || !window.Chart) return;

        // Destroy existing chart
        if (window.scoreHistoryChart) {
            window.scoreHistoryChart.destroy();
        }

        // Create new chart
        const ctx = container.getContext('2d');
        window.scoreHistoryChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({ length: scoreHistory.length }, (_, i) => `Game ${i + 1}`),
                datasets: [{
                    label: 'Score',
                    data: scoreHistory,
                    borderColor: '#333',
                    backgroundColor: 'rgba(51, 51, 51, 0.05)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#333',
                    pointBorderColor: '#fff',
                    pointRadius: 3,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 15,
                        right: 25,
                        bottom: 15,
                        left: 25
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { display: false },
                        min: 0,
                        max: Math.max(Math.max(...scoreHistory) * 1.1, 100),
                        ticks: {
                            color: '#333',
                            font: {
                                family: "'ThaleahFat', sans-serif",
                                size: 14
                            },
                            stepSize: 50,
                            callback: value => value.toFixed(0)
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#333',
                            font: {
                                family: "'ThaleahFat', sans-serif",
                                size: 14
                            },
                            maxTicksLimit: 12
                        }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // Game over screen
    showGameOver(gameState, plateData) {
        const gameOver = document.getElementById('game-over');
        if (!gameOver) return;

        const content = this.createGameOverContent(gameState, plateData);
        gameOver.innerHTML = '';
        gameOver.appendChild(content);
        gameOver.classList.add('active');

        this.setupGameOverCarousel(gameOver);
        this.setupGameOverButtons(gameOver);
    }

    createGameOverContent(gameState, plateData) {
        const content = document.createElement('div');
        content.className = 'game-over-content';
        content.innerHTML = this.generateGameOverHTML(gameState, plateData);
        return content;
    }

    generateGameOverHTML(gameState, plateData) {
        return `
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
                            ${this.generatePlatesHTML(gameState, plateData)}
                        </div>
                        <button class="carousel-arrow right" type="button">→</button>
                    </div>
                </div>

                <div class="button-container">
                    <button class="menu-button" data-screen="game-screen">Play Again</button>
                    <button class="menu-button" data-screen="main-menu">Main Menu</button>
                </div>
            </div>
        `;
    }

    generatePlatesHTML(gameState, plateData) {
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
            button.addEventListener('mousedown', () => {
                gameOver.classList.remove('active');
                const targetScreen = button.getAttribute('data-screen');
                gameState.gameActive = false;
                this.showScreen(targetScreen);
            });
        });
    }
}

// Create and export singleton instance
const uiManager = new UIManager();
export default uiManager;
