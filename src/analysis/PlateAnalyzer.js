/**
 * PlateAnalyzer - Optimized license plate analysis for PL8WRDS
 * High-performance word finding with configurable options
 */

import DataManager from '../data/DataManager.js';
import LicensePlateSolver from '../game/LicensePlateSolver.js';

class PlateAnalyzer {
    constructor(options = {}) {
        this.dataManager = null;
        this.solver = null;
        
        // Configuration
        this.config = {
            minWordLength: options.minWordLength || 2,
            maxWordLength: options.maxWordLength || 20,
            useFrequencyScoring: options.useFrequencyScoring || false,
            useCuratedLists: options.useCuratedLists || false,
            maxResultsPerPlate: options.maxResultsPerPlate || 50000,
            enableProgress: options.enableProgress !== false,
            progressInterval: options.progressInterval || 1000,
            ...options
        };
        
        // Results storage
        this.results = {
            statistics: {},
            plateSolutions: {},
            difficultyLevels: {
                easy: [],    // 7000+ solutions
                medium: [],  // 1000-6999 solutions  
                hard: [],    // 1-999 solutions
                impossible: [] // 0 solutions
            }
        };
    }

    /**
     * Initialize the analyzer
     */
    async initialize() {
        const initStart = performance.now();
        
        this.dataManager = new DataManager();
        await this.dataManager.initialize();
        
        this.solver = new LicensePlateSolver(this.dataManager);
        
        const initTime = performance.now() - initStart;
        
        if (this.config.enableProgress) {
            console.log(`✅ PlateAnalyzer initialized in ${initTime.toFixed(2)}ms`);
            console.log(`📚 Loaded ${this.dataManager.getWords().length.toLocaleString()} words`);
        }
        
        return initTime;
    }

    /**
     * Generate all possible 3-letter license plates (AAA-ZZZ)
     */
    generateAllPlates() {
        const plates = [];
        for (let i = 0; i < 26; i++) {
            for (let j = 0; j < 26; j++) {
                for (let k = 0; k < 26; k++) {
                    plates.push(
                        String.fromCharCode(65 + i) + 
                        String.fromCharCode(65 + j) + 
                        String.fromCharCode(65 + k)
                    );
                }
            }
        }
        return plates; // 17,576 total
    }

