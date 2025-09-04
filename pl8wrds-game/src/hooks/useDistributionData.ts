import { useMemo } from 'react';
import { GameData } from '../types/game';

interface DistributionData {
  solutions: number[];
  scores: number[];
}

interface UseDistributionDataParams {
  gameData?: GameData | null | undefined;
  wordDictionary: Record<string, any> | null;
}

export const useDistributionData = ({ gameData, wordDictionary }: UseDistributionDataParams): DistributionData | null => {
  return useMemo(() => {
    if (!gameData) return null;

    try {
      const allSolutionCounts: number[] = [];
      // Calculate actual average ensemble scores for distribution analysis
      const allAverageScores: number[] = [];

      gameData.plates.forEach(plateData => {
        const solutionCount = Object.keys(plateData.solutions).length;
        allSolutionCounts.push(solutionCount);
        
        // Calculate actual average ensemble score for this plate
        let totalScore = 0;
        let scoreCount = 0;
        
        Object.entries(plateData.solutions).forEach(([wordId, infoScore]) => {
          const wordData = wordDictionary?.[wordId];
          if (wordData) {
            const vocabScore = wordData.frequency_score || 0;
            const orthoScore = wordData.orthographic_score || 0;
            const ensembleScore = (vocabScore + (infoScore as number) + orthoScore) / 3;
            totalScore += ensembleScore;
            scoreCount++;
          }
        });
        
        const averageScore = scoreCount > 0 ? totalScore / scoreCount : 0;
        allAverageScores.push(averageScore);
      });

      return {
        solutions: allSolutionCounts.sort((a, b) => a - b),
        scores: allAverageScores.sort((a, b) => a - b)
      };
    } catch (error) {
      console.error('Error building distribution data:', error);
      return null;
    }
  }, [gameData, wordDictionary]);
};