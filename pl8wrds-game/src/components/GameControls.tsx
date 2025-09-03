// GameControls component - Game control buttons and actions
import React from 'react';
import { RotateCcw } from 'lucide-react';

interface GameControlsProps {
  gameStatus: 'idle' | 'playing' | 'completed';
  onNewGame: () => void;
  className?: string;
}

export const GameControls: React.FC<GameControlsProps> = ({
  gameStatus,
  onNewGame,
  className = "",
}) => {
  return (
    <div className={`game-controls ${className}`}>
      <button 
        onClick={onNewGame}
        className="control-button new-game-button"
        title="New Game (Spacebar)"
      >
        <RotateCcw size={24} />
      </button>
    </div>
  );
};

export default GameControls;
