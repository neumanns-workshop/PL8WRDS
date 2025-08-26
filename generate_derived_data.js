#!/usr/bin/env node
/**
 * Generate Derived Data for PL8WRDS
 * Creates syllable counts and rhyme groups from pronunciation data
 */

import fs from 'fs';
import path from 'path';

class DerivedDataGenerator {
    constructor() {
        this.pronunciations = null;
        this.words = null;
    }

    async loadData() {
        console.log('Loading base data...');
        
        // Load words and pronunciations
        const wordsData = JSON.parse(fs.readFileSync('modular_data/words.json', 'utf8'));
        const pronData = JSON.parse(fs.readFileSync('modular_data/pronunciations.json', 'utf8'));
        
        this.words = wordsData.words;
        this.pronunciations = pronData.pronunciations;
        
        console.log(`Loaded ${this.words.length} words and ${Object.keys(this.pronunciations).length} pronunciations`);
    }

    /**
     * Count syllables from ARPAbet pronunciation
     */
    countSyllablesFromArpabet(arpabet) {
        if (!arpabet || arpabet.length === 0) return null;
        
        const phones = arpabet.split(' ');
        // ARPAbet vowel phonemes with stress markers (0, 1, 2)
        const vowelPhonemes = phones.filter(phone => 
            phone.match(/^(AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)[012]?$/)
        );
        return vowelPhonemes.length > 0 ? vowelPhonemes.length : null;
    }

    /**
     * Get rhyme ending from ARPAbet (primary rhyme = from stressed vowel to end)
     */
    getRhymeEnding(arpabet) {
        if (!arpabet) return null;
        
        const phones = arpabet.split(' ');
        let stressedIndex = -1;
        
        // Find the last stressed vowel (1 = primary stress)
        for (let i = phones.length - 1; i >= 0; i--) {
            if (phones[i].match(/^(AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)1$/)) {
                stressedIndex = i;
                break;
            }
        }
        
        // If no primary stress, find any stressed vowel
        if (stressedIndex === -1) {
            for (let i = phones.length - 1; i >= 0; i--) {
                if (phones[i].match(/^(AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)[12]$/)) {
                    stressedIndex = i;
                    break;
                }
            }
        }
        
        // If still no stress found, take the last vowel
        if (stressedIndex === -1) {
            for (let i = phones.length - 1; i >= 0; i--) {
                if (phones[i].match(/^(AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)[012]?$/)) {
                    stressedIndex = i;
                    break;
                }
            }
        }
        
        if (stressedIndex === -1) return null;
        
        const rhymeEnding = phones.slice(stressedIndex)
            .map(phone => phone.replace(/[012]$/, ''))
            .join(' ');
            
        // Filter out problematic American-only rhymes
        if (this.isProblematicRhyme(rhymeEnding)) {
            return null;
        }
        
        return rhymeEnding;
    }

    /**
     * Check if rhyme ending has British/American pronunciation conflicts
     */
    isProblematicRhyme(rhymeEnding) {
        // AH shouldn't rhyme with words ending in R or L in British English
        if (rhymeEnding.includes('AH') && (rhymeEnding.includes(' R') || rhymeEnding.includes(' L'))) {
            return true;
        }
        
        // AH at end shouldn't rhyme with words ending in R/L sounds
        if (rhymeEnding.endsWith('AH') && rhymeEnding.length > 2) {
            return true;
        }
        
        // ER endings are pronounced differently in British English
        if (rhymeEnding.includes('ER') && rhymeEnding.includes(' R')) {
            return true;
        }
        
        return false;
    }

    /**
     * Get final consonant ending for near-rhymes
     */
    getFinalEnding(arpabet) {
        if (!arpabet) return null;
        
        const phones = arpabet.split(' ');
        // Take last 2-3 phones for consonant endings
        return phones.slice(-2).map(phone => phone.replace(/[012]$/, '')).join(' ');
    }