    /**
     * Analyze multiple plates with comprehensive linguistic analysis
     */
    async analyzeAll(plates = null) {
        const platesToAnalyze = plates || this.generateAllPlates();
        
        if (this.config.enableProgress) {
            console.log(`🚀 Starting comprehensive analysis of ${platesToAnalyze.length.toLocaleString()} plates\n`);
        }
        
        const startTime = performance.now();
        
        // Analysis variables
        let processed = 0;
        let totalSolutions = 0;
        let maxSolutions = 0;
        let minSolutions = Infinity;
        let unsolvableCount = 0;
        const solutionDistribution = {};
        
        // Rich linguistic analysis variables
        const frequencyAnalysis = {
            veryHighFreq: 0,  // Top 10% (>3.33)
            highFreq: 0,      // 75-90th percentile (0.75-3.33)
            mediumFreq: 0,    // 50-75th percentile (0.16-0.75)
            lowFreq: 0,       // 25-50th percentile (0.04-0.16)
            veryLowFreq: 0,   // Bottom 25% (<0.04)
            unknownFreq: 0    // No frequency data
        };
        
        const curatedListAnalysis = {
            ogden: { total: 0, plates: 0 },
            afinn: { positive: 0, negative: 0, neutral: 0, plates: 0 },
            swadesh: { total: 0, plates: 0 },
            stop: { total: 0, plates: 0 }
        };
        
        const lengthDistribution = {};
        const difficultyScores = [];
        const phoneticAnalysis = {
            withPronunciation: 0,
            withoutPronunciation: 0
        };
        
        // Process each plate
        for (const plate of platesToAnalyze) {
            const result = await this.solver.solve(plate, {
                minLength: this.config.minWordLength,
                maxLength: this.config.maxWordLength,
                useFrequencyScoring: this.config.useFrequencyScoring,
                useCuratedLists: this.config.useCuratedLists,
                maxResults: this.config.maxResultsPerPlate
            });
            
            const solutionCount = result.totalWords;
            const words = result.words.map(w => w.word);
            
            // Store results
            this.results.plateSolutions[plate] = words;
            
            // Basic statistics
            totalSolutions += solutionCount;
            maxSolutions = Math.max(maxSolutions, solutionCount);
            solutionDistribution[solutionCount] = (solutionDistribution[solutionCount] || 0) + 1;
            
            if (solutionCount === 0) {
                unsolvableCount++;
            } else {
                minSolutions = Math.min(minSolutions, solutionCount);
            }
            
                    // Collect words for later unique analysis
        if (words.length > 0) {
            // Calculate sophisticated difficulty score
            const difficultyScore = await this.calculateDifficultyScore(plate, words);
            difficultyScores.push({ plate, score: difficultyScore, solutionCount });
        }
            
            processed++;
            
            // Progress reporting
            if (this.config.enableProgress && processed % this.config.progressInterval === 0) {
                const elapsed = performance.now() - startTime;
                const rate = processed / (elapsed / 1000);
                const eta = ((platesToAnalyze.length - processed) / rate / 60).toFixed(1);
                const progress = (processed / platesToAnalyze.length * 100).toFixed(1);
                
                console.log(`📊 Progress: ${progress}% (${processed.toLocaleString()}/${platesToAnalyze.length.toLocaleString()}) | ${rate.toFixed(1)} plates/sec | ETA: ${eta}min`);
            }
        }
        
        const endTime = performance.now();
        const totalTime = endTime - startTime;
        const avgTimePerPlate = totalTime / platesToAnalyze.length;
        
        // Analyze all unique words for linguistic features
        console.log('🔬 Analyzing linguistic features of unique words...');
        const allWords = Object.values(this.results.plateSolutions).flat();
        const uniqueWords = [...new Set(allWords)];
        console.log(`📚 Found ${uniqueWords.length.toLocaleString()} unique words from ${allWords.length.toLocaleString()} total solutions`);
        
        await this.analyzeUniqueWords(uniqueWords, frequencyAnalysis, curatedListAnalysis, lengthDistribution, phoneticAnalysis);
        
        // Calculate sophisticated difficulty levels based on actual distribution
        const validScores = difficultyScores.filter(item => !isNaN(item.score));
        const sortedScores = validScores.sort((a, b) => a.score - b.score);
        const difficultyLevels = this.categorizeDifficulty(sortedScores, unsolvableCount);
        
        // Compile comprehensive statistics
        this.results.statistics = {
            basic_stats: {
                total_plates: platesToAnalyze.length,
                total_words: this.dataManager.getWords().length,
                avg_solutions_per_plate: totalSolutions / platesToAnalyze.length,
                max_solutions: maxSolutions,
                min_solutions: minSolutions === Infinity ? 0 : minSolutions,
                unsolvable_count: unsolvableCount,
                solution_distribution: solutionDistribution
            },
            frequency_analysis: {
                ...frequencyAnalysis,
                total_analyzed: Object.values(frequencyAnalysis).reduce((a, b) => a + b, 0),
                very_high_freq_percentage: (frequencyAnalysis.veryHighFreq / Object.values(frequencyAnalysis).reduce((a, b) => a + b, 0) * 100).toFixed(1)
            },
            curated_lists: curatedListAnalysis,
            phonetic_coverage: {
                ...phoneticAnalysis,
                coverage_percentage: (phoneticAnalysis.withPronunciation / (phoneticAnalysis.withPronunciation + phoneticAnalysis.withoutPronunciation) * 100).toFixed(1)
            },
            length_distribution: lengthDistribution,
            difficulty_distribution: {
                score_statistics: {
                    mean: sortedScores.length > 0 ? sortedScores.reduce((sum, item) => sum + item.score, 0) / sortedScores.length : 0,
                    median: sortedScores.length > 0 ? sortedScores[Math.floor(sortedScores.length / 2)]?.score || 0 : 0,
                    std_dev: sortedScores.length > 0 ? this.calculateStandardDeviation(sortedScores.map(item => item.score)) : 0
                },
                levels: difficultyLevels
            },
            processing_stats: {
                total_time_ms: totalTime,
                avg_time_per_plate_ms: avgTimePerPlate,
                plates_per_second: 1000 / avgTimePerPlate
            }
        };
        
        this.results.difficultyLevels = difficultyLevels;
        
        if (this.config.enableProgress) {
            console.log(`\n✅ Comprehensive analysis complete! Processed ${platesToAnalyze.length.toLocaleString()} plates in ${(totalTime / 1000).toFixed(1)}s\n`);
        }
        
        return this.results;
    }
    
