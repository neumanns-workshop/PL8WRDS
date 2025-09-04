// Geographic Map Background System
// Enhanced version that uses real waypoints from the map pinning interface

import { DynamicMapBackground } from './dynamicMapBackground';
import { mapPanner } from './mapPanner';
import { VINTAGE_MAP_WAYPOINTS } from './vintage-map-waypoints';

export interface MapWaypoint {
  id: string;
  name: string;
  x_percent: number;
  y_percent: number;
  category: 'city' | 'landmark' | 'junction' | 'airport';
}

export interface RoadTripRoute {
  id: string;
  name: string;
  description: string;
  waypoints: MapWaypoint[];
  totalMiles: number;
  estimatedDriveTimeHours: number;
  highways: string[]; // Major highways used (I-80, I-95, Route 66, etc.)
  routeType: 'interstate' | 'scenic' | 'historic' | 'coastal';
  drivingStyle: 'highway' | 'scenic' | 'mixed';
}

export class RouteManager {
  private isRunning = false;
  private currentRouteTimeout: NodeJS.Timeout | null = null;
  private routes: RoadTripRoute[] = [];
  private currentRouteIndex = 0;
  private onRouteChange: (route: RoadTripRoute) => Promise<void>;
  
  constructor(onRouteChange: (route: RoadTripRoute) => Promise<void>) {
    this.onRouteChange = onRouteChange;
  }
  
  setRoutes(routes: RoadTripRoute[]): void {
    this.routes = routes;
    this.currentRouteIndex = 0;
  }
  
  start(): void {
    if (this.isRunning || this.routes.length === 0) return;
    this.isRunning = true;
    this.executeNextRoute();
  }
  
  stop(): void {
    this.isRunning = false;
    if (this.currentRouteTimeout) {
      clearTimeout(this.currentRouteTimeout);
      this.currentRouteTimeout = null;
    }
  }
  
  private async executeNextRoute(): Promise<void> {
    if (!this.isRunning || this.routes.length === 0) return;
    
    const route = this.routes[this.currentRouteIndex];
    console.log(`🎬 Starting cinematic journey ${this.currentRouteIndex + 1}/${this.routes.length}: ${route.name}`);
    console.log(`   Route: ${route.waypoints.map(wp => wp.name).join(' → ')}`);
    
    // Execute the route and wait for it to complete
    try {
      await this.onRouteChange(route);
    } catch (error) {
      console.warn('Route execution error:', error);
    }
    
    if (!this.isRunning) return; // Check if we were stopped during route execution
    
    // Dramatic pause between cinematic journeys (4-8 seconds for anticipation)
    const pauseMs = 4000 + Math.random() * 4000;
    console.log(`⏸️  Dramatic pause for ${Math.round(pauseMs/1000)}s before next journey...`);
    
    // Schedule next route
    this.currentRouteTimeout = setTimeout(() => {
      if (!this.isRunning) return;
      
      this.currentRouteIndex = (this.currentRouteIndex + 1) % this.routes.length;
      this.executeNextRoute();
    }, pauseMs);
  }
  
  setRoute(index: number): void {
    if (index >= 0 && index < this.routes.length) {
      this.currentRouteIndex = index;
      if (this.isRunning) {
        this.stop();
        this.start();
      }
    }
  }
  
  getCurrentRoute(): RoadTripRoute | null {
    return this.routes[this.currentRouteIndex] || null;
  }
}

export class GeographicMapBackground extends DynamicMapBackground {
  private waypoints: Map<string, MapWaypoint> = new Map();
  private roadTripRoutes: RoadTripRoute[] = [];
  private isGeographicMode: boolean = false;
  private routeManager: RouteManager;
  private roadTripSpeedMultiplier: number = 1.0; // Adjustable speed control
  private debugMode: boolean = false; // Enable detailed position tracking
  private roadTripZoomLevel: number = 6.5; // Close, intimate road trip zoom level
  
  // Smooth cruise control easing function - no jerky acceleration/deceleration
  private cruiseControlEasing = (t: number): number => {
    // Very gentle ease-in-out to minimize jerkiness - almost linear
    return t < 0.5 ? 2 * t * t : 1 - 2 * (1 - t) * (1 - t);
  };
  
  // Road trip simulation parameters - dampened for ultra-leisurely cruising
  private averageHighwaySpeed: number = 45; // mph (dampened from 65 for leisurely cruising)  
  private averageScenicSpeed: number = 30; // mph (dampened from 45 for relaxed sightseeing)
  private timeCompressionFactor: number = 1.8; // 1 real second = 5 game hours (100x slower for ultra-relaxing road trips)
  private mapWidthMiles: number = 2800; // Approximate miles coast-to-coast
  private mapHeightMiles: number = 1700; // Approximate miles north-to-south
  
  // Add public constructor for this subclass
  constructor() {
    super();
    this.routeManager = new RouteManager(this.executeRoadTripRoute.bind(this));
    this.setupKeyboardShortcuts();
  }
  
