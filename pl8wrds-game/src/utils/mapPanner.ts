// MapPanner: precise, interruptible pixel-based pan/zoom of the vintage map background
// Renders a fixed, full-screen container with a single image layer transformed via CSS

import vintageMapImage from '../assets/1918_AAA_General_Map_of_Transcontinental_Routes.jpg';

export type EasingFunction = (t: number) => number;

export interface PanOptions {
  zoom?: number;             // target zoom (scale), default keeps current
  durationMs?: number;       // duration in ms, default 2000
  easing?: EasingFunction;   // easing function
  clampToEdges?: boolean;    // clamp to keep image covering viewport, default true
}

export interface WaypointPercent {
  x_percent: number;
  y_percent: number;
}

export class MapPanner {
  private static instance: MapPanner | null = null;

  private containerEl: HTMLDivElement | null = null;
  private imageEl: HTMLImageElement | null = null;

  private imageNaturalWidth = 0;
  private imageNaturalHeight = 0;
  private viewportWidth = 0;
  private viewportHeight = 0;

  // Current transform state
  private currentScale = 1.0;
  private currentTx = 0; // translateX in px
  private currentTy = 0; // translateY in px

  // Scaling constraints
  private baseCoverScale = 1.0; // minimal scale so the image covers viewport
  private minScale = 0.1;
  private maxScale = 3.0;
  private initialZoomFactor = 3.5; // start slightly closer by default

  // RAF animation
  private animAbort: (() => void) | null = null;

  static getInstance(): MapPanner {
    if (!MapPanner.instance) {
      MapPanner.instance = new MapPanner();
    }
    return MapPanner.instance;
  }

  async initialize(): Promise<void> {
    if (this.containerEl) return; // already initialized

    // Disable CSS ::before background
    document.body.classList.add('no-css-bg');

    // Create container
    const container = document.createElement('div');
    container.id = 'map-pan-container';
    container.style.position = 'fixed';
    container.style.inset = '0';
    container.style.overflow = 'hidden';
    container.style.zIndex = '-2';
    container.style.pointerEvents = 'none';
    container.style.willChange = 'transform';

    // Create image
    const img = document.createElement('img');
    img.id = 'map-pan-image';
    img.src = vintageMapImage;
    img.alt = 'Vintage Map Background';
    img.style.position = 'absolute';
    img.style.top = '0';
    img.style.left = '0';
    img.style.transformOrigin = '0 0'; // transform relative to top-left
    img.style.willChange = 'transform';
    img.decoding = 'async';
    img.loading = 'eager';

    container.appendChild(img);
    document.body.appendChild(container);

    this.containerEl = container;
    this.imageEl = img;

    await this.measureImage();
    this.measureViewport();

    // Force-remove any CSS-injected background image to avoid visual stacking
    const cssBg = document.getElementById('dynamic-map-bg-image');
    if (cssBg && cssBg.parentElement) {
      cssBg.parentElement.removeChild(cssBg);
    }

    // Compute base scale to ensure the image covers the viewport
    this.baseCoverScale = this.computeCoverScale();
    this.minScale = this.baseCoverScale;
    this.maxScale = this.baseCoverScale * 10;
    this.currentScale = Math.min(this.maxScale, this.baseCoverScale * this.initialZoomFactor);

    window.addEventListener('resize', this.handleResize, { passive: true });

    // Initial fit: center US by default (approx at 55% x, 55% y of image)
    const midX = this.imageNaturalWidth * 0.55;
    const midY = this.imageNaturalHeight * 0.55;
    const { tx, ty } = this.computeCentering(midX, midY, this.currentScale);
    this.applyTransform(tx, ty, this.currentScale);
  }

  private handleResize = () => {
    this.measureViewport();
    // Recompute cover scale and constraints on resize
    this.baseCoverScale = this.computeCoverScale();
    this.minScale = this.baseCoverScale;
    this.maxScale = this.baseCoverScale * 10;
    // Re-clamp on resize to avoid blank edges
    const { tx, ty } = this.clampTranslation(this.currentTx, this.currentTy, this.currentScale);
    this.applyTransform(tx, ty, this.currentScale);
  };

  private async measureImage(): Promise<void> {
    if (!this.imageEl) return;
    if (this.imageEl.complete && this.imageEl.naturalWidth > 0) {
      this.imageNaturalWidth = this.imageEl.naturalWidth;
      this.imageNaturalHeight = this.imageEl.naturalHeight;
      return;
    }
    await new Promise<void>((resolve) => {
      if (!this.imageEl) return resolve();
      this.imageEl.onload = () => {
        if (!this.imageEl) return resolve();
        this.imageNaturalWidth = this.imageEl.naturalWidth;
        this.imageNaturalHeight = this.imageEl.naturalHeight;
        resolve();
      };
      this.imageEl.onerror = () => resolve();
    });
  }

  private measureViewport(): void {
    this.viewportWidth = window.innerWidth;
    this.viewportHeight = window.innerHeight;
  }

  private applyTransform(tx: number, ty: number, scale: number): void {
    if (!this.imageEl) return;
    const clampedScale = this.clampScale(scale);
    const { tx: clampedTx, ty: clampedTy } = this.clampTranslation(tx, ty, clampedScale);
    this.currentTx = clampedTx;
    this.currentTy = clampedTy;
    this.currentScale = clampedScale;
    this.imageEl.style.transform = `translate3d(${this.currentTx}px, ${this.currentTy}px, 0) scale(${this.currentScale})`;
  }