    /**
     * Analyze unique words for linguistic features 
     */
    async analyzeUniqueWords(uniqueWords, frequencyAnalysis, curatedListAnalysis, lengthDistribution, phoneticAnalysis) {
        // Load additional data on demand
        await this.dataManager.ensureDataLoaded('frequencies');
        await this.dataManager.ensureDataLoaded('curatedMemberships');
        await this.dataManager.ensureDataLoaded('pronunciations');
        
        for (const word of uniqueWords) {
            // Frequency analysis - using actual statistical thresholds
            const freqData = await this.dataManager.getFrequency(word);
            if (freqData && freqData.frequency && freqData.frequency > 0) {
                const freq = freqData.frequency;
                if (freq > 3.33) frequencyAnalysis.veryHighFreq++;          // Top 10%
                else if (freq >= 0.75) frequencyAnalysis.highFreq++;        // 75-90th percentile
                else if (freq >= 0.16) frequencyAnalysis.mediumFreq++;      // 50-75th percentile
                else if (freq >= 0.04) frequencyAnalysis.lowFreq++;         // 25-50th percentile
                else frequencyAnalysis.veryLowFreq++;                       // Bottom 25%
            } else {
                frequencyAnalysis.unknownFreq++;
            }
            
            // Length distribution
            const length = word.length;
            lengthDistribution[length] = (lengthDistribution[length] || 0) + 1;
            
            // Curated list analysis
            const membership = await this.dataManager.getCuratedMemberships(word);
            if (membership) {
                // OGDEN analysis - check all OGDEN categories  
                if (membership.ogden_basic_action || membership.ogden_basic_concept || membership.ogden_basic_concrete || 
                    membership.ogden_basic_contrast || membership.ogden_basic_quality || membership.ogden_field_body || 
                    membership.ogden_field_food || membership.ogden_field_home || membership.ogden_field_animal || 
                    membership.ogden_field_color || membership.ogden_field_time) {
                    curatedListAnalysis.ogden.total++;
                }
                
                // AFINN sentiment analysis - fix: check actual AFINN fields
                const afinnFields = Object.keys(membership).filter(key => key.startsWith('afinn_'));
                if (afinnFields.length > 0) {
                    if (membership.afinn_score !== undefined) {
                        const score = membership.afinn_score;
                        if (score > 0) curatedListAnalysis.afinn.positive++;
                        else if (score < 0) curatedListAnalysis.afinn.negative++;
                        else curatedListAnalysis.afinn.neutral++;
                    } else {
                        // Handle specific AFINN fields
                        const hasPositive = afinnFields.some(field => field.includes('pos_'));
                        const hasNegative = afinnFields.some(field => field.includes('neg_'));
                        const hasNeutral = afinnFields.some(field => field.includes('neutral'));
                        
                        if (hasPositive) curatedListAnalysis.afinn.positive++;
                        else if (hasNegative) curatedListAnalysis.afinn.negative++;
                        else if (hasNeutral) curatedListAnalysis.afinn.neutral++;
                    }
                }
                
                // SWADESH analysis
                if (membership.swadesh_core || membership.swadesh_extended) {
                    curatedListAnalysis.swadesh.total++;
                }
                
                // STOP words analysis
                if (membership.stop_nltk || membership.stop_spacy || membership.stop_fox || membership.stop_learn) {
                    curatedListAnalysis.stop.total++;
                }
                
                // ROGET analysis - add missing categories
                const rogetFields = Object.keys(membership).filter(key => key.startsWith('roget_'));
                if (rogetFields.length > 0) {
                    if (!curatedListAnalysis.roget) curatedListAnalysis.roget = { total: 0 };
                    curatedListAnalysis.roget.total++;
                }
            }
            
            // Phonetic analysis
            const pronunciation = await this.dataManager.getPronunciation(word);
            if (pronunciation) {
                phoneticAnalysis.withPronunciation++;
            } else {
                phoneticAnalysis.withoutPronunciation++;
            }
        }
    }
    