  /**
   * Setup keyboard shortcuts for quick location access
   */
  private setupKeyboardShortcuts(): void {
    // Add keyboard listeners for quick zoom (only when no input is focused)
    document.addEventListener('keydown', (event) => {
      const activeElement = document.activeElement;
      const isTypingInInput = activeElement?.tagName === 'INPUT' || activeElement?.tagName === 'TEXTAREA';
      const isModalOpen = document.querySelector('.registration-overlay, .score-breakdown-overlay');
      
      if (isTypingInInput || isModalOpen) {
        return;
      }
      
      // Ctrl/Cmd + number keys for quick city zoom
      if ((event.metaKey || event.ctrlKey) && event.key >= '1' && event.key <= '9') {
        event.preventDefault();
        const cityIndex = parseInt(event.key) - 1;
        const cities = Array.from(this.waypoints.values())
          .filter(wp => wp.category === 'city')
          .sort((a, b) => a.name.localeCompare(b.name));
        
        if (cities[cityIndex]) {
          this.zoomToLocation(cities[cityIndex].name);
          console.log(`🔍 Keyboard shortcut: Zooming to ${cities[cityIndex].name}`);
        }
      }
    });
  }
  
  /**
   * Load waypoints from the map pinning interface or local file
   */
  async loadWaypoints(): Promise<void> {
    try {
      console.log('🗺️  Loading geographic waypoints...');
      
      let waypoints: MapWaypoint[] = [];
      
      // Try to fetch from backend API first
      try {
        const response = await fetch('http://localhost:8000/map/pins');
        if (response.ok) {
          const pins: any[] = await response.json();
          waypoints = pins.map(pin => ({
            id: pin.id,
            name: pin.name,
            x_percent: pin.x_percent,
            y_percent: pin.y_percent,
            category: pin.category
          }));
          console.log(`✅ Loaded ${waypoints.length} waypoints from API`);
        } else {
          throw new Error(`API responded with ${response.status}`);
        }
      } catch (apiError) {
        console.log('🔄 API unavailable, using local waypoints...');
        // Fallback to local waypoints
        waypoints = VINTAGE_MAP_WAYPOINTS;
        console.log(`✅ Loaded ${waypoints.length} waypoints from local file`);
      }
      
      // Populate waypoints map
      this.waypoints.clear();
      waypoints.forEach(waypoint => {
        this.waypoints.set(waypoint.id, waypoint);
      });
      
      if (waypoints.length > 0) {
        console.log(`🎯 Total waypoints: ${this.waypoints.size}`);
        // Generate realistic flight routes
        this.generateRealisticRoutes();
      } else {
        throw new Error('No waypoints available');
      }
      
    } catch (error) {
      console.warn('⚠️  Failed to load geographic waypoints, falling back to artistic routes:', error);
      this.isGeographicMode = false;
    }
  }
  