    /**
     * Generate syllable counts for all words with pronunciations
     */
    generateSyllableCounts() {
        console.log('Generating syllable counts...');
        
        const syllableCounts = {};
        let processed = 0;
        let withCounts = 0;
        
        for (const word of this.words) {
            processed++;
            
            if (this.pronunciations[word]) {
                const arpabet = this.pronunciations[word].arpabet[0]; // Use first pronunciation
                const syllables = this.countSyllablesFromArpabet(arpabet);
                
                if (syllables !== null) {
                    syllableCounts[word] = {
                        syllables: syllables,
                        arpabet: arpabet,
                        source: 'arpabet_analysis'
                    };
                    withCounts++;
                }
            }
            
            if (processed % 10000 === 0) {
                console.log(`  Processed ${processed}/${this.words.length} words...`);
            }
        }
        
        console.log(`Generated syllable counts for ${withCounts} words`);
        return syllableCounts;
    }

    /**
     * Generate rhyme groups from pronunciations
     */
    generateRhymeGroups() {
        console.log('Generating rhyme groups...');
        
        const rhymeGroups = new Map();
        const nearRhymeGroups = new Map();
        
        let processed = 0;
        
        for (const word of this.words) {
            processed++;
            
            if (this.pronunciations[word]) {
                const arpabet = this.pronunciations[word].arpabet[0];
                
                // Perfect rhymes (from stressed vowel to end)
                const perfectRhyme = this.getRhymeEnding(arpabet);
                if (perfectRhyme && perfectRhyme.length > 1) { // At least 2 characters
                    const key = `perfect:${perfectRhyme}`;
                    if (!rhymeGroups.has(key)) {
                        rhymeGroups.set(key, []);
                    }
                    rhymeGroups.get(key).push(word);
                }
                
                // Near rhymes (final consonant patterns)
                const nearRhyme = this.getFinalEnding(arpabet);
                if (nearRhyme && nearRhyme.length > 1) {
                    const key = `near:${nearRhyme}`;
                    if (!nearRhymeGroups.has(key)) {
                        nearRhymeGroups.set(key, []);
                    }
                    nearRhymeGroups.get(key).push(word);
                }
            }
            
            if (processed % 10000 === 0) {
                console.log(`  Processed ${processed}/${this.words.length} words...`);
            }
        }
        
        // Filter groups to only include those with multiple words
        const filteredRhymes = new Map();
        for (const [key, words] of rhymeGroups) {
            if (words.length >= 2) { // At least 2 words to form a rhyme group
                filteredRhymes.set(key, words);
            }
        }
        
        for (const [key, words] of nearRhymeGroups) {
            if (words.length >= 3) { // Need more words for near rhymes
                filteredRhymes.set(key, words);
            }
        }
        
        console.log(`Generated ${filteredRhymes.size} rhyme groups`);
        
        // Convert Map to Object for JSON serialization
        const rhymeObject = {};
        for (const [key, words] of filteredRhymes) {
            rhymeObject[key] = words.sort(); // Sort words alphabetically
        }
        
        return rhymeObject;
    }

    /**
     * Generate word complexity scores
     */
    generateComplexityScores() {
        console.log('Generating complexity scores...');
        
        const complexityScores = {};
        let processed = 0;
        
        for (const word of this.words) {
            processed++;
            
            let complexity = 0;
            let factors = {};
            
            // Length factor (0-30 points)
            const lengthScore = Math.min(word.length * 2, 30);
            complexity += lengthScore;
            factors.length = lengthScore;
            
            // Syllable factor (if available)
            if (this.pronunciations[word]) {
                const arpabet = this.pronunciations[word].arpabet[0];
                const syllables = this.countSyllablesFromArpabet(arpabet);
                
                if (syllables !== null) {
                    const syllableScore = Math.min(syllables * 5, 25);
                    complexity += syllableScore;
                    factors.syllables = syllableScore;
                }
                
                // Pronunciation complexity (consonant clusters, etc.)
                const phones = arpabet.split(' ');
                const consonantClusters = this.countConsonantClusters(phones);
                const clusterScore = Math.min(consonantClusters * 3, 15);
                complexity += clusterScore;
                factors.clusters = clusterScore;
            }
            
            // Uncommon letters (Q, X, Z get bonus points)
            const uncommonLetters = (word.match(/[qxz]/gi) || []).length;
            const uncommonScore = uncommonLetters * 5;
            complexity += uncommonScore;
            if (uncommonScore > 0) factors.uncommon_letters = uncommonScore;
            
            complexityScores[word] = {
                total_score: Math.round(complexity),
                factors: factors,
                difficulty_level: this.getComplexityLevel(complexity)
            };
            
            if (processed % 10000 === 0) {
                console.log(`  Processed ${processed}/${this.words.length} words...`);
            }
        }
        
        console.log(`Generated complexity scores for ${Object.keys(complexityScores).length} words`);
        return complexityScores;
    }

