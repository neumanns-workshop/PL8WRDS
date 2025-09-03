// Game data service for client-side PL8WRDS
import * as pako from 'pako';
import { GameData, WordDictionary, Plate, Solution } from '../types/game';

export class GameDataService {
  private static instance: GameDataService;
  private gameData: GameData | null = null;
  private wordDictionary: WordDictionary | null = null;
  private isLoading = false;

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
   * Get a random plate
   */
  getRandomPlate(): Plate | null {
    if (!this.gameData) return null;

    const randomIndex = Math.floor(Math.random() * this.gameData.plates.length);
    const plateData = this.gameData.plates[randomIndex];

    if (!plateData) return null;

    return this.createPlateFromData(randomIndex.toString(), plateData);
  }

  /**
   * Get a plate by ID
   */
  getPlateById(id: string): Plate | null {
    if (!this.gameData) return null;

    const index = parseInt(id);
    if (isNaN(index) || index < 0 || index >= this.gameData.plates.length) return null;

    const plateData = this.gameData.plates[index];
    return this.createPlateFromData(id, plateData);
  }

  /**
   * Get plates by difficulty tier
   */
  getPlatesByDifficulty(tier: 'ultra_hard' | 'very_hard' | 'hard' | 'medium' | 'easy'): Plate[] {
    if (!this.gameData) return [];

    const difficultyRanges = {
      ultra_hard: [90, 100],
      very_hard: [80, 89],
      hard: [60, 79], 
      medium: [30, 59],
      easy: [0, 29]
    };
    
    const [minDifficulty, maxDifficulty] = difficultyRanges[tier];
    
    // Get all plates and filter by calculated difficulty
    const plates = this.gameData.plates
      .map((plateData, index) => this.createPlateFromData(index.toString(), plateData))
      .filter(Boolean) as Plate[];
    
    return plates.filter(plate => 
      plate.difficulty >= minDifficulty && plate.difficulty <= maxDifficulty
    );
  }

  /**
   * Create a Plate object from raw data
   */
  private createPlateFromData(id: string, plateData: any): Plate {
    if (!this.wordDictionary) {
      throw new Error('Word dictionary not loaded');
    }

    const solutions: Solution[] = Object.entries(plateData.solutions).map(([wordId, infoScore]) => {
      const wordData = this.wordDictionary![wordId];
      
      // Ensure we have valid word data
      if (!wordData || typeof wordData !== 'object' || !wordData.word) {
        throw new Error(`Missing or invalid word data for word ID ${wordId} in plate ${id}`);
      }
      
      // Get pre-computed scores from word dictionary
      const vocabScore = wordData.frequency_score;
      const orthoScore = wordData.orthographic_score;
      const infoScoreNum = typeof infoScore === 'number' ? infoScore : 0;
      
      // Calculate ensemble score as average of component scores
      const ensemble_score = (vocabScore + infoScoreNum + orthoScore) / 3;
      
      return {
        word: wordData.word,
        wordId: parseInt(wordId),
        ensemble_score: Math.round(ensemble_score),
        vocabulary_score: Math.round(vocabScore),
        information_score: Math.round(infoScoreNum),
        orthographic_score: Math.round(orthoScore),
        found: false,
      };
    });

    // Calculate plate statistics
    const solution_count = solutions.length;
    
    // Calculate difficulty based on solution count (fewer solutions = harder)
    let difficulty: number;
    if (solution_count <= 10) difficulty = 95;
    else if (solution_count <= 25) difficulty = 85; 
    else if (solution_count <= 50) difficulty = 70;
    else if (solution_count <= 100) difficulty = 50;
    else if (solution_count <= 200) difficulty = 30;
    else if (solution_count <= 400) difficulty = 15;
    else difficulty = 5;

    return {
      id,
      letters: plateData.letters.join('').toUpperCase(), // Convert array to string
      difficulty: difficulty,
      solution_count: solution_count,
      solutions,
    };
  }

  /**
   * Validate if a word contains plate letters in correct order
   */
  static validateWord(word: string, plate: string): boolean {
    const wordLower = word.toLowerCase();
    const plateLower = plate.toLowerCase();
    
    let plateIndex = 0;
    
    for (let i = 0; i < wordLower.length && plateIndex < plateLower.length; i++) {
      if (wordLower[i] === plateLower[plateIndex]) {
        plateIndex++;
      }
    }
    
    return plateIndex === plateLower.length;
  }

  /**
   * Check if a word is a valid solution for a plate
   */
  checkWordSolution(word: string, plate: Plate): Solution | null {
    if (!GameDataService.validateWord(word, plate.letters)) {
      return null;
    }

    const solution = plate.solutions.find(s => s.word.toLowerCase() === word.toLowerCase());
    return solution || null;
  }

  /**
   * Get starter plates (good for beginners)
   */
  getStarterPlates(count: number = 5): Plate[] {
    if (!this.gameData) return [];

    // Get easy plates with high solution counts
    const easyPlates = this.getPlatesByDifficulty('easy');
    const starterPlates = easyPlates
      .filter(plate => plate.solution_count > 200) // Lots of solutions
      .sort((a, b) => b.solution_count - a.solution_count)
      .slice(0, count);

    return starterPlates;
  }



  /**
   * Get game statistics
   */
  getGameStats() {
    if (!this.gameData || !this.wordDictionary) {
      return {
        totalPlates: 0,
        totalSolutions: 0,
        uniqueWords: 0,
        version: 'ultra_optimized',
      };
    }

    const totalPlates = this.gameData.plates.length;
    const totalSolutions = this.gameData.plates.reduce(
      (total, plate) => total + Object.keys(plate.solutions).length, 0
    );
    const uniqueWords = Object.keys(this.wordDictionary).length;

    return {
      totalPlates,
      totalSolutions,
      uniqueWords,
      version: 'ultra_optimized',
    };
  }

  /**
   * Get word dictionary for external access
   */
  getWordDictionary(): WordDictionary | null {
    return this.wordDictionary;
  }
}

export default GameDataService;
