// Game types for PL8WRDS

export interface WordDictionary {
  [wordId: string]: {
    word: string;
    frequency_score: number;
    orthographic_score: number;
  };
}

export interface GameData {
  format: string;
  description: string;
  plates: {
    letters: string[];
    solutions: { [wordId: string]: number }; // word_id -> info_score
  }[];
}

export interface Plate {
  id: string;
  letters: string;
  difficulty: number; // Based on solution count (fewer = harder)
  solution_count: number;
  solutions: Solution[];
}

export interface Solution {
  word: string;
  wordId: number;
  ensemble_score: number;
  vocabulary_score: number;
  information_score: number;
  orthographic_score: number;
  found: boolean;
}

export interface GameState {
  currentPlate: Plate | null;
  solutions: Solution[];
  foundWords: string[];
  currentWord: string;
  score: number;
  gameStatus: 'idle' | 'playing' | 'completed';
  timeRemaining?: number;
  gameData: GameData | null;
  wordDictionary: WordDictionary | null;
}

export function getDifficultyPercentile(solutionCount: number): number {
  // Convert solution count to difficulty percentile (fewer solutions = higher percentile = harder)
  // Based on approximate distribution of solution counts across all plates
  if (solutionCount >= 1000) return 5;   // Very easy - 5th percentile
  if (solutionCount >= 600) return 15;   // Easy - 15th percentile
  if (solutionCount >= 300) return 35;   // Below average - 35th percentile
  if (solutionCount >= 150) return 50;   // Average - 50th percentile
  if (solutionCount >= 75) return 70;    // Above average - 70th percentile
  if (solutionCount >= 30) return 85;    // Hard - 85th percentile
  if (solutionCount >= 15) return 95;    // Very hard - 95th percentile
  return 99;                             // Extremely hard - 99th percentile
}

export function getScorePercentile(averageScore: number): number {
  // Convert average score to percentile (higher score = higher percentile = better quality)
  // Based on approximate distribution of average scores across all plates
  if (averageScore >= 70) return 95;     // Exceptional - 95th percentile
  if (averageScore >= 60) return 85;     // Excellent - 85th percentile
  if (averageScore >= 50) return 70;     // Good - 70th percentile
  if (averageScore >= 40) return 50;     // Average - 50th percentile
  if (averageScore >= 35) return 30;     // Below average - 30th percentile
  if (averageScore >= 30) return 15;     // Poor - 15th percentile
  return 5;                              // Very poor - 5th percentile
}

export function getDifficultyColor(percentile: number): string {
  // Color coding based on difficulty percentile
  if (percentile >= 95) return '#dc3545'; // Red - Very Hard
  if (percentile >= 80) return '#fd7e14'; // Orange - Hard
  if (percentile >= 60) return '#ffc107'; // Yellow - Above Average
  if (percentile >= 40) return '#28a745'; // Green - Below Average
  return '#17a2b8';                       // Cyan - Easy
}

export function getScoreColor(percentile: number): string {
  // Color coding based on score percentile
  if (percentile >= 95) return '#6f42c1'; // Purple - Exceptional
  if (percentile >= 80) return '#007bff'; // Blue - Excellent
  if (percentile >= 60) return '#20c997'; // Teal - Good
  if (percentile >= 40) return '#28a745'; // Green - Average
  return '#6c757d';                       // Gray - Below Average
}

export function getPlateColor(plate: Plate): string {
  // Generate plate color based on difficulty
  const difficultyPercentile = getDifficultyPercentile(plate.solution_count);
  return getDifficultyColor(difficultyPercentile);
}

