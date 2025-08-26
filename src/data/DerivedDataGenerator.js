/**
 * DerivedDataGenerator - Generate rhyming groups and syllable counts
 * Processes ARPAbet pronunciation data to create derived linguistic features
 */

import { promises as fs } from 'fs';
import path from 'path';

class DerivedDataGenerator {
    constructor() {
        this.pronunciations = null;
        this.words = null;
        this.results = {
            rhymeGroups: new Map(),      // rhyme_key -> [words]
            syllableCounts: new Map()    // word -> syllable_count
        };
    }

    /**
     * Initialize by loading source data
     */
    async initialize() {
        console.log('🔊 Loading pronunciation data...');
        const pronData = await this.loadJSON('modular_data/pronunciations.json');
        this.pronunciations = pronData.pronunciations;
        
        console.log('📚 Loading word list...');
        const wordData = await this.loadJSON('modular_data/words.json');
        this.words = wordData.words;
        
        console.log(`✅ Loaded ${Object.keys(this.pronunciations).length.toLocaleString()} pronunciations`);
        console.log(`✅ Loaded ${this.words.length.toLocaleString()} words`);
    }

    /**
     * Generate all derived data
     */
    async generateAll() {
        console.log('\n🎵 Generating rhyming groups and syllable counts...\n');
        
        const startTime = performance.now();
        let processedCount = 0;
        
        for (const [word, pronData] of Object.entries(this.pronunciations)) {
            if (!pronData.arpabet || !Array.isArray(pronData.arpabet)) continue;
            
            // Use the first pronunciation variant
            const arpabet = pronData.arpabet[0];
            
            // Generate syllable count
            const syllableCount = this.extractSyllableCount(arpabet, pronData.ipa);
            this.results.syllableCounts.set(word, syllableCount);
            
            // Generate rhyme keys
            const rhymeKeys = this.extractRhymeKeys(arpabet);
            for (const rhymeKey of rhymeKeys) {
                if (!this.results.rhymeGroups.has(rhymeKey)) {
                    this.results.rhymeGroups.set(rhymeKey, []);
                }
                this.results.rhymeGroups.get(rhymeKey).push(word);
            }
            
            // Note: Removed phonetic patterns - focus on syllables + rhymes only
            
            processedCount++;
            
            if (processedCount % 5000 === 0) {
                const elapsed = performance.now() - startTime;
                const rate = processedCount / (elapsed / 1000);
                console.log(`📊 Processed ${processedCount.toLocaleString()} words (${rate.toFixed(0)} words/sec)`);
            }
        }
        
        const totalTime = performance.now() - startTime;
        console.log(`\n✅ Generated derived data in ${(totalTime / 1000).toFixed(2)}s`);
        
        // Filter and analyze results
        this.analyzeResults();
    }

    /**
     * Extract syllable count from pronunciation data
     */
    extractSyllableCount(arpabet, ipaData = null) {
        // First try counting stress markers (0, 1, 2) from ARPAbet - most accurate method
        const stressMarkers = arpabet.match(/[012]/g);
        if (stressMarkers && stressMarkers.length > 0) {
            return stressMarkers.length;
        }
        
        // Fallback 1: Try IPA if available
        if (ipaData && Array.isArray(ipaData) && ipaData.length > 0) {
            const syllableCount = this.extractSyllableCountFromIPA(ipaData[0]);
            if (syllableCount > 0) {
                return syllableCount;
            }
        }
        
        // Fallback 2: Count vowel phonemes in ARPAbet when no stress markers
        // ARPAbet vowels: AA, AE, AH, AO, AW, AY, EH, ER, EY, IH, IY, OW, OY, UH, UW
        const vowelPhonemes = arpabet.match(/\b(AA|AE|AH|AO|AW|AY|EH|ER|EY|IH|IY|OW|OY|UH|UW)\b/g);
        return vowelPhonemes ? vowelPhonemes.length : 0;
    }

