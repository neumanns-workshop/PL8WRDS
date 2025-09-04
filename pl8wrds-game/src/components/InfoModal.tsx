// InfoModal component - Shows game rules and information
import React from 'react';
import { X, MapPin } from 'lucide-react';

interface InfoModalProps {
  isOpen: boolean;
  onClose: () => void;
  gameData?: any;
}

export const InfoModal: React.FC<InfoModalProps> = ({ isOpen, onClose, gameData: _gameData }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content info-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2><MapPin size={24} />How to Play</h2>
          <button className="modal-close-button" onClick={onClose}>
            <X size={24} />
          </button>
        </div>
        
        <div className="modal-body">
          {/* Gameplay */}
          <div className="info-section">
            <h3>Gameplay</h3>
            <p>Find words that use the given letters in order.</p>
          </div>

          {/* Example */}
          <div className="info-section">
            <h3>Example</h3>
            <div className="plate-frame">
              <div className="mounting-hole top-left"></div>
              <div className="mounting-hole top-right"></div>
              <div className="mounting-hole bottom-left"></div>
              <div className="mounting-hole bottom-right"></div>
              <div className="plate-letters">QRI</div>
            </div>
            <div className="example-list">
              <div className="example-row valid">
                <span className="check">✓</span>
                <span className="word">
                  <span className="highlight">Q</span>UA<span className="highlight">R</span>ANT<span className="highlight">I</span>NE
                </span>
              </div>
              <div className="example-row valid">
                <span className="check">✓</span>
                <span className="word">
                  A<span className="highlight">Q</span>UA<span className="highlight">R</span><span className="highlight">I</span>UM
                </span>
              </div>
              <div className="example-row invalid">
                <span className="cross">✗</span>
                <span className="word">
                  IN<span className="highlight">Q</span>UI<span className="highlight">R</span>Y
                </span>
              </div>
              <div className="example-row valid">
                <span className="check">✓</span>
                <span className="word">
                  IN<span className="highlight">Q</span>UI<span className="highlight">R</span><span className="highlight">I</span>ES
                </span>
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="info-section">
            <h3>Controls</h3>
            <ul className="control-list">
              <li className="control-item">
                <div className="control-icon">⎵</div>
                <div className="control-text">
                  <strong>SPACE</strong>
                  <span>to get new plate</span>
                </div>
              </li>
              <li className="control-item">
                <div className="control-icon">↵</div>
                <div className="control-text">
                  <strong>ENTER</strong>
                  <span>to submit solution</span>
                </div>
              </li>
            </ul>
          </div>

        </div>
      </div>
    </div>
  );
};

export default InfoModal;
