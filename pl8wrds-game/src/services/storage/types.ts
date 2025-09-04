// Shared types for the storage system

export interface CollectedPlate {
  plateId: string;
  letters: string;
  difficulty: number;
  solution_count: number;
  foundWords: string[];
  totalScore: number;
  firstFoundDate: string; // ISO date string
  lastPlayedDate: string; // ISO date string
  completionPercentage: number; // 0-100
}

export interface UserProgress {
  collectedPlates: { [plateId: string]: CollectedPlate };
  totalPlatesFound: number;
  totalWordsFound: number;
  totalScore: number;
  lastPlayed: string; // ISO date string
  version: string; // For future data migration
}

export interface CollectionStats {
  totalPlates: number;
  totalWords: number;
  totalScore: number;
  averageCompletion: number;
  difficultyBreakdown: { [key: string]: number };
}

export type SortOption = 'recent' | 'completion' | 'difficulty' | 'letters';

export type DifficultyTier = 'Easy' | 'Medium' | 'Hard' | 'Very Hard' | 'Ultra Hard';