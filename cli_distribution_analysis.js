/**
 * CLI script to analyze the curated list representation for every possible plate.
 * This script iterates through every 3-letter plate, finds its solutions,
 * and calculates the exact percentage of solution words belonging to various curated lists.
 * The final output is a comprehensive JSON database mapping each plate to its analysis.
 * 
 * Usage: node cli_distribution_analysis.js
 */

import fs from 'fs';
import DataManager from './src/data/DataManager.js';
import LicensePlateSolver from './src/game/LicensePlateSolver.js';

// --- Configuration ---
const OUTPUT_FILE = './analysis_output/plate_analysis_database.json';

// Function to get all list names by iterating through all memberships
async function getAllListNames(dataManager) {
    await dataManager.ensureDataLoaded('curatedMemberships');
    
    console.log("Dynamically discovering all curated list names...");
    const listNameSet = new Set();
    
    for (const memberships of dataManager.cache.curatedMemberships.values()) {
        for (const key in memberships) {
            if (typeof memberships[key] === 'boolean') {
                listNameSet.add(key);
            }
        }
    }
    
    const listNames = Array.from(listNameSet);
    console.log(`Discovered ${listNames.length} lists.`);
    return listNames;
}

/**
 * Generates all 3-letter combinations from AAA to ZZZ.
 * @returns {string[]} An array of 17,576 plate combinations.
 */
function generateAllPlates() {
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
    return plates;
}

async function main() {
    console.log('🚀 Starting Full Plate Analysis...');
    const startTime = Date.now();

    console.log('Initializing DataManager and loading data...');
    const dataManager = new DataManager();
    await dataManager.initialize();
    
    const solver = new LicensePlateSolver();
    const allWords = dataManager.getWords();
    const allPlates = generateAllPlates();
    const listsToAnalyze = await getAllListNames(dataManager);
    
    console.log('Analyzing lists:', listsToAnalyze);

    const plateDatabase = {};

    console.log(`Analyzing ${allPlates.length} plates...`);

    for (let i = 0; i < allPlates.length; i++) {
        const plate = allPlates[i];
        
        if ((i + 1) % 500 === 0) {
            console.log(`...processed ${i + 1} plates.`);
        }

        const solutions = solver.findAllSolutions(plate, allWords);
        if (solutions.length === 0) {
            plateDatabase[plate] = { solutionCount: 0 };
            continue;
        }

        const listCounts = {};
        for (const word of solutions) {
            const memberships = await dataManager.getCuratedMemberships(word); // ensure loaded
            if (memberships) {
                for (const listName of listsToAnalyze) {
                    if (memberships[listName] === true) {
                        listCounts[listName] = (listCounts[listName] || 0) + 1;
                    }
                }
            }
        }
        
        const analysis = { solutionCount: solutions.length };
        for (const listName in listCounts) {
            analysis[listName] = (listCounts[listName] / solutions.length); // Store as a raw fraction (0 to 1)
        }
        plateDatabase[plate] = analysis;
    }

    console.log('✅ Analysis Complete!');
    
    const results = {
        metadata: {
            totalPlates: allPlates.length,
            listsAnalyzed: listsToAnalyze,
            runDate: new Date().toISOString(),
            durationSeconds: (Date.now() - startTime) / 1000,
        },
        database: plateDatabase,
    };

    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(results, null, 2));
    
    console.log(`\nResults for ${Object.keys(plateDatabase).length} plates saved to ${OUTPUT_FILE}`);
}

main().catch(console.error); 