    /**
     * Calculate sophisticated difficulty score based on linguistic features
     */
    async calculateDifficultyScore(plate, words) {
        if (words.length === 0) return 100; // Impossible
        
        let score = 0;
        let totalWeight = 0;
        
        // Base score from solution count (inverted - fewer solutions = harder)
        const solutionCountScore = Math.max(0, 100 - Math.log10(words.length + 1) * 20);
        score += solutionCountScore * 0.4;
        totalWeight += 0.4;
        
        // Average word frequency (higher frequency = easier)
        let avgFrequency = 0;
        let freqCount = 0;
        for (const word of words.slice(0, 10)) { // Sample first 10 words for performance
            const freqData = await this.dataManager.getFrequency(word);
            if (freqData && freqData.frequency && freqData.frequency > 0) { // Only count positive frequencies
                const logFreq = Math.log10(freqData.frequency + 1);
                if (!isNaN(logFreq) && isFinite(logFreq)) {
                    avgFrequency += logFreq;
                    freqCount++;
                }
            }
        }
        if (freqCount > 0) {
            avgFrequency /= freqCount;
            if (!isNaN(avgFrequency) && isFinite(avgFrequency)) {
                const frequencyScore = Math.max(0, 100 - avgFrequency * 15);
                score += frequencyScore * 0.3;
                totalWeight += 0.3;
            }
        }
        
        // Word length complexity (longer words = harder)
        const avgLength = words.reduce((sum, word) => sum + word.length, 0) / words.length;
        const lengthScore = Math.min(100, Math.max(0, (avgLength - 3) * 12));
        if (!isNaN(lengthScore) && isFinite(lengthScore)) {
            score += lengthScore * 0.2;
            totalWeight += 0.2;
        }
        
        // Curated list bonus (common words = easier) - sample for performance
        let curatedCount = 0;
        for (const word of words.slice(0, 10)) {
            const membership = await this.dataManager.getCuratedMemberships(word);
            if (membership && (membership.ogden_basic_action || membership.ogden_basic_concept || 
                              membership.swadesh_core || membership.stop_nltk)) {
                curatedCount++;
            }
        }
        const sampleSize = Math.min(10, words.length);
        const curatedRatio = curatedCount / sampleSize;
        const curatedScore = (1 - curatedRatio) * 30; // Less curated words = harder
        if (!isNaN(curatedScore) && isFinite(curatedScore)) {
            score += curatedScore * 0.1;
            totalWeight += 0.1;
        }
        
        if (totalWeight === 0) {
            // Fallback scoring based just on solution count
            return Math.max(0, 100 - Math.log10(words.length + 1) * 20);
        }
        
        const finalScore = score / totalWeight;
        

        
        return finalScore;
    }
    
