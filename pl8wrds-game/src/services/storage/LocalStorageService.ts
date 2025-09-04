// Core localStorage operations with error handling and type safety

export class LocalStorageService {
  private static readonly STORAGE_KEY = 'pl8wrds_progress';

  /**
   * Safely get data from localStorage with error handling
   */
  static get<T>(key: string): T | null {
    try {
      const stored = localStorage.getItem(key);
      if (!stored) {
        return null;
      }
      return JSON.parse(stored) as T;
    } catch (error) {
      console.warn(`Failed to get data from localStorage for key "${key}":`, error);
      return null;
    }
  }

  /**
   * Safely set data to localStorage with error handling
   */
  static set<T>(key: string, data: T): boolean {
    try {
      localStorage.setItem(key, JSON.stringify(data));
      return true;
    } catch (error) {
      console.warn(`Failed to save data to localStorage for key "${key}":`, error);
      return false;
    }
  }

  /**
   * Remove data from localStorage
   */
  static remove(key: string): boolean {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.warn(`Failed to remove data from localStorage for key "${key}":`, error);
      return false;
    }
  }

  /**
   * Check if localStorage is available
   */
  static isAvailable(): boolean {
    try {
      const testKey = '__localStorage_test__';
      localStorage.setItem(testKey, 'test');
      localStorage.removeItem(testKey);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get the main storage key for user progress
   */
  static getProgressKey(): string {
    return this.STORAGE_KEY;
  }
}