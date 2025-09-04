import { useMemo } from 'react';
import { Plate } from '../types/game';

interface DistributionData {
  solutions: number[];
  scores: number[];
}

interface Percentiles {
  difficulty: number;
  score: number;
  plateAverageScore: number;
}

interface UsePercentilesParams {
  distributionData: DistributionData | null;
  plate: Plate;
  wordDictionary: Record<string, any> | null;
}

export const usePercentiles = ({ distributionData, plate, wordDictionary }: UsePercentilesParams): Percentiles => {
  return useMemo(() => {
    if (!distributionData || !wordDictionary) return { difficulty: 50, score: 50, plateAverageScore: 0 };
    
    // Find real difficulty percentile (fewer solutions = harder = higher percentile)
    const difficultyIndex = distributionData.solutions.findIndex(count => count >= plate.solution_count);
    const difficultyPercentile = difficultyIndex >= 0 
      ? Math.round((1 - difficultyIndex / distributionData.solutions.length) * 100)
      : 1;
    
    // Calculate this plate's actual average ensemble score
    const plateAverageScore = plate.solutions.reduce((sum, solution) => sum + solution.ensemble_score, 0) / plate.solutions.length;
    
    // Find real score percentile using actual average ensemble score (higher score = higher percentile)  
    const scoreIndex = distributionData.scores.findIndex(score => score >= plateAverageScore);
    const scorePercentile = scoreIndex >= 0 
      ? Math.round((scoreIndex / distributionData.scores.length) * 100)
      : 100;
    
    return {
      difficulty: Math.max(1, Math.min(99, difficultyPercentile)),
      score: Math.max(1, Math.min(99, scorePercentile)),
      plateAverageScore
    };
  }, [distributionData, plate.solution_count, plate.solutions, wordDictionary]);
};