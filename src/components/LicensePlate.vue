<template>
  <div class="w-full max-w-sm mx-auto animate-bounce-in">
    <div
      class="bg-plate-background rounded-lg shadow-mobile-lg overflow-hidden font-plate border-2 relative sparkle-texture"
      :style="plateStyle"
    >
      <!-- Mounting Holes -->
      <div class="absolute top-3 left-3 w-3 h-2.5 rounded-full mounting-hole"></div>
      <div class="absolute top-3 right-3 w-3 h-2.5 rounded-full mounting-hole"></div>
      <div class="absolute bottom-3 left-3 w-3 h-2.5 rounded-full mounting-hole"></div>
      <div class="absolute bottom-3 right-3 w-3 h-2.5 rounded-full mounting-hole"></div>

      <div class="text-white text-center py-2" :style="{ backgroundColor: colorScheme.headerBg }">
        <p class="text-sm font-bold tracking-widest deboss-text-dark-bg" :style="{ color: colorScheme.headerText }">{{ headerText }}</p>
      </div>
      <div class="p-6 flex items-center justify-center">
        <span class="text-6xl font-extrabold tracking-wider emboss-text" :style="{ color: colorScheme.mainText }">
          <span>{{ letters }}</span>
          <span v-if="score" class="ml-4">{{ score }}</span>
        </span>
      </div>
      <div class="text-center pb-2">
        <p v-if="difficulty" class="text-xs font-semibold deboss-text-light-bg" :style="{ color: colorScheme.mainText }">
          {{ difficulty }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { usePlateColors } from '../composables/usePlateColors.js';

const props = defineProps({
  plateText: {
    type: String,
    default: 'PL8 WRDS',
  },
  difficulty: {
    type: String,
    default: '',
  },
  headerText: {
    type: String,
    default: 'YOUR STATE',
  }
});

const letters = computed(() => props.plateText.split(' ')[0] || '');
const score = computed(() => {
  const parts = props.plateText.split(' ');
  return parts.length > 1 ? parts[1] : '';
});

const plateId = computed(() => letters.value.replace(/[^A-Z0-9]/g, '').substring(0, 3));
const { colorScheme } = usePlateColors(plateId);

const plateStyle = computed(() => ({
  '--plate-gradient': `linear-gradient(to bottom, ${colorScheme.value.plateBg}, hsl(${colorScheme.value.hue}, 40%, 88%))`,
  borderColor: colorScheme.value.headerBg,
}));
</script>

<style scoped>
.sparkle-texture {
  background-image: 
    url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><filter id="s"><feTurbulence type="fractalNoise" baseFrequency="2.5" numOctaves="1" stitchTiles="stitch"/><feComponentTransfer><feFuncA type="discrete" tableValues="0 1"/></feComponentTransfer></filter><rect width="100%" height="100%" filter="url(%23s)" opacity=".18"/></svg>'),
    var(--plate-gradient);
  background-blend-mode: multiply;
  position: relative;
  z-index: 1;
}

.emboss-text {
  text-shadow: 
    -1px -1px 1px rgba(255, 255, 255, 0.8),
    1px 1px 2px rgba(0, 0, 0, 0.4);
}

.deboss-text-dark-bg {
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
}

.deboss-text-light-bg {
  text-shadow: 1px 1px 1px rgba(255, 255, 255, 0.9);
}

.mounting-hole {
  background: var(--app-bg-color); /* Use the global variable */
  box-shadow: 
    inset 1px 1px 1px rgba(0, 0, 0, 0.5), /* Dark inner shadow for depth */
    inset -1px -1px 1px rgba(255, 255, 255, 0.2); /* Light inner highlight */
}
</style> 