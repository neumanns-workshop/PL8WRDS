<template>
  <div class="word-card group cursor-pointer" @click="toggleExpanded">
    <!-- Word Header -->
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-2">
        <h4 class="font-semibold text-lg text-gray-900 dark:text-white">
          {{ wordData.word }}
        </h4>
        <div class="flex gap-1">
          <!-- Rarity Badge -->
          <span 
            v-if="rarityBadge"
            class="px-2 py-1 text-xs font-medium rounded-full"
            :class="rarityBadge.class"
          >
            {{ rarityBadge.text }}
          </span>
          
          <!-- Sentiment Badge -->
          <span 
            v-if="sentimentBadge"
            class="px-2 py-1 text-xs font-medium rounded-full"
            :class="sentimentBadge.class"
          >
            {{ sentimentBadge.text }}
          </span>
        </div>
      </div>
      
      <!-- Score -->
      <div class="font-bold text-blue-600 dark:text-blue-400">
        +{{ calculateScore(wordData) }}
      </div>
    </div>

    <!-- Quick Info -->
    <div class="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-300 mb-3">
      <span>{{ wordData.length }} letters</span>
      <span v-if="syllableCount">{{ syllableCount }} syllable{{ syllableCount !== 1 ? 's' : '' }}</span>
      <span v-if="wordData.frequencyRank">{{ wordData.frequencyRank }}</span>
    </div>

    <!-- Pronunciation (if available) -->
    <div v-if="cleanPronunciation" class="mb-3">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-200">🗣️</span>
        <span class="font-mono text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
          {{ cleanPronunciation }}
        </span>
      </div>
    </div>

    <!-- Short Definition -->
    <div v-if="shortDefinition" class="mb-3">
      <p class="text-sm text-black dark:text-white line-clamp-2">
        {{ shortDefinition }}
      </p>
    </div>

    <!-- Expand/Collapse Indicator -->
    <div class="flex items-center justify-between">
      <div class="flex gap-2">
        <!-- Etymology Indicator -->
        <span v-if="wordData.etymologies" class="text-xs text-gray-500">🌳 Etymology</span>
        <!-- Rhymes Indicator -->
        <span v-if="hasRhymes" class="text-xs text-gray-500">🎵 Rhymes</span>
        <!-- Relationships Indicator -->
        <span v-if="hasRelationships" class="text-xs text-gray-500">🔗 Related</span>
      </div>
      
      <button class="text-xs text-blue-600 dark:text-blue-400 font-medium">
        {{ expanded ? 'Less' : 'More' }} info
      </button>
    </div>

    <!-- Expanded Content -->
    <div v-if="expanded" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600 space-y-4">
      
      <!-- Definitions -->
      <div v-if="wordData.definitions" class="space-y-2">
        <h5 class="font-medium text-gray-900 dark:text-white flex items-center gap-2">
          📖 Definitions
        </h5>
        <div class="space-y-1">
                     <div 
             v-for="(defs, source) in cleanDefinitions" 
             :key="source"
             class="text-sm"
           >
             <span class="font-medium text-gray-800 dark:text-gray-200 capitalize">{{ source }}:</span>
             <div class="text-black dark:text-white ml-2 space-y-1">
               <div v-for="(def, index) in defs.slice(0, 2)" :key="index">
                 {{ cleanDefinitionText(def) }}
               </div>
               <div v-if="defs.length > 2" class="text-xs text-gray-500">
                 +{{ defs.length - 2 }} more definitions
               </div>
             </div>
           </div>
        </div>
      </div>

      <!-- Etymology -->
      <div v-if="wordData.etymologies" class="space-y-2">
        <h5 class="font-medium text-gray-900 dark:text-white flex items-center gap-2">
          🌳 Etymology
        </h5>
        <div class="space-y-1">
                     <div 
             v-for="(etym, source) in wordData.etymologies" 
             :key="source"
             class="text-sm"
           >
             <span class="font-medium text-gray-800 dark:text-gray-200 capitalize">{{ source }}:</span>
             <span class="text-black dark:text-white ml-2">
               {{ etym.substring(0, 150) }}{{ etym.length > 150 ? '...' : '' }}
             </span>
           </div>
        </div>
      </div>

      <!-- Semantic Relationships -->
      <div v-if="wordData.semanticRelationships" class="space-y-2">
        <h5 class="font-medium text-gray-900 dark:text-white flex items-center gap-2">
          🔗 Related Words
        </h5>
        <div class="space-y-2">
          <div 
            v-for="(words, type) in limitedRelationships" 
            :key="type"
            class="text-sm"
          >
                         <span class="font-medium text-gray-800 dark:text-gray-200 capitalize">{{ type }}:</span>
            <div class="flex flex-wrap gap-1 mt-1">
              <span 
                v-for="word in words.slice(0, 5)" 
                :key="word"
                class="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs"
              >
                {{ word }}
              </span>
              <span v-if="words.length > 5" class="text-xs text-gray-500">
                +{{ words.length - 5 }} more
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Word Lists -->
      <div v-if="wordData.lists && wordData.lists.length > 0" class="space-y-2">
        <h5 class="font-medium text-gray-900 dark:text-white flex items-center gap-2">
          🏷️ Word Lists
        </h5>
        <div class="flex flex-wrap gap-1">
          <span 
            v-for="list in wordData.lists" 
            :key="list"
            class="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded text-xs"
          >
            {{ list }}
          </span>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  wordData: {
    type: Object,
    required: true
  }
})

