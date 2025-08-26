#!/usr/bin/env node

/**
 * Demo: PL8WRDS GameAPI - Show how easy it is to use our data for games
 */

import DataManager from './src/data/DataManager.js';
import LicensePlateSolver from './src/game/LicensePlateSolver.js';
import GameAPI from './src/game/GameAPI.js';

async function demoGameAPI() {
    console.log('🎮 PL8WRDS GameAPI Demo\n');
    
    // Initialize our game system
    console.log('⚙️  Initializing game systems...');
    const dataManager = new DataManager();
    await dataManager.initialize();
    
    const solver = new LicensePlateSolver(dataManager);
    const gameAPI = new GameAPI(dataManager, solver);
    
    console.log(`✅ Game ready! Dictionary: ${dataManager.getWords().length} words\n`);
    
    // Demo 1: Word Validation with Rich Data
    console.log('🔍 DEMO 1: WORD VALIDATION WITH RICH DATA');
    console.log('=' .repeat(50));
    
    const testPlate = 'CAT';
    const testWords = ['cat', 'act', 'cart', 'xyz', 'elephant'];
    
    for (const word of testWords) {
        const result = await gameAPI.validateWord(word, testPlate);
        
        if (result.valid) {
            console.log(`✅ "${word}" → VALID`);
            console.log(`   📏 ${result.length} letters, ${result.syllables || '?'} syllables`);
            console.log(`   📊 Frequency: ${result.frequencyRank} (${result.frequency || 'unknown'})`);
            
            if (result.definitions) {
                console.log(`   📖 Definitions: ${Object.keys(result.definitions).length} sources`);
            }
            
            if (result.etymologies) {
                console.log(`   🔍 Etymology: ${Object.keys(result.etymologies).length} sources`);
            }
            
            if (result.pronunciation) {
                console.log(`   🗣️  Pronunciation: ${result.pronunciation}`);
            }
            
            if (result.lists.length > 0) {
                console.log(`   🏷️  Word lists: ${result.lists.join(', ')}`);
            }
            
            if (result.sentiment) {
                console.log(`   😊 Sentiment: ${result.sentiment > 0 ? 'positive' : 'negative'} (${result.sentiment})`);
            }
        } else {
            console.log(`❌ "${word}" → INVALID (${result.reason})`);
        }
        console.log();
    }
    
    // Demo 2: Hint System
    console.log('\n💡 DEMO 2: HINT SYSTEM');
    console.log('=' .repeat(50));
    
    const hintPlates = ['DOG', 'MUSIC', 'XYZ'];
    
    for (const plate of hintPlates) {
        console.log(`🎯 Hints for "${plate}":`);
        const hints = await gameAPI.generateHints(plate, 3);
        
        hints.forEach((hint, index) => {
            console.log(`   ${index + 1}. [${hint.type}] ${hint.message}`);
        });
        console.log();
    }
    
    // Demo 3: Deep Dive into Definitions and Etymology
    console.log('\n📚 DEMO 3: DEFINITIONS AND ETYMOLOGY');
    console.log('=' .repeat(50));
    
    const detailedWords = ['fantastic', 'computer', 'love', 'run'];
    
    for (const word of detailedWords) {
        console.log(`📖 Deep dive for "${word}":`);
        
        // Get definitions
        const definitions = await gameAPI.getDefinitions(word);
        if (definitions) {
            console.log(`   📖 DEFINITIONS (${Object.keys(definitions).length} sources):`);
            for (const [source, defs] of Object.entries(definitions)) {
                if (Array.isArray(defs) && defs.length > 0) {
                    console.log(`      ${source}: ${defs[0].substring(0, 80)}...`);
                }
            }
        }
        
        // Get etymologies
        const etymologies = await gameAPI.getEtymologies(word);
        if (etymologies) {
            console.log(`   🔍 ETYMOLOGY (${Object.keys(etymologies).length} sources):`);
            for (const [source, etym] of Object.entries(etymologies)) {
                if (etym) {
                    console.log(`      ${source}: ${etym.substring(0, 80)}...`);
                }
            }
        }
        
        // Get semantic relationships
        const semantics = await gameAPI.getSemanticRelationships(word);
        if (semantics) {
            console.log(`   🔗 SEMANTIC RELATIONSHIPS:`);
            const relTypes = Object.keys(semantics);
            console.log(`      Available: ${relTypes.join(', ')}`);
        }
        
        // Get basic data too
        const data = await gameAPI.getCompleteWordData(word);
        console.log(`   📊 BASIC: ${data.length} letters, ${data.syllables || '?'} syllables, ${data.frequencyRank} frequency`);
        
        if (data.pronunciation) {
            console.log(`   🗣️  PRONUNCIATION: ${data.pronunciation}`);
        }
        
        console.log();
    }
    
    // Demo 4: Rhyming Hints
    console.log('\n🎵 DEMO 4: RHYMING HINTS');
    console.log('=' .repeat(50));
    
    const rhymeWords = ['cat', 'dog', 'play', 'bright'];
    
    for (const word of rhymeWords) {
        const rhymeHint = await gameAPI.getRhymingHint(word);
        if (rhymeHint) {
            console.log(`🎼 "${word}" → ${rhymeHint.message}`);
        } else {
            console.log(`🔇 "${word}" → No rhymes found in our data`);
        }
    }
    
    // Demo 5: Simple Data Access Methods
    console.log('\n\n⚡ DEMO 5: SIMPLE DATA ACCESS');
    console.log('=' .repeat(50));
    
    const quickWords = ['happy', 'computer', 'run'];
    
    for (const word of quickWords) {
        console.log(`🔍 Quick access for "${word}":`);
        
        // Fast validation checks
        console.log(`   ✅ Valid word: ${gameAPI.isWordValid(word)}`);
        console.log(`   🔤 Can make from "RUN": ${gameAPI.canMakeFromPlate(word, 'RUN')}`);
        
        // Quick data access
        const rhymes = await gameAPI.getRhymes(word);
        console.log(`   🎵 Perfect rhymes: ${rhymes.slice(0, 3).join(', ')}${rhymes.length > 3 ? '...' : ''}`);
        
        console.log();
    }
    
    // Demo 6: Game Statistics
    console.log('\n\n📊 DEMO 6: GAME STATISTICS');
    console.log('=' .repeat(50));
    
    const stats = gameAPI.getGameStats();
    console.log('Game System Status:');
    console.log(`  📚 Dictionary size: ${stats.wordsInDictionary.toLocaleString()} words`);
    console.log(`  🧠 Game cache size: ${stats.cacheSize} items`);
    console.log(`  ⚡ Solver stats: ${stats.solverStats.totalSolves} solves, ${stats.solverStats.cacheHits} cache hits`);
    console.log(`  📦 Loaded modules: ${stats.dataManagerStats.loadedModules.join(', ')}`);
    
    console.log('\n🎉 Demo complete! Our data is ready for game development!\n');
    
    // Show simple usage examples
    console.log('💻 SIMPLE USAGE EXAMPLES:');
    console.log('=' .repeat(50));
    console.log('// Validate player input with rich data');
    console.log('const result = await gameAPI.validateWord("fantastic", "FTC");');
    console.log('if (result.valid) showWordInfo(result.definitions, result.etymologies);\n');
    
    console.log('// Quick word validation');
    console.log('if (gameAPI.isWordValid("computer") && gameAPI.canMakeFromPlate("computer", "CMP")) {');
    console.log('  // Show word details');
    console.log('}\n');
    
    console.log('// Access specific linguistic data');
    console.log('const definitions = await gameAPI.getDefinitions("love");');
    console.log('const etymologies = await gameAPI.getEtymologies("love");');
    console.log('const rhymes = await gameAPI.getRhymes("love");\n');
    
    console.log('🚀 Ready to use our rich linguistic data for games!');
}

// Run demo
demoGameAPI().catch(console.error); 