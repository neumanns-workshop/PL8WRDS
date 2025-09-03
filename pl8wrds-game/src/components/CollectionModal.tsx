import React, { useState, useMemo } from 'react';
import { X, Trophy, Calendar, Target, Filter } from 'lucide-react';
import StorageService from '../services/storage';

interface CollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPlate?: (plateId: string) => void;
}

const CollectionModal: React.FC<CollectionModalProps> = ({
  isOpen,
  onClose,
  onSelectPlate
}) => {
  const [sortBy, setSortBy] = useState<'recent' | 'completion' | 'difficulty' | 'letters'>('recent');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');

  const collectedPlates = useMemo(() => {
    let plates = StorageService.getCollectedPlates(sortBy);
    
    if (selectedDifficulty !== 'all') {
      plates = plates.filter(plate => getDifficultyTier(plate.difficulty) === selectedDifficulty);
    }
    
    return plates;
  }, [sortBy, selectedDifficulty]);

  const stats = useMemo(() => StorageService.getCollectionStats(), []);

  if (!isOpen) return null;

  const getDifficultyTier = (difficulty: number): string => {
    if (difficulty >= 90) return 'Ultra Hard';
    if (difficulty >= 80) return 'Very Hard';
    if (difficulty >= 60) return 'Hard';
    if (difficulty >= 30) return 'Medium';
    return 'Easy';
  };

  const getDifficultyColor = (difficulty: number): string => {
    if (difficulty >= 90) return '#dc3545'; // Red - Ultra Hard
    if (difficulty >= 80) return '#fd7e14'; // Orange - Very Hard
    if (difficulty >= 60) return '#ffc107'; // Yellow - Hard
    if (difficulty >= 30) return '#28a745'; // Green - Medium
    return '#17a2b8'; // Cyan - Easy
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
    });
  };

  const handlePlateClick = (plateId: string) => {
    if (onSelectPlate) {
      onSelectPlate(plateId);
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content collection-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2><Trophy className="inline-icon" size={24} />Plate Collection</h2>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Collection Stats */}
          <div className="collection-stats">
            <div className="stat-card">
              <div className="stat-number">{stats.totalPlates}</div>
              <div className="stat-label">Plates Found</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{stats.totalWords}</div>
              <div className="stat-label">Words Found</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{stats.totalScore.toLocaleString()}</div>
              <div className="stat-label">Total Score</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{stats.averageCompletion}%</div>
              <div className="stat-label">Avg Completion</div>
            </div>
          </div>

          {/* Filters and Sorting */}
          <div className="collection-controls">
            <div className="sort-controls">
              <Filter size={16} />
              <span>Sort:</span>
              <select 
                value={sortBy} 
                onChange={(e) => setSortBy(e.target.value as any)}
                className="collection-select"
              >
                <option value="recent">Recently Played</option>
                <option value="completion">Completion %</option>
                <option value="difficulty">Difficulty</option>
                <option value="letters">Alphabetical</option>
              </select>
            </div>

            <div className="filter-controls">
              <span>Difficulty:</span>
              <select 
                value={selectedDifficulty} 
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="collection-select"
              >
                <option value="all">All Difficulties</option>
                <option value="Ultra Hard">Ultra Hard</option>
                <option value="Very Hard">Very Hard</option>
                <option value="Hard">Hard</option>
                <option value="Medium">Medium</option>
                <option value="Easy">Easy</option>
              </select>
            </div>
          </div>

          {/* Collected Plates Grid */}
          {collectedPlates.length === 0 ? (
            <div className="empty-collection">
              <div className="empty-message">
                <Trophy size={48} />
                <h3>No plates collected yet!</h3>
                <p>Start playing to build your collection. Find at least one word on a plate to add it here.</p>
              </div>
            </div>
          ) : (
            <div className="collected-plates-grid">
              {collectedPlates.map((plate) => (
                <div 
                  key={plate.plateId} 
                  className="collected-plate-card"
                  onClick={() => handlePlateClick(plate.plateId)}
                  style={{ borderLeft: `4px solid ${getDifficultyColor(plate.difficulty)}` }}
                >
                  <div className="plate-header">
                    <div className="plate-letters">{plate.letters}</div>
                    <div className="plate-difficulty" style={{ color: getDifficultyColor(plate.difficulty) }}>
                      <Target size={12} fill="currentColor" />
                      {getDifficultyTier(plate.difficulty)}
                    </div>
                  </div>

                  <div className="plate-progress">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: `${plate.completionPercentage}%`,
                          backgroundColor: getDifficultyColor(plate.difficulty)
                        }}
                      />
                    </div>
                    <span className="progress-text">
                      {plate.foundWords.length}/{plate.solution_count} words ({plate.completionPercentage}%)
                    </span>
                  </div>

                  <div className="plate-meta">
                    <div className="plate-score">
                      <Target size={12} />
                      {plate.totalScore.toLocaleString()} pts
                    </div>
                    <div className="plate-date">
                      <Calendar size={12} />
                      {formatDate(plate.lastPlayedDate)}
                    </div>
                  </div>

                  {plate.completionPercentage === 100 && (
                    <div className="completion-badge">
                      <Trophy size={14} />
                      Complete!
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <div className="collection-footer">
            PL8WRDS Collection • {stats.totalPlates} plates discovered
          </div>
        </div>
      </div>
    </div>
  );
};

export default CollectionModal;
