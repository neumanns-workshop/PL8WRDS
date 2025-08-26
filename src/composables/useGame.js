import { ref, reactive } from 'vue'
import DataManager from '../data/DataManager.js'
import LicensePlateSolver from '../game/LicensePlateSolver.js'
import GameAPI from '../game/GameAPI.js'

// Global game state
const gameState = reactive({
  score: 0,
  isInitialized: false,
  currentPlate: '',
  foundWords: [],
  gameAPI: null,
  dataManager: null,
  solver: null
})

// Difficulty mappings from your analysis
const plateDifficulties = {
  'trivial': { min: 7000, color: 'green', label: 'Trivial' },
  'easy': { min: 3000, color: 'blue', label: 'Easy' },
  'moderate': { min: 1500, color: 'yellow', label: 'Moderate' },
  'challenging': { min: 750, color: 'orange', label: 'Challenging' },
  'hard': { min: 300, color: 'red', label: 'Hard' },
  'extreme': { min: 1, color: 'purple', label: 'Extreme' }
}

// Popular plates for quick testing (from your analysis)
const samplePlates = [
  'CAT', 'DOG', 'FUN', 'CAR', 'SUN', 'RUN', 'BIG', 'NEW', 'OLD', 'HOT',
  'ALE', 'RIE', 'INE', 'AIE', 'ANE', 'ITE', 'TIE', 'ENE'  // Trivial ones
]

export function useGame() {
  
  // Initialize game systems
  const initializeGame = async () => {
    if (gameState.isInitialized) return gameState.gameAPI
    
    try {
      console.log('🎮 Initializing PL8WRDS game systems...')
      
      // Initialize data manager
      gameState.dataManager = new DataManager()
      await gameState.dataManager.initialize()
      
      // Initialize solver
      gameState.solver = new LicensePlateSolver(gameState.dataManager)
      
      // Initialize game API
      gameState.gameAPI = new GameAPI(gameState.dataManager, gameState.solver)
      
      gameState.isInitialized = true
      console.log('✅ Game systems ready!')
      
      return gameState.gameAPI
    } catch (error) {
      console.error('❌ Failed to initialize game:', error)
      throw error
    }
  }
  
  // Validate a word against current plate
  const validateWord = async (word, plateLetters) => {
    if (!gameState.isInitialized) {
      await initializeGame()
    }
    
    try {
      const result = await gameState.gameAPI.validateWord(word, plateLetters)
      return result
    } catch (error) {
      console.error('Error validating word:', error)
      return { valid: false, reason: 'system_error', word }
    }
  }
  
  // Generate a new license plate
  const generatePlate = () => {
    // For demo, randomly pick from sample plates
    // In production, you'd use your difficulty analysis
    const randomPlate = samplePlates[Math.floor(Math.random() * samplePlates.length)]
    gameState.currentPlate = randomPlate
    return randomPlate
  }
  
  // Get hints for current plate
  const getHints = async (plateLetters, count = 3) => {
    if (!gameState.isInitialized) {
      await initializeGame()
    }
    
    try {
      const hints = await gameState.gameAPI.generateHints(plateLetters, count)
      return hints
    } catch (error) {
      console.error('Error getting hints:', error)
      return [
        { type: 'error', message: 'Hints temporarily unavailable' }
      ]
    }
  }
  
  // Get word data for display
  const getWordData = async (word) => {
    if (!gameState.isInitialized) {
      await initializeGame()
    }
    
    try {
      return await gameState.gameAPI.getCompleteWordData(word)
    } catch (error) {
      console.error('Error getting word data:', error)
      return null
    }
  }
  
  // Check if game is ready
  const isReady = () => gameState.isInitialized
  
  // Test real data integration
  const testRealDataIntegration = async () => {
    try {
      await initializeGame()
      console.log('🔍 Testing real data integration...')
      
      // Test a real word
      const testWord = 'cat'
      const testPlate = 'CAT'
      
      const result = await gameState.gameAPI.validateWord(testWord, testPlate)
      console.log('✅ Real validation result:', result)
      
      return result
    } catch (error) {
      console.error('❌ Real data integration failed:', error)
      return null
    }
  }
  
  // Get sample data for demo purposes
  const getSampleWordData = () => {
    return {
      word: 'fantastic',
      length: 9,
      syllables: {
        syllables: 3,
        arpabet: "F AE2 N T AE1 S T IH0 K",
        source: "arpabet_analysis"
      },
      frequency: 0.0001,
      frequencyRank: 'common',
      pronunciation: {
        arpabet: ["F AE2 N T AE1 S T IH0 K"]
      },
      definitions: {
        wordnet: ['imaginative or fanciful; remote from reality'],
        wiktionary: ['existing in or produced by fantasy; imaginary']
      },
      etymologies: {
        etymonline: 'from Greek phantastikos "able to present to the mind"'
      },
      semanticRelationships: {
        synonyms: ['amazing', 'incredible', 'wonderful', 'marvelous'],
        antonyms: ['terrible', 'awful', 'horrible'],
        hypernyms: ['adjective'],
        hyponyms: []
      },
      lists: [],
      sentiment: 3,
      rhymeGroups: {
        perfect: ['plastic', 'drastic', 'elastic']
      }
    }
  }
  
  return {
    // State
    gameState,
    plateDifficulties,
    
    // Methods
    initializeGame,
    validateWord,
    generatePlate,
    getHints,
    getWordData,
    isReady,
    getSampleWordData,
    testRealDataIntegration
  }
} 