  private clampTranslation(tx: number, ty: number, scale: number): { tx: number; ty: number } {
    const contentW = this.imageNaturalWidth * scale;
    const contentH = this.imageNaturalHeight * scale;
    const minTx = Math.min(0, this.viewportWidth - contentW);
    const maxTx = 0;
    const minTy = Math.min(0, this.viewportHeight - contentH);
    const maxTy = 0;
    const clampedTx = Math.max(minTx, Math.min(maxTx, tx));
    const clampedTy = Math.max(minTy, Math.min(maxTy, ty));
    return { tx: clampedTx, ty: clampedTy };
  }

  private clampScale(scale: number): number {
    return Math.max(this.minScale, Math.min(this.maxScale, scale));
  }

  private computeCoverScale(): number {
    if (this.imageNaturalWidth === 0 || this.imageNaturalHeight === 0) return 1.0;
    const sx = this.viewportWidth / this.imageNaturalWidth;
    const sy = this.viewportHeight / this.imageNaturalHeight;
    return Math.max(sx, sy);
  }

  private computeCentering(xPixel: number, yPixel: number, scale: number): { tx: number; ty: number } {
    // Center the given pixel at viewport center
    const cx = this.viewportWidth / 2;
    const cy = this.viewportHeight / 2;
    const tx = cx - xPixel * scale;
    const ty = cy - yPixel * scale;
    return this.clampTranslation(tx, ty, scale);
  }

  private defaultEasing: EasingFunction = (t: number) => {
    // easeInOutCubic
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  };

  private animateTo(targetTx: number, targetTy: number, targetScale: number, durationMs: number, easing: EasingFunction): Promise<void> {
    if (this.animAbort) this.animAbort();
    let rafId = 0;
    const startTime = performance.now();
    const startTx = this.currentTx;
    const startTy = this.currentTy;
    const startScale = this.currentScale;

    return new Promise<void>((resolve) => {
      let aborted = false;
      this.animAbort = () => { aborted = true; cancelAnimationFrame(rafId); };

      const step = () => {
        if (aborted) return;
        const now = performance.now();
        const t = Math.min(1, (now - startTime) / durationMs);
        const k = easing(t);
        const tx = startTx + (targetTx - startTx) * k;
        const ty = startTy + (targetTy - startTy) * k;
        const scale = startScale + (targetScale - startScale) * k;
        this.applyTransform(tx, ty, scale);
        if (t < 1) {
          rafId = requestAnimationFrame(step);
        } else {
          this.animAbort = null;
          resolve();
        }
      };
      rafId = requestAnimationFrame(step);
    });
  }

  async panToPixel(xPixel: number, yPixel: number, options: PanOptions = {}): Promise<void> {
    if (!this.imageEl) await this.initialize();
    const desiredZoom = options.zoom ?? this.currentScale;
    const zoom = this.clampScale(desiredZoom);
    const durationMs = options.durationMs ?? 2000;
    const easing = options.easing ?? this.defaultEasing;
    const { tx, ty } = this.computeCentering(xPixel, yPixel, zoom);
    await this.animateTo(tx, ty, zoom, durationMs, easing);
  }

  async panToPercent(xPercent: number, yPercent: number, options: PanOptions = {}): Promise<void> {
    if (!this.imageEl) await this.initialize();
    const xPixel = (xPercent / 100) * this.imageNaturalWidth;
    const yPixel = (yPercent / 100) * this.imageNaturalHeight;
    return this.panToPixel(xPixel, yPixel, options);
  }

  async followPathPercent(waypoints: WaypointPercent[], options: PanOptions & { perLegMs?: number } = {}): Promise<void> {
    if (waypoints.length === 0) return;
    const perLegMs = options.perLegMs ?? 2000;
    const zoom = options.zoom ?? this.currentScale;
    for (const wp of waypoints) {
      const legOptions: PanOptions = { zoom, durationMs: perLegMs };
      if (options.easing) {
        legOptions.easing = options.easing;
      }
      await this.panToPercent(wp.x_percent, wp.y_percent, legOptions);
    }
  }

  getImagePixels(): { width: number; height: number } {
    return { width: this.imageNaturalWidth, height: this.imageNaturalHeight };
  }

  getState(): { tx: number; ty: number; scale: number } {
    return { tx: this.currentTx, ty: this.currentTy, scale: this.currentScale };
  }

  getBaseScale(): number {
    return this.baseCoverScale;
  }

  // Instantly position without animation
  setInstantPercent(xPercent: number, yPercent: number, zoom?: number): void {
    if (!this.imageEl) return;
    const xPixel = (xPercent / 100) * this.imageNaturalWidth;
    const yPixel = (yPercent / 100) * this.imageNaturalHeight;
    const desiredZoom = zoom ?? this.currentScale;
    const z = this.clampScale(desiredZoom);
    const { tx, ty } = this.computeCentering(xPixel, yPixel, z);
    this.currentScale = z;
    this.currentTx = tx;
    this.currentTy = ty;
    this.imageEl!.style.transform = `translate3d(${tx}px, ${ty}px, 0) scale(${z})`;
  }
}

export const mapPanner = MapPanner.getInstance();