  /**
   * Generate realistic American highway road trip routes
   */
  private generateRealisticRoutes(): void {
    const waypointArray = Array.from(this.waypoints.values());
    const cities = waypointArray.filter(wp => wp.category === 'city');
    
    if (cities.length < 3) {
      console.warn('⚠️  Not enough cities for road trip routes, need at least 3');
      return;
    }
    
    this.roadTripRoutes = [];
    const cityMap = new Map(cities.map(c => [c.name, c]));
    
    // 1. Historic Route 66 (Chicago to Los Angeles) - The Mother Road
    const route66CitiesList = [
      'Chicago, IL', 'St. Louis, MO', 'Springfield, MO', 'Tulsa, OK', 'Oklahoma City, OK', 
      'Amarillo, TX', 'Albuquerque, NM', 'Santa Fe, NM', 'Kingman, AZ', 'Flagstaff, AZ', 'Los Angeles, CA'
    ];
    const route66Cities = this.findCitiesByName(cityMap, route66CitiesList);
    console.log(`🛣️  Route 66 cities found: ${route66Cities.map(c => c.name).join(', ')} (${route66Cities.length}/${route66CitiesList.length} cities)`);
    if (route66Cities.length >= 3) {
      this.roadTripRoutes.push({
        id: 'route_66',
        name: 'Historic Route 66: The Mother Road',
        description: 'Classic American road trip from Chicago to Los Angeles',
        waypoints: route66Cities,
        totalMiles: 2448,
        estimatedDriveTimeHours: 40, // Slightly longer with more stops
        highways: ['Route 66', 'I-40'],
        routeType: 'historic',
        drivingStyle: 'mixed'
      });
    } else {
      console.warn('⚠️  Not enough cities for Route 66');
    }
    
    // 2. I-80 Transcontinental (NYC to San Francisco)
    const i80Cities = this.findCitiesByName(cityMap, ['New York City', 'Chicago', 'Omaha', 'Salt Lake City', 'San Francisco']);
    if (i80Cities.length >= 4) {
      this.roadTripRoutes.push({
        id: 'i80_transcontinental',
        name: 'I-80 Transcontinental Highway',
        description: 'Fastest coast-to-coast route across northern states',
        waypoints: i80Cities,
        totalMiles: 2900,
        estimatedDriveTimeHours: 45,
        highways: ['I-80'],
        routeType: 'interstate',
        drivingStyle: 'highway'
      });
    }
    
    // 3. I-95 East Coast Corridor (Boston to Miami)
    const i95Cities = this.findCitiesByName(cityMap, ['Boston', 'New York City', 'Washington, DC', 'Raleigh', 'Atlanta', 'Miami']);
    if (i95Cities.length >= 4) {
      this.roadTripRoutes.push({
        id: 'i95_east_coast',
        name: 'I-95 East Coast Road Trip',
        description: 'Historic cities from New England to Florida',
        waypoints: i95Cities,
        totalMiles: 1300,
        estimatedDriveTimeHours: 20,
        highways: ['I-95'],
        routeType: 'interstate',
        drivingStyle: 'highway'
      });
    }
    
    // 4. I-10 Southern Route (Los Angeles to Miami)
    const i10Cities = this.findCitiesByName(cityMap, ['Los Angeles', 'El Paso', 'Houston', 'New Orleans', 'Miami']);
    if (i10Cities.length >= 4) {
      this.roadTripRoutes.push({
        id: 'i10_southern',
        name: 'I-10 Southern Transcontinental',
        description: 'Sunny southern route across the sunbelt',
        waypoints: i10Cities,
        totalMiles: 2460,
        estimatedDriveTimeHours: 38,
        highways: ['I-10'],
        routeType: 'interstate',
        drivingStyle: 'highway'
      });
    }
    
    // 5. Pacific Coast Highway (Seattle to Los Angeles)
    const pchCities = this.findCitiesByName(cityMap, ['Seattle', 'Portland', 'San Francisco', 'Los Angeles']);
    if (pchCities.length >= 3) {
      this.roadTripRoutes.push({
        id: 'pacific_coast',
        name: 'Pacific Coast Highway',
        description: 'Scenic coastal drive along the Pacific Ocean',
        waypoints: pchCities,
        totalMiles: 1400,
        estimatedDriveTimeHours: 30, // Slower due to scenic roads
        highways: ['I-5', 'US-101', 'PCH'],
        routeType: 'coastal',
        drivingStyle: 'scenic'
      });
    }
    
    // 6. Great Lakes Circle Tour
    const lakesTourCities = this.findCitiesByName(cityMap, ['Chicago', 'Detroit', 'Buffalo', 'Chicago']);
    if (lakesTourCities.length >= 3) {
      this.roadTripRoutes.push({
        id: 'great_lakes_tour',
        name: 'Great Lakes Circle Tour',
        description: 'Scenic loop around America\'s freshwater seas',
        waypoints: lakesTourCities.slice(0, 3), // Remove duplicate Chicago
        totalMiles: 1200,
        estimatedDriveTimeHours: 20,
        highways: ['I-80', 'I-75', 'I-90'],
        routeType: 'scenic',
        drivingStyle: 'mixed'
      });
    }
    
    // 7. Southwest Desert Loop
    const desertCities = this.findCitiesByName(cityMap, ['Las Vegas', 'Santa Fe', 'El Paso', 'Los Angeles']);
    if (desertCities.length >= 3) {
      this.roadTripRoutes.push({
        id: 'southwest_desert',
        name: 'Southwest Desert Adventure',
        description: 'Desert landscapes and southwestern culture',
        waypoints: desertCities,
        totalMiles: 1800,
        estimatedDriveTimeHours: 28,
        highways: ['I-15', 'I-25', 'I-10'],
        routeType: 'scenic',
        drivingStyle: 'mixed'
      });
    }
    
    // Ensure we have at least some basic routes if named routes fail
    if (this.roadTripRoutes.length === 0) {
      console.warn('⚠️  No named routes found, creating basic interstate routes');
      this.createBasicInterstateRoutes(cities);
    }
    
    console.log(`🛣️  Generated ${this.roadTripRoutes.length} American highway road trip routes`);
    this.isGeographicMode = true;
    
    // Set up route manager with the new routes (will be started by parent's setRandomRoute)
    this.routeManager.setRoutes(this.roadTripRoutes);
    
    // Route 66 will be automatically started as default by setRandomRoute() during parent initialization
  }
  
  /**
   * Helper method to find cities by name from a city map
   */
  private findCitiesByName(cityMap: Map<string, MapWaypoint>, cityNames: string[]): MapWaypoint[] {
    const foundCities: MapWaypoint[] = [];
    for (const name of cityNames) {
      const city = cityMap.get(name);
      if (city) {
        foundCities.push(city);
      }
    }
    return foundCities;
  }
  
  /**
   * Create basic interstate routes as fallback
   */
  private createBasicInterstateRoutes(cities: MapWaypoint[]): void {
    // Simple east-west interstate
    const eastCities = cities.filter(c => c.x_percent > 70).slice(0, 2);
    const westCities = cities.filter(c => c.x_percent < 30).slice(0, 2);
    const centralCities = cities.filter(c => c.x_percent > 40 && c.x_percent < 60).slice(0, 2);
    
    if (eastCities.length > 0 && westCities.length > 0) {
      const waypoints = [eastCities[0], ...centralCities, westCities[0]];
      const miles = this.calculateRouteMiles(waypoints);
      
      this.roadTripRoutes.push({
        id: 'basic_transcontinental',
        name: 'Basic Transcontinental Route',
        description: 'Simple coast-to-coast highway route',
        waypoints,
        totalMiles: miles,
        estimatedDriveTimeHours: Math.round(miles / this.averageHighwaySpeed),
        highways: ['I-80', 'I-40'],
        routeType: 'interstate',
        drivingStyle: 'highway'
      });
    }
  }
  
  /**
   * Calculate total miles for a route based on map coordinates
   */
  private calculateRouteMiles(waypoints: MapWaypoint[]): number {
    if (waypoints.length < 2) return 0;
    
    let totalMiles = 0;
    for (let i = 0; i < waypoints.length - 1; i++) {
      const distance = this.calculateDistance(waypoints[i], waypoints[i + 1]);
      // Convert percentage distance to miles (rough approximation)
      const segmentMiles = (distance / 100) * Math.sqrt(
        Math.pow(this.mapWidthMiles, 2) + Math.pow(this.mapHeightMiles, 2)
      );
      totalMiles += segmentMiles;
    }
    
    return Math.round(totalMiles);
  }
  
  
  
