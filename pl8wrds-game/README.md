# 🚗 PL8WRDS React Game

A React-based implementation of the PL8WRDS license plate word game using pre-generated client-side data.

## 🎮 Game Overview

PL8WRDS is a word game where players find words that contain license plate letters **in the correct order** (but not necessarily consecutive). The game features:

- **15,715 unique collectible plates** with difficulty ratings
- **7+ million pre-computed word solutions** 
- **Complete offline gameplay** after initial data load
- **Real-time scoring** using ensemble algorithms
- **Beautiful, responsive UI** with game-like styling

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ 
- npm or yarn

### Installation & Running

```bash
# Install dependencies
npm install

# Start development server
npm start
```

The game will open at `http://localhost:3000` and automatically load the 27MB game data file.

## 🎯 How to Play

1. **Look at the license plate** (e.g., "ABC")
2. **Type words** that contain those letters in order
3. **Valid examples** for "ABC": "about", "cabinet", "fabric"
4. **Invalid examples**: "cab" (wrong order), "bac" (wrong order)
5. **Find all solutions** to complete the plate!

## 🏆 Game Features

### Scoring System
- Words scored using a **3D ensemble system**:
  - **Vocabulary sophistication** (word rarity)
  - **Information content** (solution surprisal)
  - **Orthographic complexity** (pattern difficulty)
- Score ranges: 0-29 (Basic) → 90-100 (Exceptional)

### Difficulty Ratings
Plates are rated by solution count (fewer solutions = harder):
- **Ultra Hard** 🔥 (90-100) - Very few solutions (< 25 words)
- **Very Hard** 💪 (80-89) - Limited solutions (25-50 words)  
- **Hard** ⚡ (60-79) - Moderate solutions (50-100 words)
- **Medium** 🎯 (30-59) - Good selection (100-200 words)
- **Easy** ✅ (0-29) - Many solutions (200+ words)

### Game Controls
- **🎲 New Plate** - Generate random plate
- **💡 Hint** - Reveal random unfound solution
- **👁️ Show All** - Reveal all solutions
- **🔄 Continue** - Start new game after completion

## 🛠 Technical Details

### Architecture
- **React 18** with TypeScript
- **Client-side data processing** with pako compression
- **Custom hooks** for game state management
- **Responsive CSS** with modern styling
- **Error boundaries** and loading states

### Data Structure
The game uses pre-generated data (`pl8wrds_complete.json.gz`):
- **Words dictionary**: 103,949 verified English words
- **Plate data**: All possible 3-letter combinations
- **Solutions**: Pre-computed word-plate matches with scores
- **Indexes**: Difficulty ratings and collection metadata

### Performance
- **27MB initial load** (decompressed: ~674MB data)
- **Complete offline gameplay** after data load
- **Optimized storage** with 96% size reduction via deduplication
- **Instant word validation** and scoring

## 📁 Project Structure

```
src/
├── components/          # React components
│   ├── PlateDisplay.tsx    # License plate UI
│   ├── WordInput.tsx       # Word input interface  
│   ├── ScoreBoard.tsx      # Found words & scores
│   ├── GameControls.tsx    # Game action buttons
│   ├── LoadingScreen.tsx   # Data loading UI
│   └── ErrorMessage.tsx    # Error handling UI
├── hooks/
│   └── useGame.ts          # Game state management
├── services/
│   └── gameData.ts         # Data loading & processing
├── types/
│   └── game.ts             # TypeScript type definitions
├── App.tsx                 # Main application
├── App.css                 # Game styling
└── index.js                # React entry point

public/
└── pl8wrds_complete.json.gz # Complete game dataset
```

## 🎨 Customization

### Styling
Edit `src/App.css` to customize:
- Color schemes for difficulty levels
- UI animations and transitions
- Layout and responsive breakpoints

### Game Logic
Modify `src/hooks/useGame.ts` to:
- Change scoring algorithms
- Add new game modes
- Implement achievements

### Data Processing
Update `src/services/gameData.ts` to:
- Add custom plate filtering
- Implement save/load features
- Add multiplayer support

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

### Deployment Notes
- Ensure `public/pl8wrds_complete.json.gz` is served correctly
- Configure server to support gzip compression
- Set appropriate cache headers for the data file
- Test data loading on target deployment environment

## 📊 Game Statistics

- **Total Plates**: 15,715 unique collectibles
- **Total Solutions**: 7,038,012 word-plate combinations  
- **Dictionary Size**: 103,949 verified English words
- **Data Size**: 27MB compressed, 674MB uncompressed
- **Coverage**: 100% of mathematically possible solutions

## 🤝 Development

### Adding New Features
1. Create components in `src/components/`
2. Add types to `src/types/game.ts`
3. Update game logic in `src/hooks/useGame.ts`
4. Style in `src/App.css`

### Common Tasks
- **Add new game modes**: Extend `GameState` and `useGame`
- **Customize scoring**: Modify `calculateScore` in `types/game.ts`
- **Add achievements**: Track progress in `useGame` hook
- **Implement multiplayer**: Add WebSocket support to `gameData.ts`

## 📄 License

MIT License - Perfect for commercial game development.

---

**Ready to play?** Start the game and discover the fascinating world of license plate wordplay!

🎮 *Generated from comprehensive English language analysis with ❤️*