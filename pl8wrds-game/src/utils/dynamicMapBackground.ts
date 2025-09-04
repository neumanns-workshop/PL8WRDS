// Dynamic Vintage Map Background System
// Creates randomized cinematic flyover experiences

// Import the vintage map asset for webpack
import vintageMapImage from '../assets/1918_AAA_General_Map_of_Transcontinental_Routes.jpg';

export class DynamicMapBackground {
  private static instance: DynamicMapBackground;
  private currentRoute: number = 1;
  protected animationElement: HTMLElement | null = null;
  private routeTimer: NodeJS.Timeout | null = null;
  private isAutomatic: boolean = false;
  
  private routes = [
    'vintageMapFlyover',     // West to East original
    'vintageMapRoute2',      // North to South
    'vintageMapRoute3',      // Southwest to Northeast diagonal  
    'vintageMapRoute4',      // Southeast to Northwest diagonal
    'vintageMapRoute5',      // Circular route
    'vintageMapRoute6',      // Figure-8 route
    'vintageMapRoute7',      // Random zigzag
  ];

  private routeDurations = [120, 90, 110, 100, 130, 140, 95]; // seconds
  
  private routeDescriptions = [
    'Classic West to East transcontinental journey',
    'North to South continental traverse', 
    'Southwest to Northeast diagonal flyover',
    'Southeast to Northwest diagonal route',
    'Circular tour of major regions',
    'Figure-8 pattern across the continent',
    'Random zigzag exploration'
  ];

  protected constructor() {
    this.initializeDebugCommands();
  }
  
  static getInstance(): DynamicMapBackground {
    if (!DynamicMapBackground.instance) {
      DynamicMapBackground.instance = new DynamicMapBackground();
    }
    return DynamicMapBackground.instance;
  }
  
  /**
   * Initialize the dynamic map background system
   */
  initialize(): void {
    console.log('🎬 Initializing Dynamic Map Background...');
    this.animationElement = document.body;
    this.setupBackgroundImage();
    this.setRandomRoute();
  }
  
  /**
   * Set up the background image using CSS
   */
  private setupBackgroundImage(): void {
    // Create or update the background style with the imported image
    const style = document.createElement('style');
    style.textContent = `
      body::before {
        background-image: url('` + vintageMapImage + `') !important;
      }
    `;
    
    const existingBgStyle = document.querySelector('#dynamic-map-bg-image');
    if (existingBgStyle) {
      existingBgStyle.remove();
    }
    
    style.id = 'dynamic-map-bg-image';
    document.head.appendChild(style);
  }
  
  /**
   * Set a random animation route for variety
   */
  protected setRandomRoute(): void {
    // Use numbered routes only
    this.currentRoute = Math.floor(Math.random() * this.routes.length) + 1;
    console.log(`🎲 Selected route ${this.currentRoute}: ${this.routes[this.currentRoute - 1]}`);
    this.updateRoute();
    this.scheduleNextRoute();
  }
  
  /**
   * Start automatic route progression
   */
  startAutoProgression(): void {
    this.isAutomatic = true;
    this.scheduleNextRoute();
    console.log('▶️  Started automatic route progression');
  }
  
  /**
   * Stop automatic route progression
   */
  stopAutoProgression(): void {
    this.isAutomatic = false;
    if (this.routeTimer) {
      clearTimeout(this.routeTimer);
      this.routeTimer = null;
    }
    console.log('⏹️  Stopped automatic route progression');
  }
  
  /**
   * Schedule the next route change
   */
  private scheduleNextRoute(): void {
    if (!this.isAutomatic) return;
    
    if (this.routeTimer) {
      clearTimeout(this.routeTimer);
    }
    
    const currentRouteDuration = this.routeDurations[this.currentRoute - 1] * 1000; // Convert to ms
    const pauseDuration = 2000 + Math.random() * 2000; // 2-4 second pause
    const totalDuration = currentRouteDuration + pauseDuration;
    
    this.routeTimer = setTimeout(() => {
      if (this.isAutomatic) {
        this.setRandomRoute();
      }
    }, totalDuration);
  }

