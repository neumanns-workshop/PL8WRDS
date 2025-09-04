// Clean storage architecture - export all services and types
export { LocalStorageService } from './LocalStorageService';
export { ProgressStorageService } from './ProgressStorageService';
export { CollectionAnalyticsService } from './CollectionAnalyticsService';
export { BackupService } from './BackupService';

export type {
  CollectedPlate,
  UserProgress,
  CollectionStats,
  SortOption,
  DifficultyTier
} from './types';