const expanded = ref(false)

const toggleExpanded = () => {
  expanded.value = !expanded.value
}

// Computed properties for displaying data
const syllableCount = computed(() => {
  // Handle different syllable data formats
  if (typeof props.wordData.syllables === 'number') {
    return props.wordData.syllables
  }
  if (props.wordData.syllables && typeof props.wordData.syllables === 'object') {
    return props.wordData.syllables.syllables
  }
  return null
})

const cleanPronunciation = computed(() => {
  // Handle different pronunciation formats
  if (typeof props.wordData.pronunciation === 'string') {
    return props.wordData.pronunciation
  }
  if (props.wordData.pronunciation && Array.isArray(props.wordData.pronunciation.arpabet)) {
    return props.wordData.pronunciation.arpabet[0]
  }
  if (props.wordData.pronunciation && props.wordData.pronunciation.arpabet) {
    return props.wordData.pronunciation.arpabet
  }
  return null
})

const rarityBadge = computed(() => {
  const rank = props.wordData.frequencyRank
  const badges = {
    'very_rare': { text: '💎 Very Rare', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' },
    'rare': { text: '⭐ Rare', class: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' },
    'uncommon': { text: '🔸 Uncommon', class: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' }
  }
  return badges[rank] || null
})

const sentimentBadge = computed(() => {
  const sentiment = props.wordData.sentiment
  if (!sentiment) return null
  
  if (sentiment > 2) return { text: '😊 Very Positive', class: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' }
  if (sentiment > 0) return { text: '🙂 Positive', class: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' }
  if (sentiment < -2) return { text: '😢 Very Negative', class: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' }
  if (sentiment < 0) return { text: '😐 Negative', class: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' }
  
  return null
})

const shortDefinition = computed(() => {
  if (!props.wordData.definitions) return null
  
  // Get first definition from any source
  for (const [source, defs] of Object.entries(props.wordData.definitions)) {
    if (Array.isArray(defs) && defs.length > 0) {
      const def = defs[0]
      return def.length > 100 ? def.substring(0, 100) + '...' : def
    } else if (typeof defs === 'string') {
      return defs.length > 100 ? defs.substring(0, 100) + '...' : defs
    }
  }
  return null
})

const hasRhymes = computed(() => {
  return props.wordData.rhymeGroups && Object.keys(props.wordData.rhymeGroups).length > 0
})

const hasRelationships = computed(() => {
  return props.wordData.semanticRelationships && Object.keys(props.wordData.semanticRelationships).length > 0
})

const limitedRelationships = computed(() => {
  if (!props.wordData.semanticRelationships) return {}
  
  // Limit to most interesting relationship types
  const types = ['synonyms', 'antonyms', 'hypernyms', 'hyponyms']
  const limited = {}
  
  for (const type of types) {
    if (props.wordData.semanticRelationships[type]) {
      limited[type] = props.wordData.semanticRelationships[type]
    }
  }
  
  return limited
})

const cleanDefinitions = computed(() => {
  if (!props.wordData.definitions) return {}
  
  const cleaned = {}
  for (const [source, defs] of Object.entries(props.wordData.definitions)) {
    if (Array.isArray(defs)) {
      cleaned[source] = defs
    } else if (typeof defs === 'string') {
      cleaned[source] = [defs]
    } else if (defs && typeof defs === 'object') {
      // Handle complex definition objects
      cleaned[source] = [defs.definition || JSON.stringify(defs)]
    }
  }
  return cleaned
})

const cleanDefinitionText = (def) => {
  if (typeof def === 'string') {
    return def
  } else if (def && typeof def === 'object') {
    // Extract text from definition objects
    return def.definition || def.text || JSON.stringify(def)
  }
  return String(def)
}

const calculateScore = (wordData) => {
  let score = 10 // Base score
  
  // Frequency bonus
  if (wordData.frequencyRank === 'rare') score += 5
  if (wordData.frequencyRank === 'very_rare') score += 10
  if (wordData.frequencyRank === 'uncommon') score += 3
  
  // Length bonus
  if (wordData.length > 6) score += wordData.length - 6
  
  // Sentiment bonus
  if (wordData.sentiment && wordData.sentiment > 0) score += Math.abs(wordData.sentiment)
  
  return score
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 