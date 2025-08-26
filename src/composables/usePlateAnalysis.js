import { ref, computed } from 'vue';

/**
 * Performs analysis on a list of solution words for a license plate.
 * @param {import('./data/DataManager').default} dataManager - An instance of the DataManager.
 */
export function usePlateAnalysis(dataManager) {
  const analysis = ref(null);
  const isLoading = ref(false);

  /**
   * Calculates the percentage of words in a given list that belong to various curated lists.
   * @param {string[]} solutionWords - An array of solution words for a plate.
   */
  async function calculateAnalysis(solutionWords) {
    if (!solutionWords || solutionWords.length === 0) {
      analysis.value = {};
      return;
    }

    isLoading.value = true;
    analysis.value = null;

    try {
      // Ensure the necessary data is loaded (lazy-loading)
      await dataManager.ensureDataLoaded('curatedMemberships');
      
      const listCounts = {};
      
      for (const word of solutionWords) {
        const memberships = dataManager.cache.curatedMemberships.get(word);
        if (memberships) {
          for (const listName in memberships) {
            // Only count boolean true flags for this analysis
            if (memberships[listName] === true) {
              listCounts[listName] = (listCounts[listName] || 0) + 1;
            }
          }
        }
      }

      const totalSolutions = solutionWords.length;
      const percentages = {};
      for (const listName in listCounts) {
        percentages[listName] = (listCounts[listName] / totalSolutions) * 100;
      }
      
      analysis.value = percentages;

    } catch (error) {
      console.error("Failed to calculate plate analysis:", error);
      analysis.value = { error: "Could not perform analysis." };
    } finally {
      isLoading.value = false;
    }
  }

  const formattedAnalysis = computed(() => {
    if (!analysis.value || analysis.value.error) {
      return [];
    }
    return Object.entries(analysis.value)
      .map(([name, percentage]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        percentage: percentage.toFixed(1) + '%',
      }))
      .sort((a, b) => parseFloat(b.percentage) - parseFloat(a.percentage));
  });

  return {
    formattedAnalysis,
    isLoadingAnalysis: isLoading,
    calculateAnalysis,
  };
} 