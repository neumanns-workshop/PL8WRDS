# 🚀 PL8WRDS Quick Start Guide

Get PL8WRDS running in under 5 minutes! Choose your path based on what you want to do.

## 🎯 Choose Your Adventure

### 🎮 I Want to Play the Game
**Fastest path to experiencing PL8WRDS**

```bash
cd pl8wrds-game
npm install
npm start
```

- **Opens**: `http://localhost:3000` 
- **Load time**: ~30 seconds (downloading 27MB game data)
- **Features**: Complete offline game experience with 15k+ plates

**What you get**: Full game with scoring, hints, difficulty ratings, and beautiful UI.

---

### 🔧 I Want to Customize Scoring (Optional)
**For developers who want to modify the scoring algorithms**

```bash
# Install Python dependencies
pip install -r requirements.txt

# Build models (takes ~10 minutes first time)
python rebuild_all_models.py

# Start API server
uvicorn app.main:app --reload
```

**Test it works**:
```bash
# Health check
curl http://localhost:8000/health

# Find words for plate "ABC"
curl http://localhost:8000/solve/ABC
```

---

### 🏗️ I Want to Contribute
**For contributors**

```bash
# Fork and clone repository
git clone https://github.com/YOUR-USERNAME/PL8WRDS.git
cd PL8WRDS

# Start the game
cd pl8wrds-game
npm install
npm start

# Make your changes and test
```

**What you get**: Local development setup for the React game.

---

## ⚡ 30-Second Demo

Want to see PL8WRDS in action immediately?

```bash
# Run the game locally
cd pl8wrds-game
npm install && npm start

# Opens at http://localhost:3000
# Try typing words like "about" for plate "ABC"
```

---

## 🛠️ Prerequisites

### For Playing the Game
- **Node.js 16+** 
- **1GB RAM**

### For API Development (Optional)
- **Python 3.11+**
- **2GB RAM** (for models)

---

## 📋 First Time Setup Checklist

### ✅ Game Setup (2 minutes)
- [ ] Node.js 16+ installed
- [ ] Run `cd pl8wrds-game && npm install`
- [ ] Run `npm start`
- [ ] Open `http://localhost:3000`
- [ ] Wait for game data to load (~30s)
- [ ] Try typing a word for the displayed plate

### ✅ API Setup (5-10 minutes)
- [ ] Python 3.11+ installed OR Docker
- [ ] Clone repository
- [ ] Run `docker-compose up -d` OR manual Python setup
- [ ] Test with `curl http://localhost:8000/health`
- [ ] Try solving a plate: `curl http://localhost:8000/solve/ABC`
- [ ] Check API docs at `http://localhost:8000/docs`

### ✅ Development Setup (10-15 minutes)
- [ ] Docker and Docker Compose installed
- [ ] Repository cloned with `git clone`
- [ ] Run `docker-compose --profile monitoring up -d`
- [ ] Run tests with `python run_tests.py --fast`
- [ ] Check monitoring at `http://localhost:3000` (Grafana)

---

## 🚨 Common Quick Fixes

### Game Won't Load
```bash
# Clear npm cache and reinstall
cd pl8wrds-game
rm -rf node_modules package-lock.json
npm install
npm start
```

### API Returns 500 Errors
```bash
# Models probably not built
python rebuild_all_models.py

# Or use Docker (auto-builds models)
docker-compose up -d
```

### Port Already in Use
```bash
# Find what's using the port
lsof -i :8000  # or :3000 for game

# Kill the process or use different ports
docker-compose up -d  # Uses different ports automatically
```

### Docker Issues
```bash
# Clean Docker cache and rebuild
docker-compose down
docker system prune -f
docker-compose up --build -d
```

---

## 🎯 What's Next?

### After Game Setup ✅
- Try different difficulty levels
- Explore the scoring system
- Challenge friends with specific plates
- Read [Game Mechanics](../GAME_DESIGN.md) for advanced features

### After API Setup ✅
- Explore the [API Documentation](API.md)
- Try the interactive docs at `/docs`
- Read [Architecture Overview](ARCHITECTURE.md)
- Check out [example integrations](../examples/)

### After Development Setup ✅
- Read [Contributing Guidelines](CONTRIBUTING.md)
- Explore the codebase structure
- Run performance tests
- Set up your IDE with the development container

---

## 🆘 Still Stuck?

**Quick Debugging Steps:**
1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Verify prerequisites are installed
3. Check port availability (8000, 3000)
4. Try the Docker approach (often simpler)
5. Open an issue with your specific error

**Get Help:**
- 🐛 [Report bugs](https://github.com/your-username/PL8WRDS/issues)
- 💬 [Ask questions](https://github.com/your-username/PL8WRDS/discussions) 
- 📧 Contact maintainers

---

**⚡ That's it! You should now have PL8WRDS running. Happy word hunting!** 🎮
