/**
 * LicensePlateSolver - Finds all valid words for a given 3-letter plate.
 */
export default class LicensePlateSolver {
    /**
     * Checks if a word is a valid solution for the given plate letters.
     * The letters must appear in the word in the correct order, but not necessarily consecutively.
     * @param {string} plateLetters - The 3 letters from the license plate (e.g., "PLW").
     * @param {string} word - The word to check.
     * @returns {boolean} - True if the word is a valid solution.
     */
    isValidSolution(plateLetters, word) {
        const plateUpper = plateLetters.toUpperCase();
        const wordUpper = word.toUpperCase();

        let plateIndex = 0;
        let wordIndex = 0;

        while (wordIndex < wordUpper.length && plateIndex < plateUpper.length) {
            if (wordUpper[wordIndex] === plateUpper[plateIndex]) {
                plateIndex++;
            }
            wordIndex++;
        }

        return plateIndex === plateUpper.length;
    }

    /**
     * Finds all valid solutions for a plate from a given list of words.
     * @param {string} plateLetters - The 3 letters from the license plate.
     * @param {string[]} wordlist - An array of all possible words to check against.
     * @returns {string[]} - An array of all valid words found.
     */
    findAllSolutions(plateLetters, wordlist) {
        if (!plateLetters || plateLetters.length !== 3 || !wordlist) {
            return [];
        }

        const solutions = [];
        for (const word of wordlist) {
            if (this.isValidSolution(plateLetters, word)) {
                solutions.push(word);
            }
        }
        return solutions;
    }
} 