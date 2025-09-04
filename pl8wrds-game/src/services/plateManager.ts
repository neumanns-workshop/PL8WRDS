// Plate management service for PL8WRDS
import { GameData, Plate, WordDictionary } from '../types/game';
import { SolutionProcessorService } from './solutionProcessor';
import { GameStatisticsService } from './gameStatistics';

/**
 * Service responsible for plate creation, retrieval, and filtering
 * Handles plate management operations and data transformation
 */
export class PlateManagerService {
  private static instance: PlateManagerService;
  private solutionProcessor: SolutionProcessorService;
  private statisticsService: GameStatisticsService;

  constructor() {
    this.solutionProcessor = SolutionProcessorService.getInstance();
    this.statisticsService = GameStatisticsService.getInstance();
  }

  static getInstance(): PlateManagerService {
    if (!PlateManagerService.instance) {
      PlateManagerService.instance = new PlateManagerService();
    }
    return PlateManagerService.instance;
  }

  /**
   * Create a Plate object from raw data
   */
  createPlateFromData(id: string, plateData: any, wordDictionary: WordDictionary): Plate {
    if (!wordDictionary) {
      throw new Error('Word dictionary not loaded');
    }

    const solutions = this.solutionProcessor.processSolutions(plateData.solutions, wordDictionary, id);

    // Calculate plate statistics
    const solution_count = solutions.length;
    
    // Calculate difficulty based on solution count
    const difficulty = this.statisticsService.calculatePlateDifficulty(solution_count);

    return {
      id,
      letters: plateData.letters.join('').toUpperCase(), // Convert array to string
      difficulty: difficulty,
      solution_count: solution_count,
      solutions,
    };
  }

  /**
   * Get a random plate
   */
  getRandomPlate(gameData: GameData | null, wordDictionary: WordDictionary | null): Plate | null {
    if (!gameData || !wordDictionary) return null;

    const randomIndex = Math.floor(Math.random() * gameData.plates.length);
    const plateData = gameData.plates[randomIndex];

    if (!plateData) return null;

    return this.createPlateFromData(randomIndex.toString(), plateData, wordDictionary);
  }

  /**
   * Get a plate by ID
   */
  getPlateById(id: string, gameData: GameData | null, wordDictionary: WordDictionary | null): Plate | null {
    if (!gameData || !wordDictionary) return null;

    const index = parseInt(id);
    if (isNaN(index) || index < 0 || index >= gameData.plates.length) return null;

    const plateData = gameData.plates[index];
    return this.createPlateFromData(id, plateData, wordDictionary);
  }

  /**
   * Get plates by difficulty tier
   */
  getPlatesByDifficulty(tier: 'ultra_hard' | 'very_hard' | 'hard' | 'medium' | 'easy', gameData: GameData | null, wordDictionary: WordDictionary | null): Plate[] {
    if (!gameData || !wordDictionary) return [];

    const difficultyRanges = {
      ultra_hard: [90, 100],
      very_hard: [80, 89],
      hard: [60, 79], 
      medium: [30, 59],
      easy: [0, 29]
    };
    
    const [minDifficulty, maxDifficulty] = difficultyRanges[tier];
    
    // Get all plates and filter by calculated difficulty
    const plates = gameData.plates
      .map((plateData, index) => this.createPlateFromData(index.toString(), plateData, wordDictionary))
      .filter(Boolean) as Plate[];
    
    return plates.filter(plate => 
      plate.difficulty >= minDifficulty && plate.difficulty <= maxDifficulty
    );
  }

  /**
   * Get starter plates (good for beginners)
   */
  getStarterPlates(count: number = 5, gameData: GameData | null, wordDictionary: WordDictionary | null): Plate[] {
    if (!gameData || !wordDictionary) return [];

    // Get easy plates with high solution counts
    const easyPlates = this.getPlatesByDifficulty('easy', gameData, wordDictionary);
    const starterPlates = easyPlates
      .filter(plate => plate.solution_count > 200) // Lots of solutions
      .sort((a, b) => b.solution_count - a.solution_count)
      .slice(0, count);

    return starterPlates;
  }
}

export default PlateManagerService;