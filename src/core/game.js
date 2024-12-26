import gameController from '/PL8WRDS/src/core/gameController.js';
import gameState from '/PL8WRDS/src/core/gameState.js';

// Initialize game
gameController.initialize().then(() => {
    // Enable play button once data is loaded
    const playButton = document.querySelector('.menu-button[data-screen="game-screen"]');
    if (playButton) {
        playButton.disabled = false;
    }
    
    // Show ready message
    const gameStatus = document.querySelector('.menu-screen .status-message');
    if (gameStatus) {
        gameStatus.textContent = 'Ready!';
    }
}).catch(error => {
    console.error('Error initializing game:', error);
    const gameStatus = document.querySelector('.menu-screen .status-message');
    if (gameStatus) {
        gameStatus.innerHTML = '<span style="color: #ff4444">Error loading game data</span>';
    }
});
