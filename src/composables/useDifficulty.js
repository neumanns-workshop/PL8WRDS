import { computed } from 'vue';

const DIFFICULTY_LEVELS = ['Easy', 'Medium', 'Hard', 'Genius'];

/**
 * Generates a deterministic, mock difficulty level based on a 3-character license plate ID.
 * @param {import('vue').Ref<string>} plateLetters - A ref containing the 3-character plate ID (e.g., "PLW").
 */
export function useDifficulty(plateLetters) {
  const difficulty = computed(() => {
    const id = plateLetters.value.toUpperCase();
    if (id.length !== 3 || !/^[A-Z]+$/.test(id)) {
      return 'Unranked';
    }

    // Placeholder logic: generate a "difficulty" from the letters' char codes.
    // This provides a deterministic but mock value for now.
    const charCodeSum = id.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
    const index = charCodeSum % DIFFICULTY_LEVELS.length;

    return DIFFICULTY_LEVELS[index];
  });

  return { difficulty };
} 