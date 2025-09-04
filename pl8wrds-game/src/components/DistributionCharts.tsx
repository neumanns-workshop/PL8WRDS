import React from 'react';
import { Plate } from '../types/game';

interface DistributionData {
  solutions: number[];
  scores: number[];
}

interface Percentiles {
  difficulty: number;
  score: number;
  plateAverageScore: number;
}

interface DistributionChartsProps {
  distributionData: DistributionData;
  plate: Plate;
  percentiles: Percentiles;
}

export const DistributionCharts: React.FC<DistributionChartsProps> = ({
  distributionData,
  plate,
  percentiles,
}) => {
  const renderDifficultyChart = () => {
    const data = distributionData.solutions;
    const bins = 40;
    
    // Log transform the data to compress the range
    const logData = data.map(value => Math.log10(Math.max(1, value)));
    const logMin = Math.min(...logData);
    const logMax = Math.max(...logData);
    const logBinSize = (logMax - logMin) / bins;
    
    const histogram = new Array(bins).fill(0);
    logData.forEach(logValue => {
      const binIndex = Math.min(Math.floor((logValue - logMin) / logBinSize), bins - 1);
      histogram[binIndex]++;
    });
    
    const maxCount = Math.max(...histogram);
    const currentLogValue = Math.log10(Math.max(1, plate.solution_count));
    const currentBin = Math.min(Math.floor((currentLogValue - logMin) / logBinSize), bins - 1);
    
    return histogram.map((count, i) => {
      const x = (i / bins) * 380 + 10;
      const height = (count / maxCount) * 80;
      const y = 100 - height;
      const width = 380 / bins - 1;
      
      return (
        <rect
          key={i}
          x={x}
          y={y}
          width={width}
          height={height}
          fill={i === currentBin ? '#C0392B' : '#BDC3C7'}
          opacity={i === currentBin ? 1 : 0.6}
        />
      );
    });
  };

  const renderScoreChart = () => {
    const data = distributionData.scores;
    const bins = 80;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const binSize = (max - min) / bins;
    
    const histogram = new Array(bins).fill(0);
    data.forEach(value => {
      const binIndex = Math.min(Math.floor((value - min) / binSize), bins - 1);
      histogram[binIndex]++;
    });
    
    const maxCount = Math.max(...histogram);
    const currentBin = Math.min(Math.floor((percentiles.plateAverageScore - min) / binSize), bins - 1);
    
    return histogram.map((count, i) => {
      const x = (i / bins) * 380 + 10;
      const height = (count / maxCount) * 80;
      const y = 100 - height;
      const width = 380 / bins - 1;
      
      return (
        <rect
          key={i}
          x={x}
          y={y}
          width={width}
          height={height}
          fill={i === currentBin ? '#1B4F72' : '#BDC3C7'}
          opacity={i === currentBin ? 1 : 0.6}
        />
      );
    });
  };

  return (
    <div className="distribution-charts">
      <div className="chart-container">
        <h4>Difficulty Distribution ({plate.solution_count} solutions, {percentiles.difficulty}th percentile)</h4>
        <svg width="400" height="120" className="distribution-svg">
          {renderDifficultyChart()}
          
          {/* X-axis labels */}
          <text x="10" y="115" fontSize="10" fill="#666">{Math.min(...distributionData.solutions)}</text>
          <text x="390" y="115" fontSize="10" fill="#666" textAnchor="end">{Math.max(...distributionData.solutions)}</text>
          <text x="200" y="115" fontSize="10" fill="#C0392B" textAnchor="middle" fontWeight="bold">{plate.solution_count}</text>
        </svg>
      </div>
      
      {distributionData.scores.length > 0 && (
        <div className="chart-container">
          <h4>Score Average Distribution ({percentiles.plateAverageScore.toFixed(1)}, {percentiles.score}th percentile)</h4>
          <svg width="400" height="120" className="distribution-svg">
            {renderScoreChart()}
            
            {/* X-axis labels */}
            <text x="10" y="115" fontSize="10" fill="#666">{Math.min(...distributionData.scores).toFixed(1)}</text>
            <text x="390" y="115" fontSize="10" fill="#666" textAnchor="end">{Math.max(...distributionData.scores).toFixed(1)}</text>
            <text x="200" y="115" fontSize="10" fill="#1B4F72" textAnchor="middle" fontWeight="bold">{percentiles.plateAverageScore.toFixed(1)}</text>
          </svg>
        </div>
      )}
    </div>
  );
};