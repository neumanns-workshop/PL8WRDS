// Collection analytics, statistics, sorting, and filtering
import { CollectedPlate, CollectionStats, SortOption, DifficultyTier } from './types';
import { ProgressStorageService } from './ProgressStorageService';

export class CollectionAnalyticsService {
  
  /**
   * Get collected plates sorted by various criteria
   */
  static getCollectedPlates(sortBy: SortOption = 'recent'): CollectedPlate[] {
    const progress = ProgressStorageService.loadProgress();
    const plates = Object.values(progress.collectedPlates);

    return this.sortPlates(plates, sortBy);
  }

  /**
   * Get collection statistics
   */
  static getCollectionStats(): CollectionStats {
    const progress = ProgressStorageService.loadProgress();
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
    const difficultyBreakdown = this.calculateDifficultyBreakdown(plates);

    return {
      totalPlates: progress.totalPlatesFound,
      totalWords: progress.totalWordsFound,
      totalScore: progress.totalScore,
      averageCompletion: Math.round(totalCompletion / plates.length),
      difficultyBreakdown
    };
  }

  /**
   * Filter plates by difficulty tier
   */
  static filterByDifficulty(plates: CollectedPlate[], difficultyTier: string): CollectedPlate[] {
    if (difficultyTier === 'all') {
      return plates;
    }
    
    return plates.filter(plate => this.getDifficultyTier(plate.difficulty) === difficultyTier);
  }

  /**
   * Get difficulty tier for a difficulty value
   */
  static getDifficultyTier(difficulty: number): DifficultyTier {
    if (difficulty >= 90) return 'Ultra Hard';
    if (difficulty >= 80) return 'Very Hard';
    if (difficulty >= 60) return 'Hard';
    if (difficulty >= 30) return 'Medium';
    return 'Easy';
  }

  /**
   * Sort plates by given criteria
   */
  private static sortPlates(plates: CollectedPlate[], sortBy: SortOption): CollectedPlate[] {
    const sortedPlates = [...plates]; // Create copy to avoid mutating original

    switch (sortBy) {
      case 'recent':
        return sortedPlates.sort((a, b) => 
          new Date(b.lastPlayedDate).getTime() - new Date(a.lastPlayedDate).getTime()
        );
      case 'completion':
        return sortedPlates.sort((a, b) => b.completionPercentage - a.completionPercentage);
      case 'difficulty':
        return sortedPlates.sort((a, b) => b.difficulty - a.difficulty); // Higher difficulty = harder
      case 'letters':
        return sortedPlates.sort((a, b) => a.letters.localeCompare(b.letters));
      default:
        return sortedPlates;
    }
  }

  /**
   * Calculate difficulty breakdown statistics
   */
  private static calculateDifficultyBreakdown(plates: CollectedPlate[]): { [key: string]: number } {
    const breakdown: { [key: string]: number } = {};
    
    plates.forEach(plate => {
      const difficultyTier = this.getDifficultyTier(plate.difficulty);
      breakdown[difficultyTier] = (breakdown[difficultyTier] || 0) + 1;
    });

    return breakdown;
  }
}