  /**
   * Update the CSS animation with the current route
   */
  private updateRoute(): void {
    if (!this.animationElement) {
      console.warn('❌ No animation element found');
      return;
    }

    const routeName = this.routes[this.currentRoute - 1];
    const duration = this.routeDurations[this.currentRoute - 1];
    
    // Remove any existing animation classes
    this.routes.forEach(route => {
      this.animationElement?.classList.remove(route);
    });
    
    // Add the new route animation
    this.animationElement.classList.add(routeName);
    
    // Update animation duration via CSS custom property
    this.animationElement.style.setProperty('--flyover-duration', `${duration}s`);
    
    console.log(`🚀 Activated route: ${routeName} (${duration}s)`);
  }

  /**
   * Get information about the current route
   */
  getCurrentRouteInfo() {
    return {
      name: this.routes[this.currentRoute - 1],
      route: this.routes[this.currentRoute],
      duration: this.routeDurations[this.currentRoute - 1],
      index: this.currentRoute,
      description: this.routeDescriptions[this.currentRoute - 1]
    };
  }
  
  /**
   * Set a specific route by number (1-based)
   */
  setRoute(routeNumber: number): void {
    if (routeNumber < 1 || routeNumber > this.routes.length) {
      console.warn(`❌ Invalid route number: ${routeNumber}. Must be 1-${this.routes.length}`);
      return;
    }
    
    this.currentRoute = routeNumber;
    console.log(`🎯 Manually set route ${routeNumber}: ${this.routes[routeNumber - 1]}`);
    this.updateRoute();
    
    if (this.isAutomatic) {
      this.scheduleNextRoute();
    }
  }

  /**
   * Get all available routes
   */
  getAvailableRoutes(): Array<{index: number, name: string, description: string, duration: number}> {
    return this.routes.map((route, index) => ({
      index: index + 1,
      name: route,
      description: this.routeDescriptions[index],
      duration: this.routeDurations[index]
    }));
  }

  /**
   * Stop the current animation
   */
  stop(): void {
    if (!this.animationElement) return;
    
    this.routes.forEach(route => {
      this.animationElement?.classList.remove(route);
    });
    
    console.log('⏹️ Animation stopped');
  }

  /**
   * Start/restart the animation
   */
  start(): void {
    this.updateRoute();
    console.log('▶️ Animation started');
  }

  /**
   * Toggle animation on/off
   */
  toggle(): void {
    if (!this.animationElement) return;
    
    const hasAnimation = this.routes.some(route => 
      this.animationElement?.classList.contains(route)
    );
    
    if (hasAnimation) {
      this.stop();
    } else {
      this.start();
    }
  }
  
  /**
   * Initialize debug commands on the window object
   */
  private initializeDebugCommands(): void {
    // Create global debug interface
    (window as any).mapFlyover = {
      setRoute: (routeNumber: number) => this.setRoute(routeNumber),
      random: () => this.setRandomRoute(),
      stop: () => this.stop(),
      start: () => this.start(),
      toggle: () => this.toggle(),
      current: () => this.getCurrentRouteInfo(),
      startAuto: () => this.startAutoProgression(),
      stopAuto: () => this.stopAutoProgression(),
      auto: (enabled: boolean = true) => {
        if (enabled) {
          this.startAutoProgression();
        } else {
          this.stopAutoProgression();
        }
      },
      routes: () => {
        console.log('🗺️ Available Routes:');
        this.getAvailableRoutes().forEach(route => {
          console.log(`  ${route.index}. ${route.name} (${route.duration}s) - ${route.description}`);
        });
      },
      help: () => {
        console.log('\n🎬 DYNAMIC MAP FLYOVER CONTROLS:');
        console.log('================================');
        console.log('mapFlyover.routes() - List all available routes');
        console.log('mapFlyover.setRoute(1-7) - Set specific route');
        console.log('mapFlyover.random() - Pick random route');
        console.log('mapFlyover.current() - Show current route info');
        console.log('mapFlyover.start() - Start animation');
        console.log('mapFlyover.stop() - Stop animation');
        console.log('mapFlyover.toggle() - Toggle animation on/off');
        console.log('mapFlyover.auto(true/false) - Enable/disable auto progression');
        console.log('mapFlyover.help() - Show this help\n');
      }
    };

    // Show help on first load
    console.log('🎬 Dynamic Map Background initialized! Type mapFlyover.help() for controls.');
  }
}

// Create and export the singleton instance (explicit init required)
export const dynamicMapBackground = DynamicMapBackground.getInstance();