// PlateDisplay component - Shows the current license plate
import React, { useState, useMemo } from 'react';
import { Plate, getDifficultyColor, GameData } from '../types/game';
import RouteGuide from './PlateRegistration';

interface PlateDisplayProps {
  plate: Plate | null;
  foundWordsCount: number;
  totalSolutions: number;
  foundWords: string[];
  currentScore: number;
  gameData?: GameData | null;
}

export const PlateDisplay: React.FC<PlateDisplayProps> = ({
  plate,
  foundWordsCount,
  totalSolutions,
  foundWords,
  currentScore,
  gameData,
}) => {
  const [showRegistration, setShowRegistration] = useState(false);

  // Calculate real difficulty percentile from actual data - MUST be before conditional return
  const difficultyPercentile = useMemo(() => {
    if (!gameData || !plate) return 50;
    
    const allSolutionCounts: number[] = [];
    gameData.plates.forEach(plateData => {
      allSolutionCounts.push(Object.keys(plateData.solutions).length);
    });
    allSolutionCounts.sort((a, b) => a - b);
    
    // Find real difficulty percentile (fewer solutions = harder = higher percentile)
    const difficultyIndex = allSolutionCounts.findIndex(count => count >= plate.solution_count);
    return difficultyIndex >= 0 
      ? Math.max(1, Math.min(99, Math.round((1 - difficultyIndex / allSolutionCounts.length) * 100)))
      : 1;
  }, [gameData, plate]);

  if (!plate) {
    return (
      <div className="plate-display loading">
        <div className="plate-frame">
          <div className="plate-score">0.0</div>
          <div className="plate-letters">???</div>
        </div>
        <div className="plate-info">Loading...</div>
      </div>
    );
  }

  return (
    <div className="plate-display">
      <div 
        className="plate-frame clickable-plate"
        style={{ borderColor: getDifficultyColor(difficultyPercentile) }}
        onClick={() => setShowRegistration(true)}
        title="Click for plate details"
      >
        <div className="plate-score">{currentScore.toFixed(1)}</div>
        
        <div className="plate-letters">{plate.letters}</div>
        
        <div className="plate-id">#{plate.id}</div>
        
        <div className="plate-click-hint">Click for details</div>
      </div>

      {showRegistration && plate && (
        <RouteGuide 
          plate={plate}
          foundWords={foundWords}
          onClose={() => setShowRegistration(false)}
          gameData={gameData}
        />
      )}
    </div>
  );
};

export default PlateDisplay;
