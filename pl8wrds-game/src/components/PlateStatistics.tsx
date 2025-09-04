import React from 'react';

interface PlateStatisticsProps {
  foundWordsCount: number;
  totalSolutions: number;
}

export const PlateStatistics: React.FC<PlateStatisticsProps> = ({
  foundWordsCount,
  totalSolutions,
}) => {
  return (
    <div className="stats-list">
      <div className="stat-row">
        <span className="stat-label">Found:</span>
        <span className="stat-value">{foundWordsCount} / {totalSolutions}</span>
      </div>
    </div>
  );
};