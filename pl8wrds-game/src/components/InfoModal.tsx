// InfoModal component - Shows game rules and information
import React from 'react';
import { X, MapPin, Target, Award, Keyboard, Book } from 'lucide-react';

interface InfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  gameData?: any;
}

export const InfoModal: React.FC<InfoModalProps> = ({ isOpen, onClose, gameData }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content info-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2><MapPin size={24} />How to Play PL8WRDS</h2>
          <button className="modal-close-button" onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        
        <div className="modal-body">
          <div className="info-section">
            <div className="info-item">
              <Target className="info-icon" size={20} />
              <div>
                <h3>The Goal</h3>
                <p>Find words that contain the license plate letters <strong>in the exact order shown</strong>.</p>
                <p className="example">Example: For plate "CAR", words like "sCARe", "CARbon", or "suCCubuS" work!</p>
              </div>
            </div>
            
            <div className="info-item">
              <Award className="info-icon" size={20} />
              <div>
                <h3>Scoring</h3>
                <p>Earn points based on word rarity and difficulty. Longer, less common words score higher!</p>
              </div>
            </div>
            
            <div className="info-item">
              <Keyboard className="info-icon" size={20} />
              <div>
                <h3>Controls</h3>
                <ul>
                  <li><kbd>Enter</kbd> - Submit word</li>
                  <li><kbd>Space</kbd> - New route (new license plate)</li>
                  <li>Click plate - View registration details</li>
                </ul>
              </div>
            </div>
          </div>

          {gameData && (
            <div className="info-section">
              <div className="info-item">
                <Book className="info-icon" size={20} />
                <div>
                  <h3>Game Stats</h3>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="detail-label">Total Plates:</span>
                      <span className="detail-value">{gameData.metadata.total_plates.toLocaleString()}</span>
                    </div>
                    <div className="stat-item">
                      <span className="detail-label">Unique Words:</span>
                      <span className="detail-value">{gameData.metadata.unique_words.toLocaleString()}</span>
                    </div>
                    <div className="stat-item">
                      <span className="detail-label">Total Solutions:</span>
                      <span className="detail-value">{gameData.metadata.total_solutions.toLocaleString()}</span>
                    </div>
                  </div>
                  <p className="data-source">
                    Word list from WordNet with frequencies from Google N-grams
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <div className="info-footer">
            <p className="vintage-note">
              <em>Like the old Rand McNally atlases, each plate tells a story of the open road...</em>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfoModal;
