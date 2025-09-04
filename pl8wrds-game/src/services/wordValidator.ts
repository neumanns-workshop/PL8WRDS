// Word validation service for PL8WRDS
import { Plate, Solution } from '../types/game';

/**
 * Service responsible for word validation and solution checking
 * Handles validation logic and word-plate matching
 */
export class WordValidatorService {
  private static instance: WordValidatorService;

  static getInstance(): WordValidatorService {
    if (!WordValidatorService.instance) {
      WordValidatorService.instance = new WordValidatorService();
    }
    return WordValidatorService.instance;
  }

  /**
   * Validate if a word contains plate letters in correct order
   */
  validateWord(word: string, plate: string): boolean {
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
    if (!this.validateWord(word, plate.letters)) {
      return null;
    }

    const solution = plate.solutions.find(s => s.word.toLowerCase() === word.toLowerCase());
    return solution || null;
  }
}

export default WordValidatorService;