  /**
   * Calculate percentage-based distance between two waypoints
   */
  private calculateDistance(wp1: MapWaypoint, wp2: MapWaypoint): number {
    const dx = wp1.x_percent - wp2.x_percent;
    const dy = wp1.y_percent - wp2.y_percent;
    return Math.sqrt(dx * dx + dy * dy);
  }
  
  /**
   * Override parent method to always start with Route 66 when available
   */
  protected override setRandomRoute(): void {
    console.log('🔍 setRandomRoute() called - checking for Route 66...');
    console.log(`   Geographic mode: ${this.isGeographicMode}, Routes available: ${this.roadTripRoutes.length}`);
    
    if (this.isGeographicMode && this.roadTripRoutes.length > 0) {
      // Always prefer Route 66 as the starting route
      const route66 = this.roadTripRoutes.find(route => route.id === 'route_66');
      if (route66) {
        console.log('🛣️  ✅ FOUND Route 66! Starting default Route 66 experience...');
        console.log(`   Starting in: ${route66.waypoints[0]?.name} (${route66.waypoints[0]?.x_percent}%, ${route66.waypoints[0]?.y_percent}%)`);
        
        // Disable parent's CSS animations completely when using geographic mode
        this.stopParentAnimations();
        
        this.executeRoadTripRoute(route66).catch(error => {
          console.warn('Route 66 execution error:', error);
        });
        return; // Don't call parent
      } else {
        // Fallback to first available route
        console.log('⚠️  Route 66 not found, using fallback road trip...');
        this.stopParentAnimations();
        this.executeRoadTripRoute(this.roadTripRoutes[0]).catch(error => {
          console.warn('Road trip execution error:', error);
        });
        return; // Don't call parent
      }
    } else {
      console.log('⚠️  No geographic routes available, falling back to parent CSS animations');
      // Fallback to parent implementation for artistic routes
      super.setRandomRoute();
    }
  }
  
  /**
   * Stop parent's CSS animations when using geographic mode
   */
  private stopParentAnimations(): void {
    // Remove any CSS animation classes that parent might have applied
    const body = document.body;
    const classList = body.classList;
    const animationClasses = ['vintageMapFlyover', 'vintageMapRoute2', 'vintageMapRoute3', 'vintageMapRoute4', 'vintageMapRoute5', 'vintageMapRoute6', 'vintageMapRoute7'];
    
    animationClasses.forEach(className => {
      if (classList.contains(className)) {
        classList.remove(className);
        console.log(`🚫 Removed parent CSS animation: ${className}`);
      }
    });
  }
  
