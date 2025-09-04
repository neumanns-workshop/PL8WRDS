// Game data service for client-side PL8WRDS - Main facade service
import { GameData, WordDictionary, Plate, Solution } from '../types/game';
import { DataLoaderService } from './dataLoader';
import { PlateManagerService } from './plateManager';
import { WordValidatorService } from './wordValidator';
import { GameStatisticsService } from './gameStatistics';

/**
 * Main GameDataService - Facade pattern that coordinates specialized services
 * Maintains the same public API while delegating to focused service modules
 */
export class GameDataService {
  private static instance: GameDataService;
  private dataLoader: DataLoaderService;
  private plateManager: PlateManagerService;
  private wordValidator: WordValidatorService;
  private statisticsService: GameStatisticsService;

  constructor() {
    this.dataLoader = DataLoaderService.getInstance();
    this.plateManager = PlateManagerService.getInstance();
    this.wordValidator = WordValidatorService.getInstance();
    this.statisticsService = GameStatisticsService.getInstance();
  }

  static getInstance(): GameDataService {
    if (!GameDataService.instance) {
      GameDataService.instance = new GameDataService();
    }
    return GameDataService.instance;
  }

  /**
   * Load the word dictionary
   */
  async loadWordDictionary(): Promise<WordDictionary> {
    return this.dataLoader.loadWordDictionary();
  }

  /**
   * Load the complete game data from the compressed file
   */
  async loadGameData(): Promise<GameData> {
    return this.dataLoader.loadGameData();
  }

  /**
   * Get a random plate
   */
  getRandomPlate(): Plate | null {
    return this.plateManager.getRandomPlate(
      this.dataLoader.getGameData(),
      this.dataLoader.getWordDictionary()
    );
  }

  /**
   * Get a plate by ID
   */
  getPlateById(id: string): Plate | null {
    return this.plateManager.getPlateById(
      id,
      this.dataLoader.getGameData(),
      this.dataLoader.getWordDictionary()
    );
  }

  /**
   * Get plates by difficulty tier
   */
  getPlatesByDifficulty(tier: 'ultra_hard' | 'very_hard' | 'hard' | 'medium' | 'easy'): Plate[] {
    return this.plateManager.getPlatesByDifficulty(
      tier,
      this.dataLoader.getGameData(),
      this.dataLoader.getWordDictionary()
    );
  }


  /**
   * Validate if a word contains plate letters in correct order
   */
  static validateWord(word: string, plate: string): boolean {
    return WordValidatorService.getInstance().validateWord(word, plate);
  }

  /**
   * Check if a word is a valid solution for a plate
   */
  checkWordSolution(word: string, plate: Plate): Solution | null {
    return this.wordValidator.checkWordSolution(word, plate);
  }

  /**
   * Get starter plates (good for beginners)
   */
  getStarterPlates(count: number = 5): Plate[] {
    return this.plateManager.getStarterPlates(
      count,
      this.dataLoader.getGameData(),
      this.dataLoader.getWordDictionary()
    );
  }



  /**
   * Get game statistics
   */
  getGameStats() {
    return this.statisticsService.getGameStats(
      this.dataLoader.getGameData(),
      this.dataLoader.getWordDictionary()
    );
  }

  /**
   * Get word dictionary for external access
   */
  getWordDictionary(): WordDictionary | null {
    return this.dataLoader.getWordDictionary();
  }
}

export default GameDataService;
