# 🚀 PL8WRDS Setup Guide

Simple setup guide for getting PL8WRDS running locally or deploying to Netlify.

## 🎮 Play the Game Locally

```bash
cd pl8wrds-game
npm install
npm start
```

Opens at `http://localhost:3000`. Game data loads automatically (~30 seconds).

## 🌐 Deploy to Netlify

### Option 1: Netlify CLI (Recommended)
```bash
cd pl8wrds-game
npm run build
netlify deploy --prod --dir=build
```

### Option 2: Connect Git Repository
1. Push code to GitHub/GitLab
2. Connect repository in Netlify dashboard
3. Set build command: `npm run build`
4. Set publish directory: `build`
5. Deploy!

**Custom domain**: Configure `pl8wrds.gbe.games` in Netlify DNS settings

## 🔧 Optional: API Development

Only needed if you want to modify scoring algorithms:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build models (takes ~10 minutes first time)
python rebuild_all_models.py

# Start API server
uvicorn app.main:app --reload
```

**API runs at**: `http://localhost:8000`

## 🚨 Troubleshooting

### Game won't load
```bash
# Clear cache and reinstall
cd pl8wrds-game
rm -rf node_modules package-lock.json
npm install
npm start
```

### "Models not found" (API only)
```bash
# Rebuild models
python rebuild_all_models.py
```

### Port conflicts
```bash
# Use different ports
npm start -- --port 3001  # Frontend
uvicorn app.main:app --port 8001  # API
```

## 📁 What's What

- **`pl8wrds-game/`** - React game (this is what you deploy)
- **`app/`** - Python API (optional, for scoring customization)
- **`client_game_data/`** - Pre-built game data files
- **Everything else** - Development tools and documentation

---

**That's it! 🎯 Simple setup for a simple game.**