    /**
     * Categorize difficulty based on actual score distribution
     */
    categorizeDifficulty(sortedScores, unsolvableCount) {
        const levels = {
            trivial: [],    // Bottom 5% (easiest)
            easy: [],       // 5-25%
            moderate: [],   // 25-50%
            challenging: [],// 50-75%
            hard: [],       // 75-95%
            extreme: [],    // Top 5% (hardest)
            impossible: Array(unsolvableCount).fill(null).map(() => ({ plate: 'XXX', score: 100, solutionCount: 0 }))
        };
        
        const total = sortedScores.length;
        const thresholds = {
            trivial: Math.floor(total * 0.05),
            easy: Math.floor(total * 0.25),
            moderate: Math.floor(total * 0.50),
            challenging: Math.floor(total * 0.75),
            hard: Math.floor(total * 0.95)
        };
        
        sortedScores.forEach((item, index) => {
            if (index < thresholds.trivial) levels.trivial.push(item);
            else if (index < thresholds.easy) levels.easy.push(item);
            else if (index < thresholds.moderate) levels.moderate.push(item);
            else if (index < thresholds.challenging) levels.challenging.push(item);
            else if (index < thresholds.hard) levels.hard.push(item);
            else levels.extreme.push(item);
        });
        
        return levels;
    }
    
    /**
     * Calculate standard deviation
     */
    calculateStandardDeviation(values) {
        const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
        const squaredDiffs = values.map(val => Math.pow(val - mean, 2));
        const avgSquaredDiff = squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length;
        return Math.sqrt(avgSquaredDiff);
    }

