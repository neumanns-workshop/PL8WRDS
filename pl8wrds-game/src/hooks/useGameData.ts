// Hook for managing game data loading and initialization
import { useState, useEffect, useCallback } from 'react';
import { GameData, WordDictionary } from '../types/game';
import GameDataService from '../services/gameData';

export interface UseGameDataReturn {
  gameData: GameData | null;
  wordDictionary: WordDictionary | null;
  isLoading: boolean;
  error: string | null;
  gameDataService: GameDataService;
  refetch: () => Promise<void>;
}

export const useGameData = (): UseGameDataReturn => {
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [wordDictionary, setWordDictionary] = useState<WordDictionary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const gameDataService = GameDataService.getInstance();

  const loadGameData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await gameDataService.loadGameData();
      const dictionary = gameDataService.getWordDictionary();
      setGameData(data);
      setWordDictionary(dictionary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load game data');
    } finally {
      setIsLoading(false);
    }
  }, [gameDataService]);

  // Initialize on mount
  useEffect(() => {
    loadGameData();
  }, [loadGameData]);

  return {
    gameData,
    wordDictionary,
    isLoading,
    error,
    gameDataService,
    refetch: loadGameData,
  };
};