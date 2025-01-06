import BaseScreen from './BaseScreen.js';

export default class AboutScreen extends BaseScreen {
    constructor() {
        super('about-screen');
        this.currentSlideIndex = 0;
        this.slides = ['gameplay', 'example', 'controls', 'scoring', 'credits'];
    }

    show() {
        super.show();
        this.initialize();
    }

    initialize() {
        this.setupCarousel();
        this.setupNavigation();
    }

    setupCarousel() {
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
    }

    setupNavigation() {
        // Setup label navigation
        document.querySelectorAll('.label').forEach((label, index) => {
            const handleLabelNav = () => {
                this.currentSlideIndex = index;
                this.updateCarousel();
                // Ensure the slide content is scrolled to top when changing slides
                const activeSlide = document.querySelector('.carousel-slide.active');
                if (activeSlide) {
                    activeSlide.scrollTop = 0;
                }
            };

            label.addEventListener('click', handleLabelNav);
            label.addEventListener('touchend', (event) => {
                event.preventDefault();
                handleLabelNav();
            });
        });

        // Setup arrow navigation
        const leftArrow = document.querySelector('.about-screen .carousel-arrow.left');
        const rightArrow = document.querySelector('.about-screen .carousel-arrow.right');

        const handleLeft = () => {
            this.currentSlideIndex = (this.currentSlideIndex - 1 + this.slides.length) % this.slides.length;
            this.updateCarousel();
        };

        const handleRight = () => {
            this.currentSlideIndex = (this.currentSlideIndex + 1) % this.slides.length;
            this.updateCarousel();
        };

        leftArrow?.addEventListener('click', handleLeft);
        leftArrow?.addEventListener('touchend', (event) => {
            event.preventDefault();
            handleLeft();
        });

        rightArrow?.addEventListener('click', handleRight);
        rightArrow?.addEventListener('touchend', (event) => {
            event.preventDefault();
            handleRight();
        });
    }

    updateCarousel() {
        const allSlides = document.querySelectorAll('.carousel-slide');
        const allLabels = document.querySelectorAll('.label');
        
        // Update slides
        allSlides.forEach((slide, index) => {
            slide.classList.remove('active', 'prev', 'next');
            const position = (index - this.currentSlideIndex + this.slides.length) % this.slides.length;
            if (position === 0) {
                slide.classList.add('active');
            } else if (position === this.slides.length - 1) {
                slide.classList.add('prev');
            } else if (position === 1) {
                slide.classList.add('next');
            }
        });
        
        // Update labels
        allLabels.forEach((label, index) => {
            label.classList.remove('active', 'prev', 'next');
            const position = (index - this.currentSlideIndex + this.slides.length) % this.slides.length;
            if (position === 0) {
                label.classList.add('active');
            } else if (position === this.slides.length - 1) {
                label.classList.add('prev');
            } else if (position === 1) {
                label.classList.add('next');
            }
        });
    }

    cleanup() {
        // Reset carousel state
        this.currentSlideIndex = 0;
        this.updateCarousel();
    }
}
