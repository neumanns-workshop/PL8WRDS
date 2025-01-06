export default class BaseScreen {
    constructor(id) {
        this.id = id;
        this.element = document.getElementById(id);
    }

    show(previousScreen) {
        if (!this.element) return;
        this.element.classList.add('active');
        this.initialize(previousScreen);
    }

    hide() {
        if (!this.element) return;
        this.element.classList.remove('active');
    }

    initialize() {
        // Override in child classes
    }

    cleanup() {
        // Override in child classes
    }
}
