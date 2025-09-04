// Main composition hook that combines all game functionality with a clean interface
import { useState, useCallback } from 'react';
import { useGameData } from './useGameData';
import { useGameState } from './useGameState';
import { useWordInput } from './useWordInput';
import { useGameActions } from './useGameActions';
import { useGameStorage } from './useGameStorage';
import { useGameAnimations } from './useGameAnimations';
import { GameState } from '../types/game';

export interface UseGameCoreReturn {
  // Legacy GameState for compatibility with existing components
  gameState: GameState;
  
  // UI State
  isLoading: boolean;
  error: string | null;
  shouldShakePlate: boolean;
  floatingScore: { points: number; show: boolean };
  isPlatePressed: boolean;
  
  // Actions
  actions: {
    startNewGame: () => void;
    startGameWithPlate: (plateId: string) => void;
    updateCurrentWord: (word: string) => void;
    submitWord: () => void;
    getHint: () => string | null;
    revealAllSolutions: () => void;
    getStarterPlates: () => any[];
    loadCollectedPlate: (plateId: string) => void;
    handleScoreAnimationComplete: () => void;
    triggerPlatePress: () => void;
  };
}

export const useGameCore = (): UseGameCoreReturn => {
  const [error, setError] = useState<string | null>(null);

  // Initialize all focused hooks
  const gameData = useGameData();
  const gameState = useGameState();
  const wordInput = useWordInput();
  const storage = useGameStorage();
  const animations = useGameAnimations();

  // Game actions hook depends on other hooks
  const gameActions = useGameActions({
    gameState,
    wordInput,
    storage,
    animations,
    gameDataService: gameData.gameDataService,
    onError: setError,
  });

  const handleScoreAnimationComplete = useCallback(() => {
    animations.hideFloatingScore();
  }, [animations]);

  // Create legacy GameState interface for compatibility
  const legacyGameState: GameState = {
    currentPlate: gameState.currentPlate,
    solutions: gameState.solutions,
    foundWords: gameState.foundWords,
    currentWord: wordInput.currentWord,
    score: gameState.score,
    gameStatus: gameState.gameStatus,
    gameData: gameData.gameData,
    wordDictionary: gameData.wordDictionary,
  };

  return {
    gameState: legacyGameState,
    isLoading: gameData.isLoading,
    error: error || gameData.error,
    shouldShakePlate: animations.shouldShakePlate,
    floatingScore: animations.floatingScore,
    isPlatePressed: animations.isPlatePressed,
    actions: {
      ...gameActions,
      updateCurrentWord: wordInput.updateCurrentWord,
      handleScoreAnimationComplete,
      triggerPlatePress: animations.triggerPlatePress,
    },
  };
};