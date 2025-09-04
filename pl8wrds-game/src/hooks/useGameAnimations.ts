// Hook for managing UI animations and visual effects
import { useState, useCallback } from 'react';

export interface FloatingScore {
  points: number;
  show: boolean;
}

export interface UseGameAnimationsReturn {
  shouldShakePlate: boolean;
  floatingScore: FloatingScore;
  isPlatePressed: boolean;
  triggerPlateShake: () => void;
  showFloatingScore: (points: number) => void;
  hideFloatingScore: () => void;
  triggerPlatePress: () => void;
}

export const useGameAnimations = (): UseGameAnimationsReturn => {
  const [shouldShakePlate, setShouldShakePlate] = useState(false);
  const [floatingScore, setFloatingScore] = useState<FloatingScore>({ points: 0, show: false });
  const [isPlatePressed, setIsPlatePressed] = useState(false);

  const triggerPlateShake = useCallback(() => {
    setShouldShakePlate(true);
    setTimeout(() => setShouldShakePlate(false), 500); // Reset after animation
  }, []);

  const showFloatingScore = useCallback((points: number) => {
    setFloatingScore({ points, show: true });
  }, []);

  const hideFloatingScore = useCallback(() => {
    setFloatingScore({ points: 0, show: false });
  }, []);

  const triggerPlatePress = useCallback(() => {
    setIsPlatePressed(true);
    setTimeout(() => setIsPlatePressed(false), 150); // Match the CSS transition duration
  }, []);

  return {
    shouldShakePlate,
    floatingScore,
    isPlatePressed,
    triggerPlateShake,
    showFloatingScore,
    hideFloatingScore,
    triggerPlatePress,
  };
};