// Hook for managing core game state (plate, solutions, score, status)
import { useState, useCallback } from 'react';
import { Plate, Solution } from '../types/game';

export interface UseGameStateReturn {
  currentPlate: Plate | null;
  solutions: Solution[];
  foundWords: string[];
  score: number;
  gameStatus: 'idle' | 'playing' | 'completed';
  setCurrentPlate: (plate: Plate | null) => void;
  setSolutions: (solutions: Solution[] | ((prev: Solution[]) => Solution[])) => void;
  setFoundWords: (words: string[] | ((prev: string[]) => string[])) => void;
  setScore: (score: number | ((prev: number) => number)) => void;
  setGameStatus: (status: 'idle' | 'playing' | 'completed') => void;
  addFoundWord: (word: string) => void;
  addScore: (points: number) => void;
  markSolutionFound: (word: string) => boolean;
  resetGameState: () => void;
}

export const useGameState = (): UseGameStateReturn => {
  const [currentPlate, setCurrentPlate] = useState<Plate | null>(null);
  const [solutions, setSolutions] = useState<Solution[]>([]);
  const [foundWords, setFoundWords] = useState<string[]>([]);
  const [score, setScore] = useState(0);
  const [gameStatus, setGameStatus] = useState<'idle' | 'playing' | 'completed'>('idle');

  const addFoundWord = useCallback((word: string) => {
    setFoundWords(prev => [...prev, word.toLowerCase()]);
  }, []);

  const addScore = useCallback((points: number) => {
    setScore(prev => prev + points);
  }, []);

  const markSolutionFound = useCallback((word: string): boolean => {
    const wordLower = word.toLowerCase();
    let solutionFound = false;

    setSolutions(prev => {
      const updated = prev.map(solution => {
        if (solution.word.toLowerCase() === wordLower && !solution.found) {
          solutionFound = true;
          return { ...solution, found: true };
        }
        return solution;
      });
      
      // Check if all solutions are found
      const allFound = updated.filter(s => s.found).length === updated.length;
      if (allFound) {
        setGameStatus('completed');
      }
      
      return updated;
    });

    return solutionFound;
  }, []);

  const resetGameState = useCallback(() => {
    setCurrentPlate(null);
    setSolutions([]);
    setFoundWords([]);
    setScore(0);
    setGameStatus('idle');
  }, []);

  return {
    currentPlate,
    solutions,
    foundWords,
    score,
    gameStatus,
    setCurrentPlate,
    setSolutions,
    setFoundWords,
    setScore,
    setGameStatus,
    addFoundWord,
    addScore,
    markSolutionFound,
    resetGameState,
  };
};