// RouteGuide component - Shows detailed route information like a vintage highway atlas
import React, { useState, useMemo } from 'react';
import { Plate, GameData } from '../types/game';
import { Book, X } from 'lucide-react';
import GameDataService from '../services/gameData';

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
  const [sortBy, setSortBy] = useState<'ensemble' | 'vocabulary' | 'information' | 'orthographic' | 'alpha'>('ensemble');
  const [selectedWord, setSelectedWord] = useState<{word: string, score: number, breakdown: any} | null>(null);

  // Get the word dictionary
  const wordDictionary = useMemo(() => {
    return GameDataService.getInstance().getWordDictionary();
  }, []);

  // Get component score breakdown for a word
  const getScoreBreakdown = (word: string) => {
    if (!wordDictionary) return null;
    
    // Find the solution directly by word
    const solution = plate.solutions.find(sol => sol.word === word);
    if (!solution) return null;
    
    // Find the word data in the dictionary
    const wordData = wordDictionary[solution.wordId.toString()];
    
    return {
      word,
      ensemble_score: solution.ensemble_score,
      vocabulary_score: solution.vocabulary_score,
      information_score: solution.information_score,
      orthographic_score: solution.orthographic_score,
      details: {
        wordFrequency: wordData?.frequency_score || 0,
        wordLength: word.length,
        plateId: plate.letters,
        solutionCount: plate.solution_count
      }
    };
  };
  
  // Create distribution data from all plates
    const distributionData = React.useMemo(() => {
    if (!gameData) return null;

    try {
      const allSolutionCounts: number[] = [];
      // Calculate actual average ensemble scores for distribution analysis
      const allAverageScores: number[] = [];

      gameData.plates.forEach(plateData => {
        const solutionCount = Object.keys(plateData.solutions).length;
        allSolutionCounts.push(solutionCount);
        
        // Calculate actual average ensemble score for this plate
        let totalScore = 0;
        let scoreCount = 0;
        
        Object.entries(plateData.solutions).forEach(([wordId, infoScore]) => {
          const wordData = wordDictionary?.[wordId];
          if (wordData) {
            const vocabScore = wordData.frequency_score || 0;
            const orthoScore = wordData.orthographic_score || 0;
            const ensembleScore = (vocabScore + (infoScore as number) + orthoScore) / 3;
            totalScore += ensembleScore;
            scoreCount++;
          }
        });
        
        const averageScore = scoreCount > 0 ? totalScore / scoreCount : 0;
        allAverageScores.push(averageScore);
      });

      return {
        solutions: allSolutionCounts.sort((a, b) => a - b),
        scores: allAverageScores.sort((a, b) => a - b)
      };
    } catch (error) {
      console.error('Error building distribution data:', error);
      return null;
    }
  }, [gameData, wordDictionary]);

  // Calculate real percentiles from actual data distribution
  const realPercentiles = useMemo(() => {
    if (!distributionData || !wordDictionary) return { difficulty: 50, score: 50, plateAverageScore: 0 };
    
    // Find real difficulty percentile (fewer solutions = harder = higher percentile)
    const difficultyIndex = distributionData.solutions.findIndex(count => count >= plate.solution_count);
    const difficultyPercentile = difficultyIndex >= 0 
      ? Math.round((1 - difficultyIndex / distributionData.solutions.length) * 100)
      : 1;
    
    // Calculate this plate's actual average ensemble score
    const plateAverageScore = plate.solutions.reduce((sum, solution) => sum + solution.ensemble_score, 0) / plate.solutions.length;
    
    // Find real score percentile using actual average ensemble score (higher score = higher percentile)  
    const scoreIndex = distributionData.scores.findIndex(score => score >= plateAverageScore);
    const scorePercentile = scoreIndex >= 0 
      ? Math.round((scoreIndex / distributionData.scores.length) * 100)
      : 100;
    
    return {
      difficulty: Math.max(1, Math.min(99, difficultyPercentile)),
      score: Math.max(1, Math.min(99, scorePercentile)),
      plateAverageScore
    };
  }, [distributionData, plate.solution_count, plate.solutions, wordDictionary]);

  // Create sorted list of found words with their component scores
  const sortedFoundWords = useMemo(() => {
    const foundWordsWithScores = foundWords.map(word => {
      // Find the solution directly by word
      const solution = plate.solutions.find(sol => sol.word === word);
      
      if (!solution) {
        return {
          word,
          ensemble_score: 0,
          vocabulary_score: 0,
          information_score: 0,
          orthographic_score: 0
        };
      }
      
      return {
        word,
        ensemble_score: solution.ensemble_score,
        vocabulary_score: solution.vocabulary_score,
        information_score: solution.information_score,
        orthographic_score: solution.orthographic_score
      };
    });

    return foundWordsWithScores.sort((a, b) => {
      if (sortBy === 'alpha') {
        return a.word.localeCompare(b.word);
      } else {
        // Map sortBy to actual property names
        const scoreMap = {
          ensemble: 'ensemble_score',
          vocabulary: 'vocabulary_score', 
          information: 'information_score',
          orthographic: 'orthographic_score'
        };
        const propName = scoreMap[sortBy as keyof typeof scoreMap];
        const scoreA = a[propName as keyof typeof a] as number;
        const scoreB = b[propName as keyof typeof b] as number;
        return scoreB - scoreA; // Highest score first
      }
    });
  }, [foundWords, plate.solutions, sortBy]);

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
            <div className="distribution-charts">
              <div className="chart-container">
                <h4>Difficulty Distribution ({plate.solution_count} solutions, {realPercentiles.difficulty}th percentile)</h4>
                <svg width="400" height="120" className="distribution-svg">
                  {/* Create log-scale histogram from solution counts */}
                  {(() => {
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
                  })()}
                  
                  {/* X-axis labels */}
                  <text x="10" y="115" fontSize="10" fill="#666">{Math.min(...distributionData.solutions)}</text>
                  <text x="390" y="115" fontSize="10" fill="#666" textAnchor="end">{Math.max(...distributionData.solutions)}</text>
                  <text x="200" y="115" fontSize="10" fill="#C0392B" textAnchor="middle" fontWeight="bold">{plate.solution_count}</text>
                </svg>
              </div>
              
              {distributionData.scores.length > 0 && (
                <div className="chart-container">
                  <h4>Score Average Distribution ({realPercentiles.plateAverageScore.toFixed(1)}, {realPercentiles.score}th percentile)</h4>
                  <svg width="400" height="120" className="distribution-svg">
                    {/* Create histogram from scores */}
                    {(() => {
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
                      const currentBin = Math.min(Math.floor((realPercentiles.plateAverageScore - min) / binSize), bins - 1);
                      
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
                    })()}
                    
                    {/* X-axis labels */}
                    <text x="10" y="115" fontSize="10" fill="#666">{Math.min(...distributionData.scores).toFixed(1)}</text>
                    <text x="390" y="115" fontSize="10" fill="#666" textAnchor="end">{Math.max(...distributionData.scores).toFixed(1)}</text>
                    <text x="200" y="115" fontSize="10" fill="#1B4F72" textAnchor="middle" fontWeight="bold">{realPercentiles.plateAverageScore.toFixed(1)}</text>
                  </svg>
                </div>
              )}
            </div>
          )}

          <div className="stats-list">
            <div className="stat-row">
              <span className="stat-label">Found:</span>
              <span className="stat-value">{foundWords.length} / {plate.solution_count}</span>
            </div>
          </div>

          {foundWords.length > 0 && (
            <div className="found-words-section">
              <div className="found-words-header">
                <h4>Found Words</h4>
                <div className="sort-controls">
                  <button 
                    className={`sort-btn ${sortBy === 'ensemble' ? 'active' : ''}`}
                    onClick={() => setSortBy('ensemble')}
                  >
                    Ensemble
                  </button>
                  <button 
                    className={`sort-btn ${sortBy === 'vocabulary' ? 'active' : ''}`}
                    onClick={() => setSortBy('vocabulary')}
                  >
                    Vocabulary
                  </button>
                  <button 
                    className={`sort-btn ${sortBy === 'information' ? 'active' : ''}`}
                    onClick={() => setSortBy('information')}
                  >
                    Information
                  </button>
                  <button 
                    className={`sort-btn ${sortBy === 'orthographic' ? 'active' : ''}`}
                    onClick={() => setSortBy('orthographic')}
                  >
                    Orthography
                  </button>
                  <button 
                    className={`sort-btn ${sortBy === 'alpha' ? 'active' : ''}`}
                    onClick={() => setSortBy('alpha')}
                  >
                    A-Z
                  </button>
                </div>
              </div>
              <div className="found-words-list">
                {sortedFoundWords.map((wordData, index) => (
                  <div 
                    key={index} 
                    className="found-word-item clickable"
                    onClick={() => {
                      const breakdown = getScoreBreakdown(wordData.word);
                      if (breakdown) {
                        setSelectedWord({
                          word: wordData.word,
                          score: wordData.ensemble_score,
                          breakdown
                        });
                      }
                    }}
                    title="Click to see detailed score breakdown"
                  >
                    <div className="found-word-info">
                      <span className="found-word">{wordData.word}</span>
                      <div className="component-scores">
                        <span className="score-item">
                          <span className="score-label">E:</span>
                          <span className="score-value">{wordData.ensemble_score}</span>
                        </span>
                        <span className="score-item">
                          <span className="score-label">V:</span>
                          <span className="score-value">{wordData.vocabulary_score}</span>
                        </span>
                        <span className="score-item">
                          <span className="score-label">I:</span>
                          <span className="score-value">{wordData.information_score}</span>
                        </span>
                        <span className="score-item">
                          <span className="score-label">O:</span>
                          <span className="score-value">{wordData.orthographic_score}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="info-footer">
          <p className="vintage-note">
            PL8WRDS Game • Plate Statistics
          </p>
        </div>
      </div>

      {/* Score Breakdown Modal */}
      {selectedWord && (
        <div className="modal-overlay" onClick={() => setSelectedWord(null)}>
          <div className="modal-content score-breakdown-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Score Breakdown: {selectedWord.breakdown.word.toUpperCase()}</h2>
              <button className="modal-close-button" onClick={() => setSelectedWord(null)}>
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
      )}
    </div>
  );
};

export default RouteGuide;
