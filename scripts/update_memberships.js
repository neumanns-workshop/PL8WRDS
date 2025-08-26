/**
 * This script automatically discovers and processes wordlist files from the 
 * `/scripts/wordlists` directory, merging them into the main curated list memberships file.
 *
 * To add a new list, simply create a new file in the wordlists directory,
 * where the filename is the list name (e.g., `my_new_list.js`), and the
 * default export is an array of words.
 *
 * Usage: node scripts/update_memberships.js
 */

import fs from 'fs';
import path from 'path';

const MEMBERSHIPS_FILE = './modular_data/curated_list_memberships.json';
const WORDLISTS_DIR = './scripts/wordlists';
const SIGNATURE = 'jneumann/pl8wrds-gemini-v1';

async function main() {
  console.log('🚀 Starting to update curated list memberships...');

  // Read the existing memberships file
  let membershipsData;
  try {
    const fileContent = fs.readFileSync(MEMBERSHIPS_FILE, 'utf8');
    membershipsData = JSON.parse(fileContent);
  } catch (error) {
    console.error(`Error reading or parsing ${MEMBERSHIPS_FILE}`, error);
    return;
  }
  const allMemberships = membershipsData.memberships;

  // Find all wordlist files in the directory
  const wordlistFilenames = fs.readdirSync(WORDLISTS_DIR).filter(
    file => file.endsWith('.js')
  );

  if (wordlistFilenames.length === 0) {
    console.log('No wordlist files found in `scripts/wordlists`. Exiting.');
    return;
  }

  console.log(`Found ${wordlistFilenames.length} wordlist files to process...`);

  let totalWordsUpdated = 0;
  let listsProcessed = 0;

  for (const filename of wordlistFilenames) {
    const listName = path.basename(filename, '.js');
    const filePath = path.join(WORDLISTS_DIR, filename);
    
    try {
      // Dynamically import the wordlist
      const { default: words } = await import(filePath);
      
      console.log(`  - Processing list: ${listName} (${words.length} words)`);
      let wordsAddedToList = 0;

      for (const word of words) {
        const normalizedWord = word.toLowerCase();
        if (!allMemberships[normalizedWord]) {
          allMemberships[normalizedWord] = {};
        }
        
        if (!allMemberships[normalizedWord][listName]) {
          allMemberships[normalizedWord][listName] = true;
          
          if (!allMemberships[normalizedWord].signatures) {
            allMemberships[normalizedWord].signatures = [];
          }
          if (!allMemberships[normalizedWord].signatures.includes(SIGNATURE)) {
            allMemberships[normalizedWord].signatures.push(SIGNATURE);
          }
          wordsAddedToList++;
        }
      }
      if (wordsAddedToList > 0) {
        totalWordsUpdated += wordsAddedToList;
      }
      listsProcessed++;

    } catch (error) {
      console.error(`\nError processing file ${filename}:`, error);
    }
  }

  // Write the updated data back to the file
  membershipsData.metadata.lastUpdated = new Date().toISOString();
  if (!membershipsData.metadata.sources.includes(SIGNATURE)) {
      membershipsData.metadata.sources.push(SIGNATURE);
  }
  
  try {
    fs.writeFileSync(MEMBERSHIPS_FILE, JSON.stringify(membershipsData, null, 2));
    console.log('\n✅ Successfully updated curated_list_memberships.json');
    console.log(`  - Processed ${listsProcessed} lists.`);
    console.log(`  - Added/updated memberships for ${totalWordsUpdated} unique words.`);
  } catch (error) {
    console.error(`Error writing to ${MEMBERSHIPS_FILE}`, error);
  }
}

main(); 