  /**
   * Execute a complete road trip route and return when finished
   */
  private async executeRoadTripRoute(route: RoadTripRoute): Promise<void> {
    console.log(`🚗 Beginning American road trip: ${route.name}`);
    console.log(`   📍 Route: ${route.waypoints.map(wp => wp.name).join(' → ')}`);
    console.log(`   🛣️  Highway: ${route.highways.join(', ')} | ${route.totalMiles} miles | ${route.estimatedDriveTimeHours}h drive time`);
    
    if (route.waypoints.length === 0) return;
    
    const base = mapPanner.getBaseScale();
    
    // Calculate realistic travel timing based on road trip parameters
    let cruiseZoom: number;
    let baseSpeed: number; // mph
    
    // Use close, intimate road trip zoom level for all driving styles
    cruiseZoom = base * this.roadTripZoomLevel;
    
    switch (route.drivingStyle) {
      case 'highway':
        baseSpeed = this.averageHighwaySpeed; // 45 mph (dampened)
        break;
      case 'scenic':
        baseSpeed = this.averageScenicSpeed; // 30 mph (ultra-leisurely)  
        break;
      case 'mixed':
        baseSpeed = (this.averageHighwaySpeed + this.averageScenicSpeed) / 2; // 37.5 mph (dampened)
        break;
      default:
        baseSpeed = this.averageHighwaySpeed; // 45 mph (dampened default)
    }
    
    // Calculate leg duration based on distance and speed
    const segmentDistance = route.totalMiles / (route.waypoints.length - 1);
    const segmentTimeHours = segmentDistance / baseSpeed;
    const legDurationMs = Math.round(segmentTimeHours * 1000 * 60 / this.timeCompressionFactor * this.roadTripSpeedMultiplier);
    
    console.log(`   🎯 Road trip settings: ${route.drivingStyle} driving, ${baseSpeed}mph avg (dampened), ${(legDurationMs/1000).toFixed(1)}s/leg, ${cruiseZoom.toFixed(1)}x zoom (ultra-leisurely cruise)`);
    
    // Start immediately at the first city
    const first = route.waypoints[0];
    console.log(`   🚗 Starting road trip from ${first.name} (${first.x_percent.toFixed(1)}%, ${first.y_percent.toFixed(1)}%)`);
    
    // Instantly position at the starting city
    mapPanner.setInstantPercent(first.x_percent, first.y_percent, cruiseZoom);
    console.log(`   📍 DEPARTING from ${first.name} - road trip begins now!`);
    
    // Drive to each destination on the road trip
    if (route.waypoints.length > 1) {
      console.log(`   🛣️  Beginning road trip through ${route.waypoints.length - 1} more destinations...`);
      
      // Drive to each city individually for proper logging
      for (let i = 1; i < route.waypoints.length; i++) {
        const destination = route.waypoints[i];
        const legNumber = i;
        const totalLegs = route.waypoints.length - 1;
        
        const startTime = Date.now();
        console.log(`   🚗 Leg ${legNumber}/${totalLegs}: Driving to ${destination.name} (${destination.x_percent.toFixed(1)}%, ${destination.y_percent.toFixed(1)}%)`);
        console.log(`   📊 Departing at ${startTime}`);
        
        // Start real-time position tracking during travel (if debug mode enabled)
        let trackingInterval: NodeJS.Timeout | null = null;
        if (this.debugMode) {
          trackingInterval = setInterval(() => {
            const state = mapPanner.getState();
            const imageSize = mapPanner.getImagePixels();
            const viewportCenter = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
            const imageX = (-state.tx + viewportCenter.x) / state.scale;
            const imageY = (-state.ty + viewportCenter.y) / state.scale;
            const xPercent = (imageX / imageSize.width) * 100;
            const yPercent = (imageY / imageSize.height) * 100;
            
            console.log(`   🛣️  On the road: ${xPercent.toFixed(1)}%, ${yPercent.toFixed(1)}% → driving to ${destination.name}`);
          }, Math.round(legDurationMs / 4)); // Log 4 times during each leg
        }
        
        // Drive to this destination and wait for completion
        await mapPanner.panToPercent(destination.x_percent, destination.y_percent, { 
          zoom: cruiseZoom, 
          durationMs: legDurationMs,
          easing: this.cruiseControlEasing // Smooth cruise control - no jerky acceleration/deceleration
        });
        
        // Stop position tracking
        if (trackingInterval) {
          clearInterval(trackingInterval);
        }
        
        const arrivalTime = Date.now();
        const travelTimeMs = arrivalTime - startTime;
        console.log(`   📍 ARRIVED in ${destination.name} - Leg ${legNumber}/${totalLegs} completed in ${travelTimeMs}ms`);
        console.log(`   🎯 Current position: ${destination.x_percent.toFixed(1)}%, ${destination.y_percent.toFixed(1)}% (${destination.name})`);
        
        // Rest stop at each destination (except the last one)
        if (i < route.waypoints.length - 1) {
          const pauseMs = Math.round(1200 / this.roadTripSpeedMultiplier); // Longer pause for road trip rest stops
          console.log(`   ⏸️  Rest stop in ${destination.name} (${pauseMs}ms)...`);
          await new Promise(resolve => setTimeout(resolve, pauseMs));
          console.log(`   🚗 Back on the road from ${destination.name}...`);
        }
      }
    }
    
    const finalDestination = route.waypoints[route.waypoints.length - 1];
    console.log(`   🏁 Road trip completed: ${route.name}`);
    console.log(`   📍 Final destination: ${finalDestination.name} (${finalDestination.x_percent.toFixed(1)}%, ${finalDestination.y_percent.toFixed(1)}%)`);
    console.log(`   🎉 Total distance: ${route.totalMiles} miles in ${route.estimatedDriveTimeHours} hours`);
  }
  
  /**
   * Activate a specific road trip route (manual control)
   */
  private activateRoadTripRoute(route: RoadTripRoute): void {
    // For manual route activation, don't await - fire and forget
    this.executeRoadTripRoute(route).catch(error => {
      console.warn('Manual road trip activation error:', error);
    });
  }
  
  /**
   * Generate CSS keyframes for a flight route
   */
  // Removed: CSS keyframe generation obsolete in JS panner mode
  
  /**
   * Generate random offset for more natural flight movement
   */
  // Removed leftover helper from CSS animation era
  
  /**
   * Get information about available road trip routes
   */
  getRoadTripRoutes(): RoadTripRoute[] {
    return [...this.roadTripRoutes];
  }
  
  /**
   * Set a specific road trip route by ID
   */
  setRoadTripRoute(routeId: string): boolean {
    const route = this.roadTripRoutes.find(r => r.id === routeId);
    if (route) {
      // Stop the automatic route manager and activate this specific route
      this.routeManager.stop();
      this.activateRoadTripRoute(route);
      return true;
    }
    return false;
  }
  
  /**
   * Set a specific road trip route by index
   */
  setRouteByIndex(index: number): boolean {
    this.routeManager.setRoute(index);
    return true;
  }
  
  /**
   * Start automatic route progression
   */
  startRouteProgression(): void {
    this.routeManager.start();
  }
  
  /**
   * Stop automatic route progression
   */
  stopRouteProgression(): void {
    this.routeManager.stop();
  }
  
  /**
   * Get current route information
   */
  getCurrentRoute(): RoadTripRoute | null {
    return this.routeManager.getCurrentRoute();
  }
  
  /**
   * Toggle between geographic and artistic routes
   */
  toggleGeographicMode(): void {
    this.isGeographicMode = !this.isGeographicMode;
    console.log(`🔄 Switched to ${this.isGeographicMode ? 'geographic' : 'artistic'} routes`);
    
    if (this.isGeographicMode) {
      // Switch to geographic mode - start route manager
      this.routeManager.start();
    } else {
      // Switch to artistic mode - stop route manager and use parent implementation
      this.routeManager.stop();
      super.setRandomRoute();
    }
  }
  
