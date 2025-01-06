import BaseScreen from './BaseScreen.js';
import gameState from '../../core/gameState.js';
import statusManager from '../../utils/statusManager.js';

export default class MainMenuScreen extends BaseScreen {
    constructor() {
        super('main-menu');
    }

    show() {
        super.show();
        this.initialize();
    }

    initialize() {
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
    }
}
