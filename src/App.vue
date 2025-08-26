<template>
  <div id="app">
    <!-- Active Game State -->
    <template v-if="isGameActive">
      <LicensePlate :plate-text="plateText" :difficulty="difficulty" :header-text="headerText" />
      
      <!-- Word Input Area -->
      <div class="word-input-area">
        <input 
          v-model="currentWord" 
          @keyup.enter="checkWord" 
          type="text" 
          placeholder="Enter a word" 
          class="flex-grow p-3 text-base rounded-lg bg-dark-surface border-dark-border text-dark-text font-game placeholder:text-gray-400" 
        />
        <button 
          @click="checkWord" 
          class="bg-game-correct text-white font-bold py-3 px-6 rounded-lg cursor-pointer"
        >
          Check
        </button>
      </div>
      
      <div class="controls">
        <button @click="generateRandomPlate" class="random-button">
          New Plate
        </button>
        <button @click="findWord" class="score-button">
          Find Word (Test)
        </button>
        <button @click="isInfoModalVisible = true" class="info-button" title="Plate Info">
          &#9432;
        </button>
      </div>
    </template>

    <!-- Initial Splash Screen -->
    <template v-else>
      <LicensePlate plate-text="PL8 WRDS" header-text="WELCOME TO" />
      <button @click="startGame" class="random-button">
        New Game
      </button>
    </template>

    <PlateInfoModal 
      :show="isInfoModalVisible" 
      :analysis="formattedAnalysis"
      @close="isInfoModalVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import LicensePlate from './components/LicensePlate.vue';
import PlateInfoModal from './components/PlateInfoModal.vue';
import DataManager from './data/DataManager.js';
import LicensePlateSolver from './game/LicensePlateSolver.js';
import { usePlateAnalysis } from './composables/usePlateAnalysis.js';

const dataManager = new DataManager();
const solver = new LicensePlateSolver();
const { formattedAnalysis, calculateAnalysis } = usePlateAnalysis(dataManager);

const isGameActive = ref(false);
const isLoading = ref(false);
const isInfoModalVisible = ref(false);
const plateLetters = ref('PL8');
const score = ref(0);
const wordsFound = ref(0);
const difficulty = ref('');
const allSolutions = ref([]);
const currentWord = ref('');
const foundWords = new Set();

const headerText = computed(() => {
  if (isLoading.value) return 'Loading...';
  return `${wordsFound.value} out of ${allSolutions.value.length}`;
});

const formattedScore = computed(() => {
  return score.value.toString().padStart(4, '0');
});

const plateText = computed(() => {
  return `${plateLetters.value} ${formattedScore.value}`;
});

watch(plateLetters, async (newLetters) => {
  if (newLetters && isGameActive.value) {
    isLoading.value = true;
    
    const plateData = await dataManager.getPlateData(newLetters);
    difficulty.value = plateData ? plateData.difficulty : 'Unranked';
    
    // Find all solutions using the solver
    const solutions = solver.findAllSolutions(newLetters, dataManager.getWords());
    allSolutions.value = solutions;
    foundWords.clear(); // Clear found words for the new plate

    // Run analysis
    await calculateAnalysis(solutions);

    isLoading.value = false;
  }
});

async function generateRandomPlate() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  let randomLetters = '';
  for (let i = 0; i < 3; i++) {
    randomLetters += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  plateLetters.value = randomLetters;
  score.value = 0;
  wordsFound.value = 0;
  foundWords.clear(); // Also clear here for safety
}

function findWord() {
  if (wordsFound.value < allSolutions.value.length) {
    wordsFound.value++;
    score.value += 10;
    if (score.value > 9999) score.value = 9999;
  }
}

function checkWord() {
  if (!currentWord.value) return;

  const wordToCheck = currentWord.value.toLowerCase();
  
  if (foundWords.has(wordToCheck)) {
    console.log(`You already found "${wordToCheck}"!`);
    currentWord.value = '';
    return;
  }
  
  const isValid = allSolutions.value.map(w => w.toLowerCase()).includes(wordToCheck);
  
  console.log(`Is "${wordToCheck}" a valid solution for "${plateLetters.value}"?`, isValid);
  
  if (isValid) {
    console.log('Correct!');
    foundWords.add(wordToCheck);
    // This call replaces the old test button functionality
    findWord(); 
  } else {
    console.log('Incorrect, try again.');
  }

  currentWord.value = ''; // Clear input after check
}

async function startGame() {
  await dataManager.initialize();
  isGameActive.value = true;
  await generateRandomPlate();
}
</script>

<style>
:root {
  --app-bg-color: #1a202c; /* A dark slate gray */
}

body, html {
  margin: 0;
  padding: 0;
}
#app {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  height: 100vh;
  background-color: var(--app-bg-color);
}

.controls {
  display: flex;
  gap: 1rem;
}

.random-button, .score-button {
  @apply bg-gray-600 text-white font-bold py-3 px-4 rounded-lg cursor-pointer transition-colors duration-200;
}
.random-button:hover, .score-button:hover {
  @apply bg-gray-700;
}
.score-button {
  @apply bg-blue-700;
}
.score-button:hover {
  @apply bg-blue-800;
}

.word-input-area {
  display: flex;
  gap: 0.5rem;
  width: 100%;
  max-width: 22rem; /* Match license plate width */
  margin-top: 1rem;
}

.info-button {
  @apply bg-gray-500 text-white font-bold w-12 h-12 rounded-lg cursor-pointer transition-colors duration-200 flex items-center justify-center text-2xl;
}
.info-button:hover {
  @apply bg-gray-600;
}
</style> 