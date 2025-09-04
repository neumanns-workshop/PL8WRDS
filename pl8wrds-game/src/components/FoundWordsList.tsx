import React, { useState, useMemo } from 'react';
import { Plate } from '../types/game';

export type SortBy = 'ensemble' | 'vocabulary' | 'information' | 'orthographic' | 'alpha';

interface WordWithScores {
  word: string;
  ensemble_score: number;
  vocabulary_score: number;
  information_score: number;
  orthographic_score: number;
}

interface FoundWordsListProps {
  foundWords: string[];
  plate: Plate;
  onWordClick: (word: string) => void;
}

export const FoundWordsList: React.FC<FoundWordsListProps> = ({
  foundWords,
  plate,
  onWordClick,
}) => {
  const [sortBy, setSortBy] = useState<SortBy>('ensemble');

  // Create sorted list of found words with their component scores
  const sortedFoundWords = useMemo(() => {
    const foundWordsWithScores: WordWithScores[] = foundWords.map(word => {
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

  if (foundWords.length === 0) {
    return null;
  }

  return (
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
            onClick={() => onWordClick(wordData.word)}
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
  );
};