    /**
     * Print comprehensive analysis results
     */
    async printResults() {
        const stats = this.results.statistics;
        const solverStats = this.solver.getStats();
        
        console.log('🏆 COMPREHENSIVE PLATE ANALYSIS RESULTS');
        console.log('='.repeat(70));
        
        console.log('\n⚡ Performance Metrics:');
        console.log(`  Plates analyzed: ${stats.basic_stats.total_plates.toLocaleString()}`);
        console.log(`  Total time: ${(stats.processing_stats.total_time_ms / 1000).toFixed(2)}s`);
        console.log(`  Average per plate: ${stats.processing_stats.avg_time_per_plate_ms.toFixed(2)}ms`);
        console.log(`  Processing rate: ${stats.processing_stats.plates_per_second.toFixed(1)} plates/sec`);
        
        console.log('\n📊 Basic Solution Statistics:');
        console.log(`  Total solutions found: ${stats.basic_stats.total_words.toLocaleString()}`);
        console.log(`  Average per plate: ${stats.basic_stats.avg_solutions_per_plate.toFixed(1)}`);
        console.log(`  Maximum solutions: ${stats.basic_stats.max_solutions.toLocaleString()}`);
        console.log(`  Minimum solutions: ${stats.basic_stats.min_solutions.toLocaleString()}`);
        console.log(`  Unsolvable plates: ${stats.basic_stats.unsolvable_count.toLocaleString()}`);
        
        console.log('\n📈 Frequency Distribution Analysis (SUBTLEX-US percentiles):');
        console.log(`  Very High (>3.33, top 10%): ${stats.frequency_analysis.veryHighFreq.toLocaleString()} (${((stats.frequency_analysis.veryHighFreq / stats.frequency_analysis.total_analyzed) * 100).toFixed(1)}%)`);
        console.log(`  High (0.75-3.33, 75-90th %ile): ${stats.frequency_analysis.highFreq.toLocaleString()} (${((stats.frequency_analysis.highFreq / stats.frequency_analysis.total_analyzed) * 100).toFixed(1)}%)`);
        console.log(`  Medium (0.16-0.75, 50-75th %ile): ${stats.frequency_analysis.mediumFreq.toLocaleString()} (${((stats.frequency_analysis.mediumFreq / stats.frequency_analysis.total_analyzed) * 100).toFixed(1)}%)`);
        console.log(`  Low (0.04-0.16, 25-50th %ile): ${stats.frequency_analysis.lowFreq.toLocaleString()} (${((stats.frequency_analysis.lowFreq / stats.frequency_analysis.total_analyzed) * 100).toFixed(1)}%)`);
        console.log(`  Very Low (<0.04, bottom 25%): ${stats.frequency_analysis.veryLowFreq.toLocaleString()} (${((stats.frequency_analysis.veryLowFreq / stats.frequency_analysis.total_analyzed) * 100).toFixed(1)}%)`);
        console.log(`  No frequency data: ${stats.frequency_analysis.unknownFreq.toLocaleString()} (${((stats.frequency_analysis.unknownFreq / stats.frequency_analysis.total_analyzed) * 100).toFixed(1)}%)`);
        
        console.log('\n🏷️ Curated List Distribution:');
        console.log(`  OGDEN Basic English: ${stats.curated_lists.ogden.total.toLocaleString()} words`);
        console.log(`  ROGET Thesaurus: ${stats.curated_lists.roget?.total.toLocaleString() || 0} words`);
        console.log(`  AFINN Sentiment: +${stats.curated_lists.afinn.positive.toLocaleString()} positive, -${stats.curated_lists.afinn.negative.toLocaleString()} negative, ${stats.curated_lists.afinn.neutral.toLocaleString()} neutral`);
        console.log(`  SWADESH Core/Extended: ${stats.curated_lists.swadesh.total.toLocaleString()} words`);
        console.log(`  STOP words: ${stats.curated_lists.stop.total.toLocaleString()} words`);
        
        console.log('\n🔊 Phonetic Coverage:');
        console.log(`  With pronunciations: ${stats.phonetic_coverage.withPronunciation.toLocaleString()} (${stats.phonetic_coverage.coverage_percentage}%)`);
        console.log(`  Without pronunciations: ${stats.phonetic_coverage.withoutPronunciation.toLocaleString()}`);
        
        console.log('\n📏 Word Length Distribution:');
        const sortedLengths = Object.keys(stats.length_distribution).map(Number).sort((a, b) => a - b);
        const totalWords = Object.values(stats.length_distribution).reduce((a, b) => a + b, 0);
        for (const length of sortedLengths) { // Show all lengths
            const count = stats.length_distribution[length];
            const percentage = (count / totalWords * 100).toFixed(1);
            console.log(`  ${length} letters: ${count.toLocaleString()} words (${percentage}%)`);
        }
        
        console.log('\n🎯 Sophisticated Difficulty Distribution:');
        console.log(`  Score Statistics: μ=${stats.difficulty_distribution.score_statistics.mean.toFixed(1)}, σ=${stats.difficulty_distribution.score_statistics.std_dev.toFixed(1)}`);
        const levels = stats.difficulty_distribution.levels;
        console.log(`  Trivial (0-5th percentile): ${levels.trivial.length.toLocaleString()}`);
        console.log(`  Easy (5-25th percentile): ${levels.easy.length.toLocaleString()}`);
        console.log(`  Moderate (25-50th percentile): ${levels.moderate.length.toLocaleString()}`);
        console.log(`  Challenging (50-75th percentile): ${levels.challenging.length.toLocaleString()}`);
        console.log(`  Hard (75-95th percentile): ${levels.hard.length.toLocaleString()}`);
        console.log(`  Extreme (95-100th percentile): ${levels.extreme.length.toLocaleString()}`);
        console.log(`  Impossible (no solutions): ${levels.impossible.length.toLocaleString()}`);
        
        console.log('\n🧠 Solver Performance:');
        console.log(`  Cache hits: ${solverStats.cacheHits} (${(solverStats.cacheHits / solverStats.totalSolves * 100).toFixed(1)}%)`);
        console.log(`  Cache entries: ${solverStats.cacheSize.toLocaleString()}`);
        
        // Show some example plates from each difficulty level
        console.log('\n🎲 Example Plates by Difficulty:');
        const examples = ['trivial', 'easy', 'moderate', 'challenging', 'hard', 'extreme'];
        for (const level of examples) {
            if (levels[level].length > 0) {
                const example = levels[level][0];
                console.log(`  ${level.toUpperCase()}: ${example.plate} (${example.solutionCount} solutions, score: ${example.score.toFixed(1)})`);
            }
        }

        // Show detailed profiles for random plates
        await this.printRandomPlateProfiles(5);
    }

