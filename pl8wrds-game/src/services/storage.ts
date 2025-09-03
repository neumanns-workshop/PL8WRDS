// Local storage service for user progress and collections

export interface CollectedPlate {
  plateId: string;
  letters: string;
  difficulty: number;
  solution_count: number;
  foundWords: string[];
  totalScore: number;
  firstFoundDate: string; // ISO date string
  lastPlayedDate: string; // ISO date string
  completionPercentage: number; // 0-100
}

export interface UserProgress {
  collectedPlates: { [plateId: string]: CollectedPlate };
  totalPlatesFound: number;
  totalWordsFound: number;
  totalScore: number;
  lastPlayed: string; // ISO date string
  version: string; // For future data migration
}

class StorageService {
  private static readonly STORAGE_KEY = 'pl8wrds_progress';
  private static readonly VERSION = '1.0.0';

  /**
   * Load user progress from localStorage
   */
  static loadProgress(): UserProgress {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (!stored) {
        return this.getDefaultProgress();
      }

      const progress = JSON.parse(stored) as UserProgress;
      
      // Check version and migrate if needed
      if (progress.version !== this.VERSION) {
        return this.migrateProgress(progress);
      }
      
      return progress;
    } catch (error) {
      console.warn('Failed to load progress from localStorage:', error);
      return this.getDefaultProgress();
    }
  }

  /**
   * Save user progress to localStorage
   */
  static saveProgress(progress: UserProgress): void {
    try {
      progress.lastPlayed = new Date().toISOString();
      progress.version = this.VERSION;
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(progress));
    } catch (error) {
      console.warn('Failed to save progress to localStorage:', error);
    }
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
  ): void {
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
    this.saveProgress(progress);
  }

  /**
   * Get collected plates sorted by various criteria
   */
  static getCollectedPlates(sortBy: 'recent' | 'completion' | 'difficulty' | 'letters' = 'recent'): CollectedPlate[] {
    const progress = this.loadProgress();
    const plates = Object.values(progress.collectedPlates);

    switch (sortBy) {
      case 'recent':
        return plates.sort((a, b) => new Date(b.lastPlayedDate).getTime() - new Date(a.lastPlayedDate).getTime());
      case 'completion':
        return plates.sort((a, b) => b.completionPercentage - a.completionPercentage);
      case 'difficulty':
        return plates.sort((a, b) => b.difficulty - a.difficulty); // Higher difficulty = harder
      case 'letters':
        return plates.sort((a, b) => a.letters.localeCompare(b.letters));
      default:
        return plates;
    }
  }

  /**
   * Get collection statistics
   */
  static getCollectionStats(): {
    totalPlates: number;
    totalWords: number;
    totalScore: number;
    averageCompletion: number;
    difficultyBreakdown: { [key: string]: number };
  } {
    const progress = this.loadProgress();
    const plates = Object.values(progress.collectedPlates);
    
    if (plates.length === 0) {
      return {
        totalPlates: 0,
        totalWords: 0,
        totalScore: 0,
        averageCompletion: 0,
        difficultyBreakdown: {}
      };
    }

    const totalCompletion = plates.reduce((sum, plate) => sum + plate.completionPercentage, 0);
    const difficultyBreakdown: { [key: string]: number } = {};
    
    plates.forEach(plate => {
      const difficultyTier = this.getDifficultyTier(plate.difficulty);
      difficultyBreakdown[difficultyTier] = (difficultyBreakdown[difficultyTier] || 0) + 1;
    });

    return {
      totalPlates: progress.totalPlatesFound,
      totalWords: progress.totalWordsFound,
      totalScore: progress.totalScore,
      averageCompletion: Math.round(totalCompletion / plates.length),
      difficultyBreakdown
    };
  }

  /**
   * Clear all progress (for testing or reset)
   */
  static clearProgress(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }

  /**
   * Export progress as JSON (for backup)
   */
  static exportProgress(): string {
    const progress = this.loadProgress();
    return JSON.stringify(progress, null, 2);
  }

  /**
   * Import progress from JSON (for restore)
   */
  static importProgress(jsonData: string): boolean {
    try {
      const progress = JSON.parse(jsonData) as UserProgress;
      this.saveProgress(progress);
      return true;
    } catch (error) {
      console.error('Failed to import progress:', error);
      return false;
    }
  }

  // Private helper methods
  
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

  private static migrateProgress(oldProgress: any): UserProgress {
    // Future version migration logic
    console.log('Migrating progress from version:', oldProgress.version);
    return this.getDefaultProgress();
  }

  private static recalculateProgress(progress: UserProgress): void {
    const plates = Object.values(progress.collectedPlates);
    progress.totalPlatesFound = plates.length;
    progress.totalWordsFound = plates.reduce((sum, plate) => sum + plate.foundWords.length, 0);
    progress.totalScore = plates.reduce((sum, plate) => sum + plate.totalScore, 0);
  }

  private static getDifficultyTier(difficulty: number): string {
    if (difficulty >= 90) return 'Ultra Hard';
    if (difficulty >= 80) return 'Very Hard';
    if (difficulty >= 60) return 'Hard';
    if (difficulty >= 30) return 'Medium';
    return 'Easy';
  }
}

export default StorageService;