  /**
   * Zoom to a specific location/city
   */
  zoomToLocation(locationName: string, zoomLevel: number = 4.0, duration: number = 3000): boolean {
    const waypoint = this.getWaypointByName(locationName);
    if (!waypoint) {
      console.warn(`❌ Location not found: ${locationName}`);
      return false;
    }
    
    console.log(`🔍 Zooming to ${waypoint.name} at ${waypoint.x_percent.toFixed(1)}%, ${waypoint.y_percent.toFixed(1)}%`);
    // Use JS panner directly
    const base = mapPanner.getBaseScale();
    const targetZoom = zoomLevel ? Math.max(base, zoomLevel) : base * 4.0; // tight zoom
    mapPanner.panToPercent(waypoint.x_percent, waypoint.y_percent, { 
      zoom: targetZoom, 
      durationMs: duration,
      easing: this.cruiseControlEasing // Smooth cruise control for manual zoom too
    });
    return true;
  }
  
  /**
   * Get waypoint by name (case insensitive)
   */
  private getWaypointByName(name: string): MapWaypoint | undefined {
    const searchName = name.toLowerCase();
    return Array.from(this.waypoints.values()).find(wp => 
      wp.name.toLowerCase() === searchName || 
      wp.name.toLowerCase().includes(searchName)
    );
  }
  
  /**
   * Create CSS animation to zoom to a specific location
   */
  // Removed: CSS zoom animation obsolete in JS panner mode
  
  /**
   * Quick zoom to major cities
   */
  zoomToCity(cityName: string): boolean {
    const cityAliases: { [key: string]: string } = {
      'ny': 'New York',
      'nyc': 'New York', 
      'sf': 'San Francisco',
      'la': 'Los Angeles',
      'chicago': 'Chicago',
      'chi': 'Chicago',
      'seattle': 'Seattle',
      'miami': 'Miami',
      'denver': 'Denver',
      'dallas': 'Dallas',
      'boston': 'Boston',
      'dc': 'Washington',
      'atlanta': 'Atlanta'
    };
    
    const searchName = cityAliases[cityName.toLowerCase()] || cityName;
    return this.zoomToLocation(searchName, 5.0, 4000);
  }
  
  /**
   * Enhanced initialize method that loads waypoints
   */
  override async initialize(): Promise<void> {
    console.log('🎬 Initializing Geographic Map Background...');
    
    // Ensure JS panner is ready and CSS is suppressed
    await mapPanner.initialize();
    
    // Load waypoints and generate Route 66 FIRST, before parent initialization
    await this.loadWaypoints();
    console.log('✅ Route 66 and other routes are now ready for default selection');
    
    // NOW initialize parent - when it calls setRandomRoute(), Route 66 will be available as default
    super.initialize();
    
    // Set up enhanced debug commands
    this.initializeGeographicDebugCommands();
  }
  
