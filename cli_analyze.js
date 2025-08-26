#!/usr/bin/env node
/**
 * License Plate Analysis CLI - Improved replacement for Python utils
 * Fast, configurable analysis of license plate word combinations
 */

import PlateAnalyzer from './src/analysis/PlateAnalyzer.js';

async function main() {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const sampleSize = args[0] ? parseInt(args[0]) : null;
    
    // Configuration options
    const config = {
        minWordLength: 2,
        maxWordLength: 20,
        useFrequencyScoring: false,  // Faster analysis without scoring
        useCuratedLists: false,      // Faster analysis without curated data
        maxResultsPerPlate: 50000,   // Higher limit for complete analysis
        enableProgress: true,
        progressInterval: 1000       // Progress every 1000 plates
    };
    
    console.log('🚀 PL8WRDS License Plate Analyzer v2.0\n');
    
    if (sampleSize) {
        console.log(`📊 Sample Analysis: ${sampleSize.toLocaleString()} plates`);
    } else {
        console.log('📊 Full Analysis: All 17,576 license plates');
    }
    
    console.log(`⚙️  Solver Configuration:`);
    console.log(`   Word length: ${config.minWordLength}-${config.maxWordLength}`);
    console.log(`   Frequency word ranking: ${config.useFrequencyScoring ? 'ON' : 'OFF'}`);
    console.log(`   Curated list bonuses: ${config.useCuratedLists ? 'ON' : 'OFF'}`);
    console.log(`   Max results per plate: ${config.maxResultsPerPlate.toLocaleString()}`);
    console.log(`   📊 Linguistic analysis: ALWAYS ON (comprehensive)\n`);
    
    try {
        // Initialize analyzer
        const analyzer = new PlateAnalyzer(config);
        await analyzer.initialize();
        
        // Determine plates to analyze
        let plates = null;
        if (sampleSize) {
            plates = analyzer.generateAllPlates().slice(0, sampleSize);
        }
        
        // Run analysis
        const results = await analyzer.analyzeAll(plates);
        
        // Print results
        await analyzer.printResults();
        
        // Save results
        await analyzer.saveResults();
        
        console.log('\n✅ Analysis complete!');
        
    } catch (error) {
        console.error('❌ Analysis failed:', error.message);
        process.exit(1);
    }
}

// Show usage information
function showUsage() {
    console.log('Usage: node analyze_plates.js [sample_size]');
    console.log('');
    console.log('Examples:');
    console.log('  node analyze_plates.js        # Analyze all 17,576 plates');
    console.log('  node analyze_plates.js 1000   # Analyze first 1,000 plates');
    console.log('  node analyze_plates.js 100    # Quick test with 100 plates');
}

// Handle help flag
if (process.argv.includes('--help') || process.argv.includes('-h')) {
    showUsage();
    process.exit(0);
}

// Run main function
main().catch(console.error); 