    /**
     * Print detailed profiles for random license plates
     */
    async printRandomPlateProfiles(count = 5) {
        if (!this.results || !this.results.plateSolutions || Object.keys(this.results.plateSolutions).length === 0) {
            console.log('\n❌ No results available for profile display');
            return;
        }

        console.log(`\n🔍 Detailed Profiles for ${count} Random License Plates:\n`);
        console.log('=' .repeat(80));

        // Get plates with solutions and their difficulty info
        const plateEntries = Object.entries(this.results.plateSolutions);
        const platesWithSolutions = plateEntries.filter(([plate, words]) => words.length > 0);
        
        if (platesWithSolutions.length === 0) {
            console.log('\n❌ No plates with solutions found');
            return;
        }

        const selectedPlates = [];
        
        for (let i = 0; i < count && i < platesWithSolutions.length; i++) {
            const randomIndex = Math.floor(Math.random() * platesWithSolutions.length);
            const [plate, words] = platesWithSolutions[randomIndex];
            
            if (!selectedPlates.find(p => p.plate === plate)) {
                // Find difficulty info from difficulty levels
                const difficulty = this.findPlateDifficulty(plate);
                const score = await this.calculateDifficultyScore(plate, words);
                
                selectedPlates.push({
                    plate,
                    words,
                    difficulty,
                    score
                });
            }
        }

        for (let i = 0; i < selectedPlates.length; i++) {
            const result = selectedPlates[i];
            await this.printPlateProfile(result, i + 1);
            if (i < selectedPlates.length - 1) {
                console.log('\n' + '-'.repeat(80) + '\n');
            }
        }
        
        console.log('\n' + '='.repeat(80));
    }

    /**
     * Find difficulty level for a plate
     */
    findPlateDifficulty(targetPlate) {
        const levels = this.results.difficultyLevels;
        
        for (const [difficulty, plates] of Object.entries(levels)) {
            if (plates.find(p => p.plate === targetPlate)) {
                return difficulty;
            }
        }
        
        return 'unknown';
    }

    /**
     * Categorize word frequency based on SUBTLEX-US percentiles
     */
    categorizeFrequency(frequency) {
        if (frequency > 3.33) return 'VHigh';      // Top 10%
        if (frequency >= 0.75) return 'High';     // 75-90th percentile
        if (frequency >= 0.16) return 'Med';      // 50-75th percentile
        if (frequency >= 0.04) return 'Low';      // 25-50th percentile
        return 'VLow';                             // Bottom 25%
    }

    /**
     * Print detailed profile for a single license plate
     */
    async printPlateProfile(plateResult, profileNumber) {
        const { plate, words, difficulty, score } = plateResult;
        
        console.log(`Profile #${profileNumber}: License Plate "${plate}"`);
        console.log(`Difficulty: ${difficulty} (Score: ${score.toFixed(1)})`);
        console.log(`Total Solutions: ${words.length.toLocaleString()}`);
        
        // Show first 15 words with detailed info
        const wordsToShow = Math.min(15, words.length);
        console.log(`\nFirst ${wordsToShow} Solutions:`);
        
        for (let i = 0; i < wordsToShow; i++) {
            const word = words[i];
            const profile = await this.getWordProfile(word);
            console.log(`  ${(i + 1).toString().padStart(2)}. ${word.padEnd(15)} ${profile}`);
        }
        
        if (words.length > wordsToShow) {
            console.log(`      ... and ${(words.length - wordsToShow).toLocaleString()} more solutions`);
        }

        // Word length distribution for this plate
        const lengthDist = {};
        words.forEach(word => {
            const len = word.length;
            lengthDist[len] = (lengthDist[len] || 0) + 1;
        });
        
        console.log(`\nWord Length Distribution:`);
        Object.keys(lengthDist)
            .sort((a, b) => parseInt(a) - parseInt(b))
            .forEach(len => {
                const count = lengthDist[len];
                const pct = ((count / words.length) * 100).toFixed(1);
                const bar = '█'.repeat(Math.max(1, Math.floor(count / words.length * 20)));
                console.log(`  ${len.padStart(2)} letters: ${count.toString().padStart(4)} (${pct.padStart(5)}%) ${bar}`);
            });
    }

