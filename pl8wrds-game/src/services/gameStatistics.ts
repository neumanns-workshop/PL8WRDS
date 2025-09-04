// Game statistics service for PL8WRDS
import { GameData, WordDictionary } from '../types/game';

/**
 * Service responsible for calculating game statistics and difficulty metrics
 * Handles statistical calculations and plate difficulty computation
 */
export class GameStatisticsService {
  private static instance: GameStatisticsService;

  static getInstance(): GameStatisticsService {
    if (!GameStatisticsService.instance) {
      GameStatisticsService.instance = new GameStatisticsService();
    }
    return GameStatisticsService.instance;
  }

  /**
   * Calculate plate difficulty based on solution count
   */
  calculatePlateDifficulty(solutionCount: number): number {
    // Calculate difficulty based on solution count (fewer solutions = harder)
    if (solutionCount <= 10) return 95;
    else if (solutionCount <= 25) return 85; 
    else if (solutionCount <= 50) return 70;
    else if (solutionCount <= 100) return 50;
    else if (solutionCount <= 200) return 30;
    else if (solutionCount <= 400) return 15;
    else return 5;
  }

  /**
   * Get game statistics
   */
  getGameStats(gameData: GameData | null, wordDictionary: WordDictionary | null) {
    if (!gameData || !wordDictionary) {
      return {
        totalPlates: 0,
        totalSolutions: 0,
        uniqueWords: 0,
        version: 'ultra_optimized',
      };
    }

    const totalPlates = gameData.plates.length;
    const totalSolutions = gameData.plates.reduce(
      (total, plate) => total + Object.keys(plate.solutions).length, 0
    );
    const uniqueWords = Object.keys(wordDictionary).length;

    return {
      totalPlates,
      totalSolutions,
      uniqueWords,
      version: 'ultra_optimized',
    };
  }
}

export default GameStatisticsService;