import { useCallback } from 'react';
import { Plate } from '../types/game';

interface ScoreBreakdownData {
  word: string;
  ensemble_score: number;
  vocabulary_score: number;
  information_score: number;
  orthographic_score: number;
  details: {
    wordFrequency: number;
    wordLength: number;
    plateId: string;
    solutionCount: number;
  };
}

interface UseScoreBreakdownParams {
  plate: Plate;
  wordDictionary: Record<string, any> | null;
}

export const useScoreBreakdown = ({ plate, wordDictionary }: UseScoreBreakdownParams) => {
  const getScoreBreakdown = useCallback((word: string): ScoreBreakdownData | null => {
    if (!wordDictionary) return null;
    
    // Find the solution directly by word
    const solution = plate.solutions.find(sol => sol.word === word);
    if (!solution) return null;
    
    // Find the word data in the dictionary
    const wordData = wordDictionary[solution.wordId.toString()];
    
    return {
      word,
      ensemble_score: solution.ensemble_score,
      vocabulary_score: solution.vocabulary_score,
      information_score: solution.information_score,
      orthographic_score: solution.orthographic_score,
      details: {
        wordFrequency: wordData?.frequency_score || 0,
        wordLength: word.length,
        plateId: plate.letters,
        solutionCount: plate.solution_count
      }
    };
  }, [plate, wordDictionary]);

  return { getScoreBreakdown };
};