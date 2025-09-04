// Import/export and migration functionality for user progress
import { UserProgress } from './types';
import { ProgressStorageService } from './ProgressStorageService';

export class BackupService {
  
  /**
   * Export progress as JSON string (for backup)
   */
  static exportProgress(): string {
    const progress = ProgressStorageService.loadProgress();
    return JSON.stringify(progress, null, 2);
  }

  /**
   * Import progress from JSON string (for restore)
   */
  static importProgress(jsonData: string): boolean {
    try {
      const progress = JSON.parse(jsonData) as UserProgress;
      
      // Validate the imported data structure
      if (!this.isValidProgressData(progress)) {
        console.error('Invalid progress data structure');
        return false;
      }
      
      return ProgressStorageService.saveProgress(progress);
    } catch (error) {
      console.error('Failed to import progress:', error);
      return false;
    }
  }

  /**
   * Create a downloadable backup file
   */
  static downloadBackup(filename?: string): void {
    const exportData = this.exportProgress();
    const blob = new Blob([exportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `pl8wrds-backup-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up the URL object
    URL.revokeObjectURL(url);
  }

  /**
   * Validate imported progress data structure
   */
  private static isValidProgressData(data: any): data is UserProgress {
    return (
      data &&
      typeof data === 'object' &&
      typeof data.collectedPlates === 'object' &&
      typeof data.totalPlatesFound === 'number' &&
      typeof data.totalWordsFound === 'number' &&
      typeof data.totalScore === 'number' &&
      typeof data.lastPlayed === 'string' &&
      typeof data.version === 'string'
    );
  }
}