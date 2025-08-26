# PL8WRDS

A word puzzle game where players find words containing license plate letters in order.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0). This means you are free to:
- Share: Copy and redistribute the material in any medium or format
- Adapt: Remix, transform, and build upon the material

Under the following terms:
- Attribution: You must give appropriate credit
- NonCommercial: You may not use the material for commercial purposes

## Version
Current version: 0.1.0-beta.4

This is a beta release. While the core gameplay is complete, you may encounter bugs or incomplete features. Please report any issues through GitHub.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/jneumann/pl8wrds.git
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Open index.html in a web browser or serve using a local server

## Game Overview

PL8WRDS challenges players to find words that contain three given letters in sequence. For example, with the letters "QRI":
- ✓ "QUARANTINE" (Q->R->I in order)
- ✓ "AQUARIUM" (Q->R->I in order)
- ✗ "INQUIRY" (Q->R but missing I)
- ✓ "INQUIRIES" (Q->R->I in order)

### Features

- Dynamic license plate generation with varying difficulties
- Combo system for chaining valid words
- Score multipliers based on word rarity
- Statistics tracking and personal bests
- Advanced hint system with multiple hint types:
  - Lexical hints (coverage %, difficulty, rare word count)
  - Semantic hints (definitions, synonyms)
  - Phonetic hints (rhyming words)
- Responsive design with:
  - Dynamic scaling for different screen sizes
  - Custom pixel font (ThaleahFat)
  - Smooth animations and transitions
  - Full mobile support with touch controls
  - Consistent UI across all screens

## Technical Implementation

### Core Components

1. **Word System** (`wordData.js`)
   - Loads word dictionary from JSONL file
   - Stores word metadata (frequency, definitions, synonyms)
   - Provides word validation and search functionality
   - Indexes words by length for efficient lookup

2. **License Plate System** (`plateData.js`)
   - Manages 3-letter combinations with difficulty ratings
   - Weighted random plate generation
   - Tracks used plates and best scores
   - Validates words against plate patterns

3. **Scoring System** (`scoreFactory.js`)
   - Base points (10 per word)
   - Combo points for consecutive valid words
   - Multipliers based on word rarity:
     - Ultra Common (>0.01): +0.0×
     - Very Common (>0.001): +0.05×
     - Common (>0.0001): +0.10×
     - Moderately Common (>0.00001): +0.25×
     - Uncommon (>0.000001): +0.50×
     - Rare (>0.0000001): +0.75×
     - Very Rare (≤0.0000001): +1.0×

4. **Game Logic** (`game.js`)
   - Core gameplay loop and state management
   - Input handling and word validation
   - Score calculation and statistics tracking
   - UI updates and animations

### Data Structure

```
PL8WRDS/
├── index.html        # Game interface
├── LICENSE.txt       # CC BY-NC 4.0 License
├── README.md        # Project documentation
├── data/            # Data files
│   ├── letter_combinations_with_possibilities_and_difficulties.jsonl
│   ├── letter_frequencies.json
│   └── wordlist_v1.jsonl
└── src/             # Source code
    ├── core/        # Core game logic
    │   ├── game.js
    │   ├── gameController.js
    │   ├── gameState.js
    │   └── scoreFactory.js
    ├── data/        # Data management
    │   ├── hintData.js
    │   ├── plateData.js
    │   └── wordData.js
    ├── ui/          # User interface
    │   ├── eventHandler.js
    │   ├── uiManager.js
    │   ├── fonts/
    │   │   └── ThaleahFat.ttf
    │   ├── screens/ # Screen components
    │   │   ├── AboutScreen.js
    │   │   ├── BaseScreen.js
    │   │   ├── GameScreen.js
    │   │   ├── MainMenuScreen.js
    │   │   ├── ScreenManager.js
    │   │   └── StatsScreen.js
    │   └── styles/  # Modular CSS
    │       ├── about.css
    │       ├── base.css
    │       ├── carousel.css
    │       ├── game-over.css
    │       ├── game-screen.css
    │       ├── license-plate.css
    │       ├── main.css
    │       ├── menu.css
    │       ├── stats.css
    │       └── status.css
    └── utils/       # Utilities
        └── statusManager.js
```

### Game Flow

1. Player starts game from main menu
2. System generates random license plate based on weighted difficulties
3. Player types words containing plate letters in sequence
4. Each valid word:
   - Adds 10 base points
   - Contributes to combo if consecutive
   - Affects score multiplier based on rarity
5. Final plate score = (base points + combo points) × multiplier
6. Game continues for 90 seconds
7. Statistics and high scores are saved locally

## Controls

- **Space**: Start game & get new letters
- **Enter**: Submit word
- **Backspace**: Delete letter
- **A-Z**: Type letters to form words
- **Touch**: Full mobile support with touch controls

## Statistics

The game tracks various statistics including:
- Games played
- Total score
- Best score
- Unique plates collected
- Best combo
- Best multiplier
- Score history
- Hidden rare words discovered

## Development

The project uses vanilla JavaScript with a modular architecture. Key design patterns:
- Singleton pattern for core systems (WordData, PlateData)
- Factory pattern for score calculation
- Observer pattern for UI updates
- Queue system for status messages
- Event-driven architecture for game state management
- Modular CSS with component-specific styles

### Hint System

The game features a sophisticated hint system with three types of hints:

1. **Lexical Hints**
   - Word coverage percentage
   - Plate difficulty rating
   - Number of rare words possible

2. **Semantic Hints**
   - Word definitions
   - Related synonyms (excluding words that would be valid answers)

3. **Phonetic Hints**
   - Rhyming words (excluding words that would be valid answers)

The system intelligently cycles through hint types and includes fallback mechanisms to ensure helpful hints are always available.

### Data Loading

1. Word data is loaded from a JSONL file containing:
   - Word text
   - Word length
   - Usage frequency
   - Definitions
   - Synonyms
   - Rhyming words

2. Plate data is loaded from a JSONL file containing:
   - Letter combinations
   - Word possibilities count
   - Difficulty ratings

### UI/UX Features

1. **Status Message System**
   - Priority-based message queue
   - Animated transitions
   - Color-coded feedback
   - Context-aware positioning

2. **Interactive Elements**
   - Animated license plates
   - Word combo display with horizontal scrolling
   - Score popups with animations
   - Responsive button feedback

3. **Carousel Systems**
   - About screen with tutorial slides
   - Top plates showcase
   - Combo words display
   - Touch and keyboard navigation

4. **Mobile Support**
   - Responsive design for all screen sizes
   - Touch-friendly controls
   - Optimized layouts for mobile devices
   - Consistent UI across platforms

### Performance Considerations

- Words indexed by length for efficient lookup
- Plate combinations cached with difficulty ratings
- Status message queue for smooth UI updates
- Efficient regex patterns for word validation
- Optimized score calculation with frequency ranges
- Modular CSS for better maintainability

## Future Enhancements

Potential areas for expansion:
- Online leaderboards
- Additional game modes
- Achievement system
- Social sharing
- Additional word metadata
