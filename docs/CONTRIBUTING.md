# 🤝 Contributing to PL8WRDS

Thank you for your interest in contributing to PL8WRDS! This guide will help you get started with contributing to our license plate word game system.

## 🚀 Quick Start for Contributors

### 1. Set Up Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/PL8WRDS.git
cd PL8WRDS

# Start the game locally
cd pl8wrds-game
npm install
npm start

# Game opens at http://localhost:3000
```

### 2. Make Your First Contribution

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes (focus on the game in pl8wrds-game/)
cd pl8wrds-game
# ... edit React components, add features, fix bugs ...

# Test locally
npm start  # Verify your changes work

# Commit and push
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name

# Create pull request on GitHub
```

---

## 📋 Types of Contributions Welcome

### 🎨 Game Improvements
- UI/UX enhancements
- New game features (hints, achievements, etc.)
- Mobile responsiveness improvements
- Visual design improvements

### 🐛 Bug Fixes
- Game UI problems
- Performance issues
- Mobile compatibility fixes
- Browser compatibility

### ✨ New Features
- Game modes (timed challenges, multiplayer, etc.)
- Player statistics and progress tracking
- Social features (sharing, leaderboards)
- Accessibility improvements

### 📚 Documentation
- Improve setup instructions
- Add game feature documentation
- Create tutorials for players
- Fix documentation errors

---

## 🛠️ Development Setup Guide

### Prerequisites
- **Node.js 16+**
- **Git**
- A code editor (VS Code, etc.)

### Simple Setup
```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/PL8WRDS.git
cd PL8WRDS

# Install and run the game
cd pl8wrds-game
npm install
npm start
```

**Game URL**: http://localhost:3000

### Optional: API Development
Only needed if you want to modify scoring algorithms:
```bash
# Install Python dependencies  
pip install -r requirements.txt

# Build models (takes ~10 minutes)
python rebuild_all_models.py

# Start API
uvicorn app.main:app --reload
```

**API URL**: http://localhost:8000

---

## 🧪 Testing Guidelines

### Game Testing
```bash
# Test the React game
cd pl8wrds-game
npm test

# Build test (make sure it builds)
npm run build
```

### Manual Testing Checklist
- [ ] Game loads without errors
- [ ] Can enter words and get scores
- [ ] Game data loads properly
- [ ] Works on mobile/tablet
- [ ] No console errors

### Optional: API Testing
Only if you're working on scoring:
```bash
# Test the API
python -m pytest tests/ -v
```

---

## 📝 Code Style & Standards

### React/TypeScript Style
- **ESLint**: Configured for React best practices
- **TypeScript**: Strict mode enabled
- **Functional Components**: Use hooks over class components
- **Props Typing**: All props must be properly typed

```bash
# Check linting
cd pl8wrds-game
npm run lint

# Auto-fix issues
npm run lint -- --fix
```

### Code Standards
- **Component Names**: PascalCase (e.g., `GameBoard.tsx`)
- **Hook Names**: Start with `use` (e.g., `useGameState.ts`)
- **Props**: Properly typed interfaces
- **Comments**: Explain complex game logic

### Example Component Style
```typescript
interface PlateDisplayProps {
  letters: string[];
  difficulty: number;
  onPlateSelect?: (plate: string) => void;
}

export const PlateDisplay: React.FC<PlateDisplayProps> = ({ 
  letters, 
  difficulty, 
  onPlateSelect 
}) => {
  const plateString = letters.join('');
  
  const handleClick = () => {
    onPlateSelect?.(plateString);
  };

  return (
    <div className="plate-display" onClick={handleClick}>
      <span className="plate-letters">{plateString}</span>
      <span className="difficulty">{difficulty}/100</span>
    </div>
  );
};
```

---

## 🔄 Pull Request Process

### Before Submitting PR

1. **Test Your Changes**
   ```bash
   cd pl8wrds-game
   npm start  # Make sure game works
   npm run build  # Make sure it builds
   npm run lint  # Check code style
   ```

2. **Create PR**
   - Clear description of what you changed
   - Screenshots for UI changes
   - Test on mobile if relevant

### PR Requirements

✅ **Required:**
- [ ] Game builds and runs without errors
- [ ] No new console errors
- [ ] Code follows existing style
- [ ] Clear description of changes

### Review Process
1. Maintainer reviews the changes
2. Test the game functionality 
3. Merge when approved

---

## 🎯 Focus Areas

### Game Architecture
- **Component-Based**: Reusable React components in `pl8wrds-game/src/components/`
- **Custom Hooks**: Game logic in `pl8wrds-game/src/hooks/`
- **TypeScript**: Strong typing throughout
- **State Management**: React hooks for game state

### File Structure
```
pl8wrds-game/src/
├── components/     # React UI components
├── hooks/          # Game logic hooks
├── services/       # Data loading
├── types/          # TypeScript types
└── utils/          # Helper functions
```

---

## 🆘 Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Check existing issues first**
- **Include screenshots for UI issues**

## 📄 License

By contributing to PL8WRDS, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to PL8WRDS! 🚗💬**

*Every contribution makes the word game better for everyone.*
