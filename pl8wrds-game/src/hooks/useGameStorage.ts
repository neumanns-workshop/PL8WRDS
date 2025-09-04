// Hook for managing localStorage integration for game progress
import { useCallback } from 'react';
import { 
  ProgressStorageService, 
  CollectionAnalyticsService, 
  CollectedPlate 
} from '../services/storage';

export interface UseGameStorageReturn {
  saveGameProgress: (
    plateId: string,
    letters: string,
    difficulty: number,
    solutionCount: number,
    foundWords: string[],
    totalScore: number
  ) => void;
  getPlateProgress: (plateId: string) => CollectedPlate | null;
  getCollectedPlates: () => CollectedPlate[];
  clearAllProgress: () => void;
}

export const useGameStorage = (): UseGameStorageReturn => {
  const saveGameProgress = useCallback((
    plateId: string,
    letters: string,
    difficulty: number,
    solutionCount: number,
    foundWords: string[],
    totalScore: number
  ) => {
    ProgressStorageService.updateCollectedPlate(
      plateId,
      letters,
      difficulty,
      solutionCount,
      foundWords,
      totalScore
    );
  }, []);

  const getPlateProgress = useCallback((plateId: string) => {
    return ProgressStorageService.getCollectedPlate(plateId);
  }, []);

  const getCollectedPlates = useCallback(() => {
    return CollectionAnalyticsService.getCollectedPlates();
  }, []);

  const clearAllProgress = useCallback(() => {
    ProgressStorageService.clearProgress();
  }, []);

  return {
    saveGameProgress,
    getPlateProgress,
    getCollectedPlates,
    clearAllProgress,
  };
};