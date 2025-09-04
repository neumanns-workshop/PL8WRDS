// Solution processing service for PL8WRDS
import { Solution, WordDictionary } from '../types/game';

/**
 * Service responsible for processing raw solution data into Solution objects
 * Handles scoring calculations and data transformation
 */
export class SolutionProcessorService {
  private static instance: SolutionProcessorService;

  static getInstance(): SolutionProcessorService {
    if (!SolutionProcessorService.instance) {
      SolutionProcessorService.instance = new SolutionProcessorService();
    }
    return SolutionProcessorService.instance;
  }

  /**
   * Process raw solution data into Solution objects with scoring
   */
  processSolutions(solutionsData: { [wordId: string]: number }, wordDictionary: WordDictionary, plateId: string): Solution[] {
    if (!wordDictionary) {
      throw new Error('Word dictionary not loaded');
    }

    return Object.entries(solutionsData).map(([wordId, infoScore]) => {
      const wordData = wordDictionary[wordId];
      
      // Ensure we have valid word data
      if (!wordData || typeof wordData !== 'object' || !wordData.word) {
        throw new Error(`Missing or invalid word data for word ID ${wordId} in plate ${plateId}`);
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
  }
}

export default SolutionProcessorService;