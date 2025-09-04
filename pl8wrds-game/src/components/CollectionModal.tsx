import React, { useState, useMemo } from 'react';
import { X, Trophy, Filter, Award } from 'lucide-react';
import StorageService from '../services/storage';
import PlateDisplay from './PlateDisplay';
import GameDataService from '../services/gameData';

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

  const gameDataService = GameDataService.getInstance();
  
  const collectedPlates = useMemo(() => {
    let plates = StorageService.getCollectedPlates(sortBy);
    
    if (selectedDifficulty !== 'all') {
      plates = plates.filter(plate => getDifficultyTier(plate.difficulty) === selectedDifficulty);
    }
    
    // Get actual plate objects from game data
    return plates.map(collectedPlate => {
      const actualPlate = gameDataService.getPlateById(collectedPlate.plateId);
      return actualPlate ? { ...actualPlate, collectionData: collectedPlate } : null;
    }).filter((plate): plate is NonNullable<typeof plate> => plate !== null);
  }, [sortBy, selectedDifficulty, gameDataService]);

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
    if (difficulty >= 90) return '#8B2635'; // Dark red - Ultra Hard
    if (difficulty >= 80) return '#B45309'; // Dark orange - Very Hard  
    if (difficulty >= 60) return '#CA8A04'; // Dark yellow - Hard
    if (difficulty >= 30) return '#166534'; // Dark green - Medium
    return '#0F766E'; // Dark teal - Easy
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
          <button className="modal-close-button" onClick={onClose}>
            <X size={24} />
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
                <div key={plate.id} className="collection-plate-wrapper">
                  <PlateDisplay 
                    plate={plate}
                    foundWordsCount={plate.collectionData?.foundWords.length || 0}
                    totalSolutions={plate.solutions.length}
                    foundWords={plate.collectionData?.foundWords || []}
                    currentScore={plate.collectionData?.totalScore || 0}
                    onNewPlate={() => handlePlateClick(plate.id)}
                  />
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
