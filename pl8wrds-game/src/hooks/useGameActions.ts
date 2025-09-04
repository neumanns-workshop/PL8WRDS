// Hook for managing game actions (start, submit, hint, reveal)
import { useCallback } from 'react';
import GameDataService from '../services/gameData';
import { Plate } from '../types/game';
import { UseGameStateReturn } from './useGameState';
import { UseWordInputReturn } from './useWordInput';
import { UseGameStorageReturn } from './useGameStorage';
import { UseGameAnimationsReturn } from './useGameAnimations';

export interface UseGameActionsProps {
  gameState: UseGameStateReturn;
  wordInput: UseWordInputReturn;
  storage: UseGameStorageReturn;
  animations: UseGameAnimationsReturn;
  gameDataService: GameDataService;
  onError: (error: string | null) => void;
}

export interface UseGameActionsReturn {
  startNewGame: () => void;
  startGameWithPlate: (plateId: string) => void;
  submitWord: () => void;
  getHint: () => string | null;
  revealAllSolutions: () => void;
  getStarterPlates: () => Plate[];
  loadCollectedPlate: (plateId: string) => void;
}

export const useGameActions = ({
  gameState,
  wordInput,
  storage,
  animations,
  gameDataService,
  onError,
}: UseGameActionsProps): UseGameActionsReturn => {

  const initializeGameWithPlate = useCallback((plate: Plate, existingProgress?: any) => {
    const foundWords = existingProgress?.foundWords || [];
    const solutions = plate.solutions.map(s => ({
      ...s,
      found: foundWords.includes(s.word.toLowerCase())
    }));

    gameState.setCurrentPlate(plate);
    gameState.setSolutions(solutions);
    gameState.setFoundWords(foundWords);
    gameState.setScore(existingProgress?.totalScore || 0);
    gameState.setGameStatus('playing');
  }, [gameState]);

  const startNewGame = useCallback(() => {
    const plate = gameDataService.getRandomPlate();
    if (!plate) {
      onError('No plates available');
      return;
    }

    initializeGameWithPlate(plate);
    onError(null);
  }, [gameDataService, initializeGameWithPlate, onError]);

  const startGameWithPlate = useCallback((plateId: string) => {
    const plate = gameDataService.getPlateById(plateId);
    if (!plate) {
      onError(`Plate ${plateId} not found`);
      return;
    }

    initializeGameWithPlate(plate);
    onError(null);
  }, [gameDataService, initializeGameWithPlate, onError]);

  const submitWord = useCallback(() => {
    if (!gameState.currentPlate || wordInput.isWordEmpty) return;

    const word = wordInput.currentWord.trim().toLowerCase();

    // Check if word was already found
    if (gameState.foundWords.includes(word)) {
      onError(`"${word}" already found!`);
      setTimeout(() => onError(null), 2000);
      return;
    }

    // Check if word is a valid solution
    const solution = gameDataService.checkWordSolution(word, gameState.currentPlate);
    
    if (solution) {
      // Valid word found
      const solutionMarked = gameState.markSolutionFound(word);
      if (solutionMarked) {
        gameState.addFoundWord(word);
        gameState.addScore(solution.ensemble_score);
        
        // Trigger floating score animation
        animations.showFloatingScore(solution.ensemble_score);
        
        // Save progress to localStorage
        storage.saveGameProgress(
          gameState.currentPlate.id,
          gameState.currentPlate.letters,
          gameState.currentPlate.difficulty,
          gameState.currentPlate.solution_count,
          [...gameState.foundWords, word],
          gameState.score + solution.ensemble_score
        );
      }

      wordInput.clearCurrentWord();
      onError(null);
    } else {
      // Invalid word: clear input and shake plate
      wordInput.clearCurrentWord();
      animations.triggerPlateShake();
    }
  }, [gameState, wordInput, gameDataService, storage, animations, onError]);

  const getHint = useCallback((): string | null => {
    if (!gameState.currentPlate) return null;

    const unFoundSolutions = gameState.solutions.filter(s => !s.found);
    if (unFoundSolutions.length === 0) return null;

    // Get a random unfound solution
    const randomSolution = unFoundSolutions[Math.floor(Math.random() * unFoundSolutions.length)];
    return randomSolution.word;
  }, [gameState.solutions, gameState.currentPlate]);

  const revealAllSolutions = useCallback(() => {
    gameState.setSolutions(prev => prev.map(s => ({ ...s, found: true })));
    gameState.setFoundWords(gameState.solutions.map(s => s.word.toLowerCase()));
    gameState.setGameStatus('completed');
  }, [gameState]);

  const getStarterPlates = useCallback((): Plate[] => {
    return gameDataService.getStarterPlates(5);
  }, [gameDataService]);

  const loadCollectedPlate = useCallback((plateId: string) => {
    if (!gameState.gameStatus) return;
    
    const plate = gameDataService.getPlateById(plateId);
    if (!plate) return;

    // Load any existing progress from localStorage
    const existingProgress = storage.getPlateProgress(plateId);
    initializeGameWithPlate(plate, existingProgress);
  }, [gameDataService, gameState.gameStatus, storage, initializeGameWithPlate]);

  return {
    startNewGame,
    startGameWithPlate,
    submitWord,
    getHint,
    revealAllSolutions,
    getStarterPlates,
    loadCollectedPlate,
  };
};