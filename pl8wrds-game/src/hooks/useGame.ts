// Custom hook for managing game state
import { useState, useCallback, useEffect } from 'react';
import { GameState } from '../types/game';
import GameDataService from '../services/gameData';
import StorageService from '../services/storage';

export const useGame = () => {
  const [gameState, setGameState] = useState<GameState>({
    currentPlate: null,
    solutions: [],
    foundWords: [],
    currentWord: '',
    score: 0,
    gameStatus: 'idle',
    gameData: null,
    wordDictionary: null,
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [shouldShakePlate, setShouldShakePlate] = useState(false);
  const [floatingScore, setFloatingScore] = useState<{ points: number; show: boolean }>({ points: 0, show: false });
  const [isPlatePressed, setIsPlatePressed] = useState(false);

  const gameDataService = GameDataService.getInstance();

  // Initialize game data
  useEffect(() => {
    const initGame = async () => {
      try {
        setIsLoading(true);
        const gameData = await gameDataService.loadGameData();
        const wordDictionary = gameDataService.getWordDictionary();
        setGameState(prev => ({
          ...prev,
          gameData,
          wordDictionary,
          gameStatus: 'idle',
        }));
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load game');
      } finally {
        setIsLoading(false);
      }
    };

    initGame();
  }, [gameDataService]);

  // Start a new game with a random plate
  const startNewGame = useCallback(() => {
    const plate = gameDataService.getRandomPlate();
    if (!plate) {
      setError('No plates available');
      return;
    }

    setGameState(prev => ({
      ...prev,
      currentPlate: plate,
      solutions: plate.solutions.map(s => ({ ...s, found: false })),
      foundWords: [],
      score: 0,
      gameStatus: 'playing',
    }));
  }, [gameDataService]);

  // Start game with a specific plate
  const startGameWithPlate = useCallback((plateId: string) => {
    const plate = gameDataService.getPlateById(plateId);
    if (!plate) {
      setError(`Plate ${plateId} not found`);
      return;
    }

    setGameState(prev => ({
      ...prev,
      currentPlate: plate,
      solutions: plate.solutions.map(s => ({ ...s, found: false })),
      foundWords: [],
      score: 0,
      gameStatus: 'playing',
    }));
  }, [gameDataService]);

  // Update current word input
  const updateCurrentWord = useCallback((word: string) => {
    setGameState(prev => ({
      ...prev,
      currentWord: word,
    }));
  }, []);

  // Submit a word
  const submitWord = useCallback(() => {
    if (!gameState.currentPlate || !gameState.currentWord.trim()) return;

    const word = gameState.currentWord.trim().toLowerCase();

    // Check if word was already found
    if (gameState.foundWords.includes(word)) {
      setError(`"${word}" already found!`);
      setTimeout(() => setError(null), 2000);
      return;
    }

    // Check if word is a valid solution
    const solution = gameDataService.checkWordSolution(word, gameState.currentPlate);
    
    if (solution) {
      const updatedSolutions = gameState.solutions.map(s => 
        s.word.toLowerCase() === word ? { ...s, found: true } : s
      );
      
      const newFoundWords = [...gameState.foundWords, word];
      const newScore = gameState.score + solution.ensemble_score;
      
      // Trigger floating score animation
      setFloatingScore({ points: solution.ensemble_score, show: true });
      
      const isCompleted = updatedSolutions.filter(s => s.found).length === updatedSolutions.length;
      
      setGameState(prev => ({
        ...prev,
        solutions: updatedSolutions,
        foundWords: newFoundWords,
        score: newScore,
        currentWord: '',
        gameStatus: isCompleted ? 'completed' : 'playing',
      }));

      // Save progress to localStorage
      if (gameState.currentPlate) {
        StorageService.updateCollectedPlate(
          gameState.currentPlate.id,
          gameState.currentPlate.letters,
          gameState.currentPlate.difficulty,
          gameState.currentPlate.solution_count,
          newFoundWords,
          newScore
        );
      }

      setError(null);
    } else {
      // Invalid word: clear input and shake plate
      setGameState(prev => ({
        ...prev,
        currentWord: '',
      }));
      
      // Trigger plate shake animation
      setShouldShakePlate(true);
      setTimeout(() => setShouldShakePlate(false), 500); // Reset after animation
    }
  }, [gameState, gameDataService]);

  // Get a hint (reveal a random unfound word)
  const getHint = useCallback(() => {
    if (!gameState.currentPlate) return null;

    const unFoundSolutions = gameState.solutions.filter(s => !s.found);
    if (unFoundSolutions.length === 0) return null;

    // Get a random unfound solution
    const randomSolution = unFoundSolutions[Math.floor(Math.random() * unFoundSolutions.length)];
    return randomSolution.word;
  }, [gameState.solutions, gameState.currentPlate]);

  // Reveal all solutions
  const revealAllSolutions = useCallback(() => {
    setGameState(prev => ({
      ...prev,
      solutions: prev.solutions.map(s => ({ ...s, found: true })),
      foundWords: prev.solutions.map(s => s.word.toLowerCase()),
      gameStatus: 'completed',
    }));
  }, []);

  // Get starter plates
  const getStarterPlates = useCallback(() => {
    return gameDataService.getStarterPlates(5);
  }, [gameDataService]);

  // Handle floating score animation completion
  const handleScoreAnimationComplete = useCallback(() => {
    setFloatingScore({ points: 0, show: false });
  }, []);

  // Trigger plate press visual effect (for Space key)
  const triggerPlatePress = useCallback(() => {
    setIsPlatePressed(true);
    setTimeout(() => setIsPlatePressed(false), 150); // Match the CSS transition duration
  }, []);

  // Load a specific plate from collection
  const loadCollectedPlate = useCallback((plateId: string) => {
    if (!gameState.gameData) return;
    
    const plate = gameDataService.getPlateById(plateId);
    if (!plate) return;

    // Load any existing progress from localStorage
    const collectedPlates = StorageService.getCollectedPlates();
    const existingProgress = collectedPlates.find(p => p.plateId === plateId);
    
    const foundWords = existingProgress?.foundWords || [];
    const solutions = plate.solutions.map(s => ({
      ...s,
      found: foundWords.includes(s.word.toLowerCase())
    }));

    setGameState(prev => ({
      ...prev,
      currentPlate: plate,
      solutions,
      foundWords,
      score: existingProgress?.totalScore || 0,
      gameStatus: 'playing',
    }));
  }, [gameDataService, gameState.gameData]);

  return {
    gameState,
    isLoading,
    error,
    shouldShakePlate,
    floatingScore,
    isPlatePressed,
    actions: {
      startNewGame,
      startGameWithPlate,
      updateCurrentWord,
      submitWord,
      getHint,
      revealAllSolutions,
      getStarterPlates,
      loadCollectedPlate,
      handleScoreAnimationComplete,
      triggerPlatePress,
    },
  };
};

export default useGame;