    /**
     * Get comprehensive profile string for a word
     */
    async getWordProfile(word) {
        const profiles = [];
        
        // Frequency information
        const freqData = await this.dataManager.getFrequency(word);
        if (freqData && freqData.frequency) {
            const freq = freqData.frequency;
            const category = this.categorizeFrequency(freq);
            profiles.push(`freq:${category}(${freq.toFixed(2)})`);
        } else {
            profiles.push('freq:none');
        }

        // Curated list memberships
        const curated = await this.dataManager.getCuratedMemberships(word);
        if (curated) {
            const lists = [];
            if (curated.ogden_basic_action || curated.ogden_basic_quality || curated.ogden_basic_name) lists.push('OGDEN');
            if (curated.roget_common) lists.push('ROGET');
            if (curated.afinn_pos_1 || curated.afinn_neg_2) lists.push('AFINN');
            if (curated.swadesh) lists.push('SWADESH');
            if (curated.stop_word) lists.push('STOP');
            
            if (lists.length > 0) {
                profiles.push(`lists:[${lists.join(',')}]`);
            } else {
                profiles.push('lists:none');
            }
        } else {
            profiles.push('lists:none');
        }

        // Syllable count (from derived data)
        const syllableCount = await this.dataManager.getSyllableCount(word);
        if (syllableCount !== null) {
            profiles.push(`syl:${syllableCount}`);
        } else {
            profiles.push('syl:?');
        }

        return profiles.join(' | ');
    }

    /**
     * Save results to files (Node.js) or return data (Browser)
     */
    async saveResults(outputDir = 'analysis_output') {
        const timestamp = new Date().toISOString();
        const metadata = {
            generated_by: 'PL8WRDS PlateAnalyzer v2.0',
            timestamp,
            configuration: this.config
        };
        
        const statsOutput = { ...this.results.statistics, metadata };
        const difficultyOutput = { 
            difficulty_levels: this.results.difficultyLevels, 
            metadata 
        };
        const solutionsOutput = { ...this.results.plateSolutions, metadata };
        
        // Environment detection
        if (typeof process !== 'undefined' && process.versions && process.versions.node) {
            // Node.js environment - save to files
            const fs = await import('fs');
            
            if (!fs.existsSync(outputDir)) {
                fs.mkdirSync(outputDir, { recursive: true });
            }
            
            fs.writeFileSync(
                `${outputDir}/analysis_statistics.json`, 
                JSON.stringify(statsOutput, null, 2)
            );
            
            fs.writeFileSync(
                `${outputDir}/game_difficulty_data.json`, 
                JSON.stringify(difficultyOutput, null, 2)
            );
            
            fs.writeFileSync(
                `${outputDir}/plate_solutions.json`, 
                JSON.stringify(solutionsOutput, null, 2)
            );
            
            console.log(`💾 Results saved to ${outputDir}/`);
            return outputDir;
        } else {
            // Browser environment - return data for download
            console.log('💾 Results prepared for download');
            return {
                statistics: statsOutput,
                difficulty: difficultyOutput,
                solutions: solutionsOutput
            };
        }
    }
}

export default PlateAnalyzer; 