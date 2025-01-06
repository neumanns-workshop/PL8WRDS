import MainMenuScreen from './MainMenuScreen.js';
import GameScreen from './GameScreen.js';
import AboutScreen from './AboutScreen.js';
import StatsScreen from './StatsScreen.js';
import gameState from '../../core/gameState.js';

export default class ScreenManager {
    constructor() {
        this.screens = {
            'main-menu': new MainMenuScreen(),
            'game-screen': new GameScreen(),
            'about-screen': new AboutScreen(),
            'stats-screen': new StatsScreen()
        };
        this.currentScreen = null;
        this.previousScreen = null;
    }

    showScreen(screenId) {
        // Hide game over screen if visible
        document.getElementById('game-over')?.classList.remove('active');
        
        // Store previous screen before changing
        this.previousScreen = this.currentScreen?.id;
        
        // Clean up current screen if exists
        if (this.currentScreen) {
            this.currentScreen.cleanup();
            this.currentScreen.hide();
        }
        
        // Show and initialize target screen
        const targetScreen = this.screens[screenId];
        if (targetScreen) {
            targetScreen.show(this.previousScreen);
            this.currentScreen = targetScreen;
            gameState.currentScreen = screenId;
        }
    }

    getPreviousScreen() {
        return this.previousScreen;
    }

    getCurrentScreen() {
        return this.currentScreen;
    }

    getScreen(screenId) {
        return this.screens[screenId];
    }
}
