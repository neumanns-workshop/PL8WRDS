<template>
  <div v-if="show" @click.self="close" class="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4 transition-opacity duration-300">
    <div class="bg-dark-surface rounded-lg shadow-mobile-lg w-full max-w-md p-6 animate-bounce-in border border-dark-border">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-2xl font-display font-bold text-dark-text">Plate Analysis</h2>
        <button @click="close" class="text-gray-400 hover:text-white text-3xl leading-none">&times;</button>
      </div>
      <div v-if="analysis.length > 0" class="max-h-80 overflow-y-auto pr-2">
        <ul class="space-y-2">
          <li v-for="item in analysis" :key="item.name" class="flex justify-between items-center bg-gray-800 p-3 rounded-md">
            <span class="font-semibold text-dark-text">{{ item.name }}</span>
            <span class="font-mono text-game-correct font-bold">{{ item.percentage }}</span>
          </li>
        </ul>
      </div>
      <div v-else class="text-gray-400 text-center py-8">
        <p>No special list memberships found for this plate's solutions.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  show: Boolean,
  analysis: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['close']);

const close = () => {
  emit('close');
};
</script>

<style scoped>
/* Custom scrollbar for webkit browsers */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: #1e293b; /* dark-surface */
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: #4a5568;
  border-radius: 4px;
  border: 2px solid #1e293b;
}
</style> 