// ScoreBreakdown component - Shows detailed scoring breakdown
import React from 'react';
import { Solution } from '../types/game';

interface ScoreBreakdownProps {
  solution: Solution;
  plateLetters: string;
  onClose: () => void;
}

export const ScoreBreakdown: React.FC<ScoreBreakdownProps> = ({
  solution,
  plateLetters,
  onClose,
}) => {
  // Use the REAL component scores from the solution
  const breakdown = {
    vocabulary: solution.vocabulary_score,
    information: solution.information_score,
    orthographic: solution.orthographic_score,
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return '#ff6b35'; // Exceptional
    if (score >= 70) return '#ff8500'; // Excellent  
    if (score >= 50) return '#ffa500'; // Good
    if (score >= 30) return '#32cd32'; // Fair
    return '#87ceeb'; // Basic
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 90) return 'Exceptional';
    if (score >= 70) return 'Excellent';
    if (score >= 50) return 'Good';
    if (score >= 30) return 'Fair';
    return 'Basic';
  };

  return (
    <div className="score-breakdown-overlay" onClick={onClose}>
      <div className="score-breakdown-modal" onClick={(e) => e.stopPropagation()}>
        <div className="breakdown-header">
          <h3>Score Breakdown</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="word-info">
          <div className="word-display">
            <span className="word-text">{solution.word}</span>
            <span className="plate-text">from "{plateLetters}"</span>
          </div>
          <div className="total-score">
            <span className="score-value">{solution.ensemble_score.toFixed(1)}</span>
            <span className="score-label">{getScoreLabel(solution.ensemble_score)}</span>
          </div>
        </div>

        <div className="breakdown-components">
          <div className="component-item">
            <div className="component-header">
              <span className="component-name">Vocabulary Sophistication</span>
              <span className="component-score">{breakdown.vocabulary}</span>
            </div>
            <div className="component-bar">
              <div 
                className="component-fill"
                style={{ 
                  width: `${breakdown.vocabulary}%`,
                  backgroundColor: getScoreColor(breakdown.vocabulary)
                }}
              />
            </div>
            <div className="component-description">
              Word rarity and sophistication in English corpus
            </div>
          </div>

          <div className="component-item">
            <div className="component-header">
              <span className="component-name">Information Content</span>
              <span className="component-score">{breakdown.information}</span>
            </div>
            <div className="component-bar">
              <div 
                className="component-fill"
                style={{ 
                  width: `${breakdown.information}%`,
                  backgroundColor: getScoreColor(breakdown.information)
                }}
              />
            </div>
            <div className="component-description">
              Surprisal value given the plate constraints
            </div>
          </div>

          <div className="component-item">
            <div className="component-header">
              <span className="component-name">Orthography Complexity</span>
              <span className="component-score">{breakdown.orthographic}</span>
            </div>
            <div className="component-bar">
              <div 
                className="component-fill"
                style={{ 
                  width: `${breakdown.orthographic}%`,
                  backgroundColor: getScoreColor(breakdown.orthographic)
                }}
              />
            </div>
            <div className="component-description">
              Letter pattern complexity and cognitive difficulty
            </div>
          </div>
        </div>

        <div className="breakdown-footer">
          <p className="ensemble-note">
            Final score combines all three dimensions using weighted ensemble averaging
          </p>
        </div>
      </div>
    </div>
  );
};

export default ScoreBreakdown;
