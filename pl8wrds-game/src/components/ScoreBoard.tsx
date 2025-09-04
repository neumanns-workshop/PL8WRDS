// ScoreBoard component - Shows current score only
import React from 'react';
import { Solution } from '../types/game';

interface ScoreBoardProps {
  solutions: Solution[];
  totalScore: number;
  plateLetters: string;
  className?: string;
}

export const ScoreBoard: React.FC<ScoreBoardProps> = ({
  solutions,
  totalScore,
  plateLetters: _plateLetters,
  className = "",
}) => {
  const foundSolutions = solutions.filter(s => s.found);

  return (
    <div className={`score-board ${className}`}>
      <div className="score-header">
        <h3>Current Score</h3>
        <div className="total-score">
          <span className="score-value">{totalScore.toFixed(1)}</span>
        </div>
      </div>

      {foundSolutions.length === 0 ? (
        <div className="no-words">
          <p>Start typing to find words!</p>
          <p className="hint">Click the plate for detailed progress.</p>
        </div>
      ) : (
        <div className="simple-stats">
          <p>{foundSolutions.length} words found</p>
          <p>Click plate for details</p>
        </div>
      )}
    </div>
  );
};

export default ScoreBoard;
