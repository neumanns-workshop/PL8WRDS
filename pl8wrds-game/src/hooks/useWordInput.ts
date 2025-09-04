// Hook for managing word input handling and submission
import { useState, useCallback } from 'react';

export interface UseWordInputReturn {
  currentWord: string;
  updateCurrentWord: (word: string) => void;
  clearCurrentWord: () => void;
  isWordEmpty: boolean;
}

export const useWordInput = (): UseWordInputReturn => {
  const [currentWord, setCurrentWord] = useState('');

  const updateCurrentWord = useCallback((word: string) => {
    setCurrentWord(word);
  }, []);

  const clearCurrentWord = useCallback(() => {
    setCurrentWord('');
  }, []);

  const isWordEmpty = currentWord.trim() === '';

  return {
    currentWord,
    updateCurrentWord,
    clearCurrentWord,
    isWordEmpty,
  };
};