// API service for PL8WRDS game (unused - keeping for reference)
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export class PL8WRDSApi {
  /**
   * Get all solutions for a license plate
   */
  static async solvePlate(plate: string): Promise<any> {
    const response = await api.get(`/solve/${plate}`);
    return response.data;
  }

  /**
   * Score a word-plate combination
   */
  static async scoreWord(word: string, plate: string): Promise<any> {
    const response = await api.post('/predict/ensemble', {
      word,
      plate,
      weights: {
        vocabulary: 1.0,
        information: 1.0,
        orthographic: 1.0,
      },
    });
    return response.data;
  }

  /**
   * Get corpus statistics
   */
  static async getCorpusStats() {
    const response = await api.get('/corpus/stats');
    return response.data;
  }

  /**
   * Validate if a word contains plate letters in correct order
   * This is client-side validation before scoring
   */
  static validateWord(word: string, plate: string): boolean {
    const wordLower = word.toLowerCase();
    const plateLower = plate.toLowerCase();
    
    let plateIndex = 0;
    
    for (let i = 0; i < wordLower.length && plateIndex < plateLower.length; i++) {
      if (wordLower[i] === plateLower[plateIndex]) {
        plateIndex++;
      }
    }
    
    return plateIndex === plateLower.length;
  }

  /**
   * Generate a random plate for gameplay
   */
  static generateRandomPlate(): string {
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    let result = '';
    for (let i = 0; i < 3; i++) {
      result += letters.charAt(Math.floor(Math.random() * letters.length));
    }
    return result;
  }
}

export default PL8WRDSApi;
