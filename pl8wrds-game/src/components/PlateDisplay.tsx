// PlateDisplay component - Shows the current license plate
import React, { useMemo } from 'react';
import { Plate, getPlateColor } from '../types/game';

interface PlateDisplayProps {
  plate: Plate | null;
  foundWordsCount: number;
  totalSolutions: number;
  foundWords: string[];
  currentScore: number;
  onNewPlate: () => void;  // Callback to get a new plate
  shouldShake?: boolean;  // Whether to shake the plate for invalid words
  isPressed?: boolean;    // Whether to show pressed state (for Space key)
}

// Generate randomized voronoi texture based on plate ID for consistent unique patterns
const generateVoronoiTexture = (plateId: string): string => {
  // Use plate ID to seed consistent random values
  const seedValue = plateId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
  
  const seededRandom = (seed: number) => {
    const x = Math.sin(seed) * 10000;
    return x - Math.floor(x);
  };
  
  // Generate 8-12 random voronoi cells
  const cellCount = 8 + Math.floor(seededRandom(seedValue) * 5);
  const gradients = [];
  
  for (let i = 0; i < cellCount; i++) {
    const x = Math.floor(seededRandom(seedValue + i * 7) * 100);
    const y = Math.floor(seededRandom(seedValue + i * 13) * 100);
    const size = 12 + Math.floor(seededRandom(seedValue + i * 19) * 8); // 12-20% size
    const intensity = seededRandom(seedValue + i * 23) > 0.5 ? 'white' : 'black';
    const opacity = 5 + Math.floor(seededRandom(seedValue + i * 29) * 10); // 5-15% opacity
    
    gradients.push(`radial-gradient(circle at ${x}% ${y}%, color-mix(in srgb, var(--plate-surface-color, var(--color-plate-surface)) ${100 - opacity}%, ${intensity} ${opacity}%) 0%, transparent ${size}%)`);
  }
  
  return gradients.join(', ');
};

export const PlateDisplay: React.FC<PlateDisplayProps> = ({
  plate,
  foundWordsCount,
  totalSolutions,
  foundWords,
  currentScore,
  onNewPlate,
  shouldShake = false,
  isPressed = false,
}) => {
  // Generate unique voronoi pattern for this plate
  const voronoiTexture = useMemo(() => {
    if (!plate) return '';
    return generateVoronoiTexture(plate.id);
  }, [plate?.id]);

  if (!plate) {
    return (
      <div className="plate-display loading">
        <div className="plate-frame">
          {/* Subtle mounting hole divots */}
          <div className="mounting-hole top-left"></div>
          <div className="mounting-hole top-right"></div>
          <div className="mounting-hole bottom-left"></div>
          <div className="mounting-hole bottom-right"></div>
          
          <div className="plate-score">0</div>
          <div className="plate-letters">???</div>
          <div className="plate-id">---</div>
        </div>
        <div className="plate-info">Loading...</div>
      </div>
    );
  }

  return (
    <div className="plate-display">
      <div 
        className={`plate-frame clickable-plate ${shouldShake ? 'shake-plate' : ''} ${isPressed ? 'pressed' : ''}`}
        style={{ 
          borderColor: getPlateColor(plate),
          '--plate-surface-color': getPlateColor(plate),
          '--voronoi-texture': voronoiTexture
        } as React.CSSProperties & { '--plate-surface-color': string; '--voronoi-texture': string }}
        onClick={onNewPlate}
        title="Click for new route"
      >
        {/* Subtle mounting hole divots */}
        <div className="mounting-hole top-left"></div>
        <div className="mounting-hole top-right"></div>
        <div className="mounting-hole bottom-left"></div>
        <div className="mounting-hole bottom-right"></div>
        
        <div className="plate-score">{Math.round(currentScore * 10)}</div>
        <div className="plate-letters">{plate.letters}</div>
        <div className="plate-id">{plate.id}</div>
      </div>
    </div>
  );
};

export default PlateDisplay;