    /**
     * Count consonant clusters in pronunciation
     */
    countConsonantClusters(phones) {
        let clusters = 0;
        let consonantRun = 0;
        
        for (const phone of phones) {
            // Check if it's a vowel phoneme (including stress markers)
            if (phone.match(/^(AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)[012]?$/)) {
                // Vowel - end consonant run
                if (consonantRun >= 2) {
                    clusters++;
                }
                consonantRun = 0;
            } else {
                // Consonant
                consonantRun++;
            }
        }
        
        // Check final consonant run
        if (consonantRun >= 2) {
            clusters++;
        }
        
        return clusters;
    }

    /**
     * Convert complexity score to difficulty level
     */
    getComplexityLevel(score) {
        if (score <= 15) return 'very_easy';
        if (score <= 25) return 'easy';
        if (score <= 40) return 'medium';
        if (score <= 60) return 'hard';
        return 'very_hard';
    }

    /**
     * Save data to JSON file with metadata
     */
    saveData(filename, data, description, additionalMetadata = {}) {
        const metadata = {
            created: new Date().toISOString(),
            total_words: this.words.length,
            entries_generated: Object.keys(data).length,
            coverage_percentage: ((Object.keys(data).length / this.words.length) * 100).toFixed(2),
            description: description,
            source_data: ['modular_data/words.json', 'modular_data/pronunciations.json'],
            ...additionalMetadata
        };

        const outputData = {
            metadata: metadata,
            [this.getDataKey(filename)]: data
        };

        const filepath = path.join('modular_data/derived', filename);
        fs.writeFileSync(filepath, JSON.stringify(outputData, null, 2));
        console.log(`Saved ${filepath} (${(fs.statSync(filepath).size / 1024 / 1024).toFixed(1)} MB)`);
    }

    /**
     * Get appropriate data key for filename
     */
    getDataKey(filename) {
        if (filename.includes('syllable')) return 'syllable_counts';
        if (filename.includes('rhyme')) return 'rhyme_groups';
        if (filename.includes('complexity')) return 'complexity_scores';
        return 'data';
    }

    /**
     * Generate all derived data
     */
    async generateAll() {
        console.log('=== GENERATING DERIVED DATA ===\n');
        
        await this.loadData();
        
        // Generate syllable counts
        const syllableCounts = this.generateSyllableCounts();
        this.saveData('syllable_counts.json', syllableCounts, 
            'Syllable counts derived from ARPAbet pronunciations',
            { 
                method: 'vowel_phoneme_count_from_arpabet',
                vowel_phonemes: 'AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW',
                stress_markers: '0,1,2'
            });
        
        // Generate rhyme groups
        const rhymeGroups = this.generateRhymeGroups();
        this.saveData('rhyme_groups.json', rhymeGroups,
            'Rhyme groups based on pronunciation patterns (American English ARPAbet)',
            {
                rhyme_types: ['perfect', 'near'],
                minimum_group_size: 2,
                perfect_rhyme_method: 'stressed_vowel_to_end',
                near_rhyme_method: 'final_consonant_pattern',
                british_american_filtering: 'excludes_problematic_AH_R_L_combinations',
                excluded_patterns: ['AH + R/L endings', 'ER + R combinations']
            });
        
        // Generate complexity scores
        const complexityScores = this.generateComplexityScores();
        this.saveData('complexity_scores.json', complexityScores,
            'Word complexity scores for difficulty assessment',
            {
                scoring_factors: ['length', 'syllables', 'consonant_clusters', 'uncommon_letters'],
                difficulty_levels: ['very_easy', 'easy', 'medium', 'hard', 'very_hard']
            });
        
        console.log('\n=== DERIVED DATA GENERATION COMPLETE ===');
        console.log('Generated files:');
        console.log('  - modular_data/derived/syllable_counts.json');
        console.log('  - modular_data/derived/rhyme_groups.json');
        console.log('  - modular_data/derived/complexity_scores.json');
    }
}

// Run the generator
if (import.meta.url === `file://${process.argv[1]}`) {
    const generator = new DerivedDataGenerator();
    generator.generateAll().catch(console.error);
}

export default DerivedDataGenerator; 