  /**
   * Enhanced debug commands for geographic mode
   */
  private initializeGeographicDebugCommands(): void {
    (window as any).geoFlyover = {
      ...((window as any).mapFlyover || {}),
      zoomFactors: {
        get base() { return mapPanner.getBaseScale(); },
        cruise: 3.0,
        focus: 4.0,
      },
      
      routes: () => {
        console.log('🛣️  American Road Trip Routes:');
        this.roadTripRoutes.forEach((route, index) => {
          const waypointNames = route.waypoints.map(wp => wp.name).join(' → ');
          console.log(`  ${index + 1}. ${route.name} (${route.totalMiles} mi, ${route.estimatedDriveTimeHours}h)`);
          console.log(`     ${waypointNames}`);
          console.log(`     ${route.description} via ${route.highways.join(', ')}`);
        });
      },
      
      waypoints: () => {
        console.log('📍 Available Waypoints:');
        const sortedWaypoints = Array.from(this.waypoints.values()).sort((a, b) => a.name.localeCompare(b.name));
        sortedWaypoints.forEach(wp => {
          console.log(`  • ${wp.name} (${wp.category}) - ${wp.x_percent.toFixed(1)}%, ${wp.y_percent.toFixed(1)}%`);
        });
      },
      
      cities: () => {
        console.log('🏙️  Available Cities for Quick Zoom:');
        const cities = Array.from(this.waypoints.values())
          .filter(wp => wp.category === 'city')
          .sort((a, b) => a.name.localeCompare(b.name));
        cities.forEach(city => {
          console.log(`  • ${city.name} - Try: geoFlyover.zoom('${city.name}')`);
        });
      },
      
      setRoute: (routeId: string | number) => {
        if (typeof routeId === 'number') {
          const success = this.setRouteByIndex(routeId);
          console.log(success ? `✅ Activated route ${routeId + 1}` : `❌ Invalid route index: ${routeId}`);
        } else {
          const success = this.setRoadTripRoute(routeId);
          console.log(success ? `✅ Activated road trip: ${routeId}` : `❌ Route not found: ${routeId}`);
        }
      },
      
      current: () => {
        const route = this.getCurrentRoute();
        if (route) {
          console.log(`🚗 Current road trip: ${route.name}`);
          console.log(`   Route: ${route.waypoints.map(wp => wp.name).join(' → ')}`);
          console.log(`   Distance: ${route.totalMiles} miles via ${route.highways.join(', ')}`);
          console.log(`   Drive time: ${route.estimatedDriveTimeHours} hours (${route.drivingStyle} style)`);
        } else {
          console.log('❌ No current road trip');
        }
        return route;
      },
      
      start: () => {
        this.startRouteProgression();
        console.log('▶️  Started automatic route progression');
      },
      
      stop: () => {
        this.stopRouteProgression();
        console.log('⏹️  Stopped automatic route progression');
      },
      
      next: () => {
        const currentIndex = this.roadTripRoutes.findIndex(r => r.id === this.getCurrentRoute()?.id);
        const nextIndex = (currentIndex + 1) % this.roadTripRoutes.length;
        this.setRouteByIndex(nextIndex);
        console.log(`⏭️  Switched to next road trip: ${this.roadTripRoutes[nextIndex].name}`);
      },
      
      zoom: (locationName: string, zoomLevel?: number, duration?: number) => {
        const waypoint = this.getWaypointByName(locationName);
        if (waypoint) {
          console.log(`🔍 Using coordinates for ${waypoint.name}: ${waypoint.x_percent}%, ${waypoint.y_percent}%`);
        }
        const factors = (window as any).geoFlyover.zoomFactors;
        const level = zoomLevel ?? factors.focus * mapPanner.getBaseScale() / mapPanner.getBaseScale();
        const success = this.zoomToLocation(locationName, level, duration);
        if (!success) {
          console.log('💡 Available locations:');
          this.waypoints.forEach(wp => console.log(`   ${wp.name}`));
        }
        return success;
      },
      
      showData: () => {
        console.log('📊 Current waypoint data being used:');
        Array.from(this.waypoints.entries()).forEach(([id, wp]) => {
          console.log(`${wp.name}: ${wp.x_percent}%, ${wp.y_percent}% (ID: ${id})`);
        });
      },
      
      zoomCity: (cityName: string) => {
        return this.zoomToCity(cityName);
      },
      
      roadTripZoom: (zoomLevel?: number) => {
        if (typeof zoomLevel === 'number') {
          this.roadTripZoomLevel = Math.max(1.0, Math.min(20.0, zoomLevel));
          console.log(`🔍 Road trip zoom level set to ${this.roadTripZoomLevel}x`);
          return this.roadTripZoomLevel;
        }
        console.log(`🔍 Current road trip zoom level: ${this.roadTripZoomLevel}x`);
        return this.roadTripZoomLevel;
      },
      
      cruiseSpeed: (timeCompressionFactor?: number) => {
        if (typeof timeCompressionFactor === 'number') {
          this.timeCompressionFactor = Math.max(0.5, Math.min(50, timeCompressionFactor));
          const gameHoursPerSecond = 1000 / 60 / 60 / this.timeCompressionFactor;
          console.log(`⏰ Time compression set to ${this.timeCompressionFactor} (${gameHoursPerSecond.toFixed(1)} game hours per real second - ultra-leisurely)`);
          return this.timeCompressionFactor;
        }
        const gameHoursPerSecond = 1000 / 60 / 60 / this.timeCompressionFactor;
        console.log(`⏰ Current time compression: ${this.timeCompressionFactor} (${gameHoursPerSecond.toFixed(1)} game hours per real second - ultra-leisurely)`);
        return this.timeCompressionFactor;
      },
      
      route66: () => {
        const route66 = this.roadTripRoutes.find(route => route.id === 'route_66');
        if (route66) {
          console.log('🛣️  Starting Historic Route 66: The Mother Road');
          this.executeRoadTripRoute(route66).catch(error => {
            console.warn('Route 66 execution error:', error);
          });
          return route66;
        } else {
          console.warn('⚠️  Route 66 not available - make sure Route 66 cities are pinned');
          return null;
        }
      },
      
      reload: () => this.loadWaypoints(),
      toggle: () => this.toggleGeographicMode(),
      
      auto: (enabled: boolean = true) => {
        if (enabled) {
          this.startRouteProgression();
          console.log('🔄 Enabled automatic route progression');
        } else {
          this.stopRouteProgression();
          console.log('⏸️  Disabled automatic route progression');
        }
      },
      
      
      roadTripSpeed: (multiplier?: number): number => {
        if (multiplier === undefined) {
          console.log(`🚗 Current road trip speed: ${this.roadTripSpeedMultiplier}x`);
          console.log('   0.5x = Leisurely sightseeing pace');
          console.log('   1.0x = Normal road trip pace');
          console.log('   2.0x = Highway cruising speed');
          console.log('   3.0x = Fast interstate travel');
          return this.roadTripSpeedMultiplier;
        }
        
        if (multiplier <= 0 || multiplier > 5) {
          console.warn('⚠️  Speed multiplier must be between 0.1 and 5.0');
          return this.roadTripSpeedMultiplier;
        }
        
        this.roadTripSpeedMultiplier = multiplier;
        console.log(`🚗 Set road trip speed to ${multiplier}x`);
        
        if (multiplier < 0.8) {
          console.log('🐌 Leisurely sightseeing mode enabled');
        } else if (multiplier > 2.5) {
          console.log('🏃 Fast interstate cruising mode enabled');
        } else {
          console.log('🚗 Normal road trip pacing active');
        }
        
        return this.roadTripSpeedMultiplier;
      },
      
      position: () => {
        const state = mapPanner.getState();
        const imageSize = mapPanner.getImagePixels();
        
        // Calculate current position as percentage of image
        const viewportCenter = {
          x: window.innerWidth / 2,
          y: window.innerHeight / 2
        };
        
        // Convert screen center to image percentage
        const imageX = (-state.tx + viewportCenter.x) / state.scale;
        const imageY = (-state.ty + viewportCenter.y) / state.scale;
        const xPercent = (imageX / imageSize.width) * 100;
        const yPercent = (imageY / imageSize.height) * 100;
        
        console.log('📍 Current Camera Position:');
        console.log(`   Map coordinates: ${xPercent.toFixed(2)}%, ${yPercent.toFixed(2)}%`);
        console.log(`   Zoom level: ${state.scale.toFixed(2)}x`);
        console.log(`   Translation: ${state.tx.toFixed(0)}px, ${state.ty.toFixed(0)}px`);
        
        // Find nearest waypoint
        const waypoints = Array.from(this.waypoints.values());
        let nearestWaypoint: MapWaypoint | null = null;
        let nearestDistance = Infinity;
        
        for (const waypoint of waypoints) {
          const distance = Math.sqrt(
            Math.pow(waypoint.x_percent - xPercent, 2) + 
            Math.pow(waypoint.y_percent - yPercent, 2)
          );
          if (distance < nearestDistance) {
            nearestDistance = distance;
            nearestWaypoint = waypoint;
          }
        }
        
        if (nearestWaypoint !== null) {
          console.log(`   🎯 Nearest location: ${nearestWaypoint.name} (${nearestDistance.toFixed(1)}% away)`);
        }
        
        return { xPercent, yPercent, zoom: state.scale, nearestWaypoint };
      },
      
      debug: (enabled?: boolean) => {
        if (enabled === undefined) {
          console.log(`🐛 Debug mode: ${this.debugMode ? 'ON' : 'OFF'}`);
          console.log('   When ON: Shows real-time position tracking during flights');
          return this.debugMode;
        }
        
        this.debugMode = enabled;
        console.log(`🐛 Debug mode ${enabled ? 'ENABLED' : 'DISABLED'}`);
        if (enabled) {
          console.log('   📍 Will show detailed position tracking during flights');
        } else {
          console.log('   📍 Will show only arrival/departure logging');
        }
        return this.debugMode;
      },
      
      help: () => {
        console.log('\n🛣️  AMERICAN ROAD TRIP CONTROLS:');
        console.log('===============================');
        console.log('roadTrip.waypoints() - List all pinned waypoints');
        console.log('roadTrip.cities() - List cities available for zoom');
        console.log('roadTrip.routes() - List all American road trip routes');
        console.log('roadTrip.route66() - Start the legendary Route 66 (default landing route)');
        console.log('roadTrip.setRoute(id/index) - Start specific route by ID or index');
        console.log('roadTrip.current() - Show current road trip info');
        console.log('roadTrip.start() - Start automatic route progression');
        console.log('roadTrip.stop() - Stop automatic route progression');
        console.log('roadTrip.next() - Skip to next road trip');
        console.log('roadTrip.auto(true/false) - Enable/disable auto progression');
        console.log('roadTrip.roadTripSpeed(multiplier) - Adjust travel speed (0.5x-3.0x)');
        console.log('roadTrip.roadTripZoom(level) - Set zoom level for intimate road trip feel (1.0-15.0, default: 6.5)');
        console.log('roadTrip.cruiseSpeed(factor) - Adjust time compression for ultra-leisurely cruising (0.5-50, default: 1.8)');
        console.log('roadTrip.position() - Show current camera position & nearest location');
        console.log('roadTrip.debug(true/false) - Enable/disable detailed position tracking');
        console.log('roadTrip.zoom("New York") - Zoom to specific location');
        console.log('roadTrip.zoomCity("nyc") - Quick zoom to major cities');
        console.log('roadTrip.reload() - Reload waypoints from server');
        console.log('roadTrip.toggle() - Toggle road trip/artistic modes');
        console.log('roadTrip.help() - Show this help');
        console.log('\n🔍 Quick Examples:');
        console.log('roadTrip.route66() // Start the legendary Mother Road (default)');
        console.log('roadTrip.roadTripZoom(8.0) // Get even closer to the ground');
        console.log('roadTrip.cruiseSpeed(1.0) // Even more leisurely cruise control');
        console.log('roadTrip.auto(false) // Disable auto progression');
        console.log('roadTrip.roadTripSpeed(0.7) // Leisurely sightseeing pace');
        console.log('roadTrip.roadTripSpeed(2.0) // Highway cruising speed');  
        console.log('roadTrip.position() // Where am I right now?');
        console.log('roadTrip.debug(true) // Enable detailed tracking');
        console.log('roadTrip.next() // Next road trip');
        console.log('roadTrip.zoomCity("chicago") // Chicago shortcut');
        console.log('roadTrip.current() // Show current trip info\n');
      }
    };
    
    // Also add alias under the old name for compatibility
    (window as any).geoFlyover = (window as any).roadTrip;
    
    console.log('🛣️  American Road Trip System initialized! Type roadTrip.help() for controls.');
  }
}

// Create and export the enhanced instance
// Since we made the constructor protected, we can now extend and instantiate
export const geographicMapBackground = new GeographicMapBackground();

