import React from 'react';
import { X } from 'lucide-react';

interface ScoreBreakdownData {
  word: string;
  ensemble_score: number;
  vocabulary_score: number;
  information_score: number;
  orthographic_score: number;
  details: {
    wordFrequency: number;
    wordLength: number;
    plateId: string;
    solutionCount: number;
  };
}

interface SelectedWord {
  word: string;
  score: number;
  breakdown: ScoreBreakdownData;
}

interface ScoreBreakdownModalProps {
  selectedWord: SelectedWord | null;
  onClose: () => void;
}

export const ScoreBreakdownModal: React.FC<ScoreBreakdownModalProps> = ({
  selectedWord,
  onClose,
}) => {
  if (!selectedWord) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content score-breakdown-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Score Breakdown: {selectedWord.breakdown.word.toUpperCase()}</h2>
          <button className="modal-close-button" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          <div className="final-score">
            <span className="score-label">Ensemble Score:</span>
            <span className="score-value">{selectedWord.breakdown.ensemble_score}</span>
          </div>

          <div className="component-scores-breakdown">
            <h4>Component Scores</h4>
            
            <div className="score-component">
              <div className="component-header">
                <span className="component-name">Vocabulary Sophistication</span>
                <span className="component-score">{selectedWord.breakdown.vocabulary_score}/100</span>
              </div>
              <div className="score-bar">
                <div className="score-fill" style={{width: `${selectedWord.breakdown.vocabulary_score}%`}}></div>
              </div>
              <p className="component-description">Based on word rarity in corpus</p>
            </div>

            <div className="score-component">
              <div className="component-header">
                <span className="component-name">Information Content</span>
                <span className="component-score">{selectedWord.breakdown.information_score}/100</span>
              </div>
              <div className="score-bar">
                <div className="score-fill" style={{width: `${selectedWord.breakdown.information_score}%`}}></div>
              </div>
              <p className="component-description">Surprisal given plate constraints</p>
            </div>

            <div className="score-component">
              <div className="component-header">
                <span className="component-name">Orthography Complexity</span>
                <span className="component-score">{selectedWord.breakdown.orthographic_score}/100</span>
              </div>
              <div className="score-bar">
                <div className="score-fill" style={{width: `${selectedWord.breakdown.orthographic_score}%`}}></div>
              </div>
              <p className="component-description">Letter pattern rarity</p>
            </div>
          </div>

          <div className="score-details">
            <h4>Word Details</h4>
            
            <div className="detail-item">
              <span className="detail-name">Corpus Frequency:</span>
              <span className="detail-value">{selectedWord.breakdown.details.wordFrequency.toLocaleString()}</span>
            </div>

            <div className="detail-item">
              <span className="detail-name">Word Length:</span>
              <span className="detail-value">{selectedWord.breakdown.details.wordLength} letters</span>
            </div>

            <div className="detail-item">
              <span className="detail-name">Total Solutions:</span>
              <span className="detail-value">{selectedWord.breakdown.details.solutionCount}</span>
            </div>

            <div className="detail-item">
              <span className="detail-name">Plate:</span>
              <span className="detail-value">{selectedWord.breakdown.details.plateId}</span>
            </div>
          </div>

          <div className="ensemble-note">
            <p><strong>Real Ensemble Scoring</strong></p>
            <p>These scores come from your trained machine learning models and represent genuine difficulty assessment across three dimensions.</p>
            <p>Word data from WordNet dictionary with Google N-grams frequency.</p>
          </div>
        </div>
      </div>
    </div>
  );
};