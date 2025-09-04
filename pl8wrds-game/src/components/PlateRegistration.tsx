// RouteGuide component - Shows detailed route information like a vintage highway atlas
import React, { useState, useMemo } from 'react';
import { Plate, GameData } from '../types/game';
import { Book, X } from 'lucide-react';
import GameDataService from '../services/gameData';
import { useDistributionData } from '../hooks/useDistributionData';
import { usePercentiles } from '../hooks/usePercentiles';
import { useScoreBreakdown } from '../hooks/useScoreBreakdown';
import { DistributionCharts } from './DistributionCharts';
import { PlateStatistics } from './PlateStatistics';
import { FoundWordsList } from './FoundWordsList';
import { ScoreBreakdownModal } from './ScoreBreakdownModal';

interface RouteGuideProps {
  plate: Plate;
  foundWords: string[];
  onClose: () => void;
  gameData?: GameData | null;
}

export const RouteGuide: React.FC<RouteGuideProps> = ({
  plate,
  foundWords,
  onClose,
  gameData,
}) => {
  const [selectedWord, setSelectedWord] = useState<{word: string, score: number, breakdown: any} | null>(null);

  // Get the word dictionary
  const wordDictionary = useMemo(() => {
    return GameDataService.getInstance().getWordDictionary();
  }, []);

  // Use custom hooks for data processing
  const distributionData = useDistributionData({ gameData, wordDictionary });
  const percentiles = usePercentiles({ distributionData, plate, wordDictionary });
  const { getScoreBreakdown } = useScoreBreakdown({ plate, wordDictionary });

  // Handle word click for score breakdown
  const handleWordClick = (word: string) => {
    const breakdown = getScoreBreakdown(word);
    if (breakdown) {
      const solution = plate.solutions.find(sol => sol.word === word);
      if (solution) {
        setSelectedWord({
          word,
          score: solution.ensemble_score,
          breakdown
        });
      }
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content route-guide-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2><Book size={24} />Plate Details</h2>
          <button className="modal-close-button" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="route-plate-display">
          <div className="reg-plate-frame">
            <div className="reg-plate-letters">{plate.letters}</div>
          </div>
          <div className="reg-plate-id">Plate #{plate.id}</div>
        </div>

        <div className="modal-body">
          {distributionData && (
            <DistributionCharts 
              distributionData={distributionData}
              plate={plate}
              percentiles={percentiles}
            />
          )}

          <PlateStatistics 
            foundWordsCount={foundWords.length}
            totalSolutions={plate.solution_count}
          />

          <FoundWordsList 
            foundWords={foundWords}
            plate={plate}
            onWordClick={handleWordClick}
          />
        </div>

        <div className="info-footer">
          <p className="vintage-note">
            PL8WRDS Game • Plate Statistics
          </p>
        </div>
      </div>

      <ScoreBreakdownModal 
        selectedWord={selectedWord}
        onClose={() => setSelectedWord(null)}
      />
    </div>
  );
};

export default RouteGuide;