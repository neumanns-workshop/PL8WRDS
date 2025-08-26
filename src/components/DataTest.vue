<template>
  <div class="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg mb-4">
    <h3 class="font-bold text-lg mb-3">🔍 Real Data Test</h3>
    
    <div class="space-y-3">
      <button 
        @click="testDataAccess" 
        :disabled="testing"
        class="game-button text-sm py-2"
      >
        {{ testing ? 'Testing...' : 'Test Your 117K Word Database' }}
      </button>
      
      <div v-if="testResults.length > 0" class="space-y-2">
        <h4 class="font-semibold">Results from your data:</h4>
        <div class="bg-white dark:bg-gray-700 p-3 rounded text-sm space-y-2">
          <div v-for="(result, index) in testResults" :key="index" class="text-black dark:text-white">
            <strong>{{ result.word }}:</strong>
            <div class="ml-4 text-xs space-y-1 text-black dark:text-white">
              <div v-if="result.pronunciation">🗣️ {{ result.pronunciation }}</div>
              <div v-if="result.syllables">📏 {{ result.syllables }} syllables</div>
              <div v-if="result.frequency">📊 Frequency: {{ result.frequency }}</div>
              <div v-if="result.definition">📖 {{ result.definition }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="error" class="text-red-600 text-sm">
        ❌ Error: {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DataManager from '../data/DataManager.js'

const testing = ref(false)
const testResults = ref([])
const error = ref('')

const testDataAccess = async () => {
  testing.value = true
  testResults.value = []
  error.value = ''
  
  try {
    console.log('🔍 Testing direct DataManager access...')
    
    const dataManager = new DataManager()
    await dataManager.initialize()
    
    console.log('✅ DataManager initialized with', dataManager.getWords().length, 'words')
    
    // Test a few words
    const testWords = ['cat', 'fantastic', 'host', 'computer']
    
    for (const word of testWords) {
      const result = { word }
      
      // Get pronunciation
      const pronunciation = await dataManager.getPronunciation(word)
      if (pronunciation && pronunciation.arpabet) {
        result.pronunciation = Array.isArray(pronunciation.arpabet) 
          ? pronunciation.arpabet[0] 
          : pronunciation.arpabet
      }
      
      // Get syllables
      const syllables = await dataManager.getSyllableCount(word)
      if (syllables && syllables.syllables) {
        result.syllables = syllables.syllables
      }
      
      // Get frequency
      const frequency = await dataManager.getFrequency(word)
      if (frequency && frequency.frequency) {
        result.frequency = frequency.frequency.toFixed(6)
      }
      
      // Get definition
      const definitions = await dataManager.getDefinitions(word)
      if (definitions) {
        for (const [source, defs] of Object.entries(definitions)) {
          if (Array.isArray(defs) && defs.length > 0) {
            result.definition = defs[0].substring(0, 100) + '...'
            break
          }
        }
      }
      
      testResults.value.push(result)
    }
    
    console.log('✅ Data test complete:', testResults.value)
    
  } catch (err) {
    console.error('❌ Data test failed:', err)
    error.value = err.message
  } finally {
    testing.value = false
  }
}
</script> 