import BaseScreen from './BaseScreen.js';
import gameState from '../../core/gameState.js';

export default class StatsScreen extends BaseScreen {
    constructor() {
        super('stats-screen');
    }

    show() {
        super.show();
        this.initialize();
    }

    initialize() {
        if (gameState.lifetimeStats) {
            this.updateStatsDisplay(gameState.lifetimeStats);
        }
    }

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

        // Sort and render plates
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
                <div class="plate-content">
                    <span class="plate-text">${plate}</span>
                    <span class="plate-score">${info.score}</span>
                    ${info.isNewBest ? '<span class="plate-best">BEST!</span>' : 
                      !info.previousBest ? '<span class="plate-new">NEW!</span>' : ''}
                </div>
                <div class="plate-details">
                    <span class="plate-difficulty">${info.difficulty || 'Unknown'}</span>
                    ${info.rarestWord ? `<span class="plate-rare">★ ${info.rarestWord}</span>` : ''}
                </div>
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
        let pageIndicator = carousel.querySelector('.page-indicator');
        if (!pageIndicator) {
            pageIndicator = document.createElement('div');
            pageIndicator.className = 'page-indicator';
            carousel.appendChild(pageIndicator);
        }
        pageIndicator.innerHTML = `<span class="current">1</span>/<span class="total">${totalPages}</span>`;

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

    cleanup() {
        // Destroy chart when leaving the screen
        if (window.scoreHistoryChart) {
            window.scoreHistoryChart.destroy();
            window.scoreHistoryChart = null;
        }
    }
}
