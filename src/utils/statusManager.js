class StatusManager {
    constructor() {
        this._messageQueue = [];
        this._isShowingMessage = false;
        this._timeout = null;
    }

    // Clear all status messages and their queue
    clearMessages(gameStatus) {
        if (!gameStatus) return;
        
        this._messageQueue = [];
        this._isShowingMessage = false;
        if (this._timeout) {
            clearTimeout(this._timeout);
            this._timeout = null;
        }
        gameStatus.textContent = '';
    }

    // Show status message with priority queue
    showMessage(gameStatus, message, duration = 2000) {
        if (!gameStatus || !message) return;
        
        // Determine message priority and adjust duration
        let messagePriority = 1;
        if (message.includes('Combo lost')) {
            messagePriority = 3;
            duration = 3000;
        } else if (message.includes('points')) {
            messagePriority = 2;
            duration = 2000;
        } else if (message.includes('Related:') || message.includes('Coverage:') || 
                   message.includes('Difficulty:') || message.includes('Rare words:') ||
                   message.includes('♪')) { // Hint messages
            messagePriority = 0;
            duration = 4000;
        }
        
        const messageObj = {
            text: message,
            duration: duration,
            priority: messagePriority
        };
        
        // Add message to queue based on priority
        const existingIndex = this._messageQueue.findIndex(m => m.priority <= messagePriority);
        if (existingIndex !== -1) {
            this._messageQueue.splice(existingIndex, 0, messageObj);
            // Remove any lower priority messages that would make queue too long
            while (this._messageQueue.length > 3) {
                const lowestPriorityIndex = this._messageQueue
                    .findIndex((m, i) => i > 0 && m.priority === Math.min(...this._messageQueue.slice(1).map(m => m.priority)));
                if (lowestPriorityIndex !== -1) {
                    this._messageQueue.splice(lowestPriorityIndex, 1);
                } else {
                    break;
                }
            }
        } else if (this._messageQueue.length < 3) {
            this._messageQueue.push(messageObj);
        }
        
        // If no message is currently showing, start displaying messages
        if (!this._isShowingMessage) {
            this._displayNextMessage(gameStatus);
        }
    }

    // Private method to display next message in queue
    _displayNextMessage(gameStatus) {
        if (!this._messageQueue || this._messageQueue.length === 0) {
            this._isShowingMessage = false;
            gameStatus.textContent = '';
            return;
        }
        
        const nextMessage = this._messageQueue.shift();
        this._isShowingMessage = true;
        gameStatus.textContent = nextMessage.text;
        
        // Set up fade out and next message
        if (this._timeout) {
            clearTimeout(this._timeout);
        }
        
        this._timeout = setTimeout(() => {
            this._displayNextMessage(gameStatus);
        }, nextMessage.duration);
    }
}

// Create and export singleton instance
const statusManager = new StatusManager();
export default statusManager;
