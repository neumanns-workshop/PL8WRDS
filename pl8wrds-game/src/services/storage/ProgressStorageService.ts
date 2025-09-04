// User progress and plate collection management
import { UserProgress, CollectedPlate } from './types';
import { LocalStorageService } from './LocalStorageService';

export class ProgressStorageService {
  private static readonly VERSION = '1.0.0';

  /**
   * Load user progress from localStorage
   */
  static loadProgress(): UserProgress {
    const stored = LocalStorageService.get<UserProgress>(LocalStorageService.getProgressKey());
    
    if (!stored) {
      return this.getDefaultProgress();
    }
    
    // Check version and migrate if needed
    if (stored.version !== this.VERSION) {
      return this.migrateProgress(stored);
    }
    
    return stored;
  }

  /**
   * Save user progress to localStorage
   */
  static saveProgress(progress: UserProgress): boolean {
    progress.lastPlayed = new Date().toISOString();
    progress.version = this.VERSION;
    return LocalStorageService.set(LocalStorageService.getProgressKey(), progress);
  }

  /**
   * Add or update a collected plate
   */
  static updateCollectedPlate(
    plateId: string,
    letters: string,
    difficulty: number,
    solutionCount: number,
    foundWords: string[],
    totalScore: number
  ): boolean {
    const progress = this.loadProgress();
    const now = new Date().toISOString();
    
    const existing = progress.collectedPlates[plateId];
    
    // Merge found words (avoid duplicates)
    const allFoundWords = existing 
      ? Array.from(new Set([...existing.foundWords, ...foundWords]))
      : foundWords;
    
    progress.collectedPlates[plateId] = {
      plateId,
      letters,
      difficulty,
      solution_count: solutionCount,
      foundWords: allFoundWords,
      totalScore,
      firstFoundDate: existing?.firstFoundDate || now,
      lastPlayedDate: now,
      completionPercentage: Math.round((allFoundWords.length / solutionCount) * 100)
    };

    // Update totals
    this.recalculateProgress(progress);
    return this.saveProgress(progress);
  }

  /**
   * Get a specific collected plate
   */
  static getCollectedPlate(plateId: string): CollectedPlate | null {
    const progress = this.loadProgress();
    return progress.collectedPlates[plateId] || null;
  }

  /**
   * Clear all progress
   */
  static clearProgress(): boolean {
    return LocalStorageService.remove(LocalStorageService.getProgressKey());
  }

  /**
   * Get default empty progress
   */
  private static getDefaultProgress(): UserProgress {
    return {
      collectedPlates: {},
      totalPlatesFound: 0,
      totalWordsFound: 0,
      totalScore: 0,
      lastPlayed: new Date().toISOString(),
      version: this.VERSION
    };
  }

  /**
   * Handle data migration between versions
   */
  private static migrateProgress(oldProgress: any): UserProgress {
    // Future version migration logic
    console.log('Migrating progress from version:', oldProgress.version);
    return this.getDefaultProgress();
  }

  /**
   * Recalculate totals in progress object
   */
  private static recalculateProgress(progress: UserProgress): void {
    const plates = Object.values(progress.collectedPlates);
    progress.totalPlatesFound = plates.length;
    progress.totalWordsFound = plates.reduce((sum, plate) => sum + plate.foundWords.length, 0);
    progress.totalScore = plates.reduce((sum, plate) => sum + plate.totalScore, 0);
  }
}