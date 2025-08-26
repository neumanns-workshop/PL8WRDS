import { computed } from 'vue';

/**
 * Generates a unique, deterministic color scheme based on a 3-character license plate ID.
 * @param {import('vue').ComputedRef<string>} plateId - A computed ref containing the 3-character plate ID (e.g., "PLW").
 */
export function usePlateColors(plateId) {
  const colorScheme = computed(() => {
    const id = plateId.value.toUpperCase().slice(0, 3);
    if (id.length !== 3 || !/^[A-Z]+$/.test(id)) {
      // Return default colors if the ID is invalid
      return {
        headerBg: 'hsl(210, 15%, 20%)', // Dark blue-gray
        plateBg: 'hsl(210, 20%, 95%)', // Very light off-white
        mainText: 'hsl(210, 15%, 20%)',
        headerText: 'hsl(210, 20%, 95%)',
        hole: 'hsl(210, 10%, 85%)',
        holeBorder: 'hsl(210, 10%, 40%)',
      };
    }

    const l1 = id.charCodeAt(0) - 65; // A=0, B=1...
    const l2 = id.charCodeAt(1) - 65;
    const l3 = id.charCodeAt(2) - 65;

    // Create a unique numeric seed from the 3 letters (0 to 17575)
    const seed = l1 * 676 + l2 * 26 + l3;

    // Generate a hue from the seed, spanning the entire color wheel
    const hue = Math.floor((seed / 17576) * 360);
    
    // Use the first letter to add some variation to saturation
    const saturation = 65 + (l1 % 6) * 3; // 65% to 80%

    return {
      headerBg: `hsl(${hue}, ${saturation}%, 25%)`,
      plateBg: `hsl(${hue}, ${saturation}%, 90%)`,
      mainText: `hsl(${hue}, ${saturation}%, 20%)`,
      headerText: `hsl(${hue}, ${saturation}%, 92%)`,
      hue: hue,
    };
  });

  return { colorScheme };
} 