    /**
     * Extract syllable count from IPA pronunciation
     */
    extractSyllableCountFromIPA(ipaString) {
        // Clean the IPA string - remove metadata and brackets
        let cleanIPA = ipaString.replace(/\|.*$/, '').replace(/[\/\[\]]/g, '');
        
        // Count vowel nuclei (syllable centers) in IPA
        // Each vowel or diphthong represents a syllable nucleus
        // IPA vowels: a, e, i, o, u, ə, ɪ, ʊ, ɛ, ɔ, æ, ʌ, ɑ
        // IPA diphthongs: eɪ, aɪ, ɔɪ, aʊ, oʊ, etc.
        
        // First handle diphthongs (must come before single vowels)
        const diphthongs = cleanIPA.match(/eɪ|aɪ|ɔɪ|aʊ|oʊ|əʊ|ɪə|eə|ʊə/g) || [];
        
        // Remove diphthongs from string to avoid double counting
        let remainingIPA = cleanIPA;
        diphthongs.forEach(diphthong => {
            remainingIPA = remainingIPA.replace(diphthong, 'X'); // placeholder
        });
        
        // Count remaining single vowels
        const singleVowels = remainingIPA.match(/[aeiouəɪʊɛɔæʌɑɒʉɨɘɤɯɶɞɜɐɚɝ]/g) || [];
        
        const totalSyllables = diphthongs.length + singleVowels.length;
        return totalSyllables > 0 ? totalSyllables : 0;
    }

    /**
     * Extract rhyme keys from ARPAbet pronunciation
     * Generates focused rhyme keys for meaningful rhyming relationships
     */
    extractRhymeKeys(arpabet) {
        const phones = arpabet.split(' ');
        const rhymeKeys = [];
        
        // Find the last stressed vowel and everything after it
        let lastStressedIndex = -1;
        for (let i = phones.length - 1; i >= 0; i--) {
            if (phones[i].match(/[12]$/)) {  // Only primary (1) and secondary (2) stress
                lastStressedIndex = i;
                break;
            }
        }
        
        // If no stressed vowel found, try to find any vowel in the last part
        if (lastStressedIndex === -1) {
            for (let i = phones.length - 1; i >= Math.max(0, phones.length - 3); i--) {
                if (phones[i].match(/[AEIOU]/)) {
                    lastStressedIndex = i;
                    break;
                }
            }
        }
        
        if (lastStressedIndex === -1) return rhymeKeys;
        
        // Perfect rhyme: from last stressed vowel to end (minimum 2 phonemes)
        const perfectRhymePhones = phones.slice(lastStressedIndex);
        if (perfectRhymePhones.length >= 2) {
            const perfectRhyme = perfectRhymePhones.join(' ');
            rhymeKeys.push(`perfect:${perfectRhyme}`);
        }
        
        // Near rhyme: last 2-3 phonemes (only if meaningful)
        if (phones.length >= 3) {
            const nearRhyme = phones.slice(-2).join(' ');
            // Only include if it has substance (not just single consonants)
            if (nearRhyme.match(/[AEIOU]/) || nearRhyme.split(' ').length >= 2) {
                rhymeKeys.push(`near:${nearRhyme}`);
            }
        }
        
        // Suffix rhyme: common word endings (more selective)
        const lastThree = phones.slice(-3).join(' ');
        const lastTwo = phones.slice(-2).join(' ');
        
        // Only include common, meaningful endings
        const meaningfulEndings = [
            // Common suffixes that create good rhymes
            'IH NG', 'EH R', 'AH R', 'EY SH AH N', 'SH AH N', 'T IH V',
            'AE T', 'EH T', 'IH T', 'UH T', 'AY T', 'OW T', 'AW T',
            'AH L', 'EH L', 'IH L', 'UH L', 'AY L', 'OW L', 'AW L',
            'AH N', 'EH N', 'IH N', 'UH N', 'AY N', 'OW N', 'AW N',
            'AH S', 'EH S', 'IH S', 'UH S', 'AY S', 'OW S', 'AW S',
            'AH Z', 'EH Z', 'IH Z', 'UH Z', 'AY Z', 'OW Z', 'AW Z'
        ];
        
        if (meaningfulEndings.includes(lastTwo)) {
            rhymeKeys.push(`suffix:${lastTwo}`);
        } else if (meaningfulEndings.includes(lastThree)) {
            rhymeKeys.push(`suffix:${lastThree}`);
        }
        
        return rhymeKeys;
    }

    // Removed phonetic complexity analysis methods - keeping it simple!

    /**
     * Analyze and filter results
     */
    analyzeResults() {
        console.log('\n📊 Analyzing derived data results:\n');
        
        // Syllable count distribution
        const syllableDistribution = {};
        for (const count of this.results.syllableCounts.values()) {
            syllableDistribution[count] = (syllableDistribution[count] || 0) + 1;
        }
        
        console.log('🔢 Syllable Count Distribution:');
        Object.keys(syllableDistribution)
            .sort((a, b) => parseInt(a) - parseInt(b))
            .forEach(syllables => {
                const count = syllableDistribution[syllables];
                const pct = ((count / this.results.syllableCounts.size) * 100).toFixed(1);
                console.log(`  ${syllables} syllables: ${count.toLocaleString()} words (${pct}%)`);
            });
        
        // Rhyme group analysis
        const rhymeGroupSizes = {};
        let totalRhymeGroups = 0;
        let perfectRhymeGroups = 0;
        
        for (const [rhymeKey, words] of this.results.rhymeGroups.entries()) {
            const groupSize = words.length;
            if (groupSize >= 2) {  // Only count groups with 2+ words
                rhymeGroupSizes[groupSize] = (rhymeGroupSizes[groupSize] || 0) + 1;
                totalRhymeGroups++;
                
                if (rhymeKey.startsWith('perfect:')) {
                    perfectRhymeGroups++;
                }
            }
        }
        
        console.log('\n🎵 Rhyme Group Analysis:');
        console.log(`  Total rhyme groups (2+ words): ${totalRhymeGroups.toLocaleString()}`);
        console.log(`  Perfect rhyme groups: ${perfectRhymeGroups.toLocaleString()}`);
        
        console.log('\n  Rhyme group sizes:');
        Object.keys(rhymeGroupSizes)
            .sort((a, b) => parseInt(b) - parseInt(a))
            .slice(0, 10)
            .forEach(size => {
                const count = rhymeGroupSizes[size];
                console.log(`    ${size} words: ${count} groups`);
            });
        
        // Show some example rhyme groups
        console.log('\n🎯 Example Perfect Rhyme Groups:');
        let exampleCount = 0;
        for (const [rhymeKey, words] of this.results.rhymeGroups.entries()) {
            if (rhymeKey.startsWith('perfect:') && words.length >= 3 && words.length <= 8) {
                console.log(`  ${rhymeKey.replace('perfect:', '')}: ${words.slice(0, 6).join(', ')}${words.length > 6 ? '...' : ''}`);
                exampleCount++;
                if (exampleCount >= 5) break;
            }
        }
        
        console.log('\n✅ Focused on essential features: syllables and rhymes only');
    }

    /**
     * Save derived data to files
     */
    async saveResults(outputDir = 'modular_data/derived') {
        await fs.mkdir(outputDir, { recursive: true });
        
        console.log('\n💾 Saving derived data...');
        
        // Convert Maps to Objects for JSON serialization
        const rhymeGroupsObj = {};
        for (const [key, words] of this.results.rhymeGroups.entries()) {
            if (words.length >= 2) {  // Only save groups with 2+ words
                rhymeGroupsObj[key] = words.sort();
            }
        }
        
        const syllableCountsObj = {};
        for (const [word, count] of this.results.syllableCounts.entries()) {
            syllableCountsObj[word] = count;
        }
        
        // Removed phonetic patterns - keeping only essential data
        
        // Save rhyme groups
        const rhymeData = {
            metadata: {
                created_at: new Date().toISOString(),
                source: 'ARPAbet pronunciations from modular_data/pronunciations.json',
                total_rhyme_groups: Object.keys(rhymeGroupsObj).length,
                rhyme_types: ['perfect', 'near', 'suffix'],
                description: 'Rhyming word groups generated from phonetic analysis'
            },
            rhyme_groups: rhymeGroupsObj
        };
        
        await fs.writeFile(
            path.join(outputDir, 'rhyme_groups.json'),
            JSON.stringify(rhymeData, null, 2)
        );
        
        // Save syllable counts
        const syllableData = {
            metadata: {
                created_at: new Date().toISOString(),
                source: 'ARPAbet pronunciations from modular_data/pronunciations.json',
                total_words: Object.keys(syllableCountsObj).length,
                method: 'Stress marker counting from ARPAbet',
                description: 'Accurate syllable counts derived from pronunciation data'
            },
            syllable_counts: syllableCountsObj
        };
        
        await fs.writeFile(
            path.join(outputDir, 'syllable_counts.json'),
            JSON.stringify(syllableData, null, 2)
        );
        
        console.log(`✅ Saved rhyme groups: ${Object.keys(rhymeGroupsObj).length.toLocaleString()} groups`);
        console.log(`✅ Saved syllable counts: ${Object.keys(syllableCountsObj).length.toLocaleString()} words`);
        console.log(`📁 Output directory: ${outputDir}`);
    }

    /**
     * Load JSON file (works in both Node.js and browser)
     */
    async loadJSON(filePath) {
        try {
            // Node.js environment
            const data = await fs.readFile(filePath, 'utf8');
            return JSON.parse(data);
        } catch (error) {
            // Browser environment fallback
            const response = await fetch(filePath);
            return await response.json();
        }
    }
}

export default DerivedDataGenerator; 