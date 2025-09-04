// Data loading and caching service for PL8WRDS
import * as pako from 'pako';
import { GameData, WordDictionary } from '../types/game';

/**
 * Service responsible for loading and caching game data and word dictionary
 * Handles decompression, HTTP requests, and singleton caching
 */
export class DataLoaderService {
  private static instance: DataLoaderService;
  private gameData: GameData | null = null;
  private wordDictionary: WordDictionary | null = null;
  private isLoading = false;

  static getInstance(): DataLoaderService {
    if (!DataLoaderService.instance) {
      DataLoaderService.instance = new DataLoaderService();
    }
    return DataLoaderService.instance;
  }

  /**
   * Load the word dictionary
   */
  async loadWordDictionary(): Promise<WordDictionary> {
    if (this.wordDictionary) {
      return this.wordDictionary;
    }

    try {
      console.log('Loading word dictionary...');
      const response = await fetch('/words/dictionary.json');
      if (!response.ok) {
        throw new Error(`Failed to fetch word dictionary: ${response.statusText}`);
      }

      this.wordDictionary = await response.json();
      console.log(`Loaded ${Object.keys(this.wordDictionary || {}).length} words in dictionary`);
      return this.wordDictionary!;
    } catch (error) {
      console.error('Failed to load word dictionary:', error);
      throw error;
    }
  }

  /**
   * Load the complete game data from the compressed file
   */
  async loadGameData(): Promise<GameData> {
    if (this.gameData && this.wordDictionary) {
      return this.gameData;
    }

    if (this.isLoading) {
      // Wait for the existing load to complete
      while (this.isLoading) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      return this.gameData!;
    }

    this.isLoading = true;

    try {
      console.log('Loading game data...');
      
      // Load both game data and word dictionary in parallel
      const [gameDataResponse] = await Promise.all([
        fetch('/pl8wrds_complete.json.gz'),
        this.loadWordDictionary()
      ]);

      if (!gameDataResponse.ok) {
        throw new Error(`Failed to fetch game data: ${gameDataResponse.statusText}`);
      }

      const compressedData = await gameDataResponse.arrayBuffer();
      const decompressed = pako.ungzip(compressedData, { to: 'string' });
      this.gameData = JSON.parse(decompressed);
      
      const plateCount = this.gameData?.plates?.length || 0;
      const solutionCount = this.gameData?.plates?.reduce(
        (total, plate) => total + Object.keys(plate.solutions).length, 0
      ) || 0;
      
      console.log(`Loaded ${plateCount} plates with ${solutionCount} solutions`);
      return this.gameData!;
    } catch (error) {
      console.error('Failed to load game data:', error);
      throw error;
    } finally {
      this.isLoading = false;
    }
  }

  /**
   * Get cached game data (null if not loaded)
   */
  getGameData(): GameData | null {
    return this.gameData;
  }

  /**
   * Get cached word dictionary (null if not loaded)
   */
  getWordDictionary(): WordDictionary | null {
    return this.wordDictionary;
  }

  /**
   * Check if data is currently being loaded
   */
  getIsLoading(): boolean {
    return this.isLoading;
  }
}

export default DataLoaderService;