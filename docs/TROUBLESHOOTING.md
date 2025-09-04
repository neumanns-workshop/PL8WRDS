# 🔧 PL8WRDS Troubleshooting Guide

Having issues with PL8WRDS? This guide covers the most common problems and their solutions.

## 🚨 Quick Diagnostics

### 30-Second Health Check
```bash
# Check if services are running
curl http://localhost:8000/health  # API health
curl http://localhost:3000         # Game UI (should return HTML)

# Check Docker status
docker-compose ps

# Check logs
docker-compose logs app --tail=20
```

**All Good?** ✅ Skip to specific issues below
**Still Problems?** ❌ Continue with detailed diagnostics

---

## 🎮 Game (Frontend) Issues

### Game Won't Load / Blank Screen

**Symptoms**: White screen, loading forever, or JavaScript errors

**Common Causes & Fixes**:

1. **Node.js Version Issues**
   ```bash
   node --version  # Should be 16+
   npm --version   # Should be 8+
   
   # Update if needed
   nvm install node  # If using nvm
   nvm use node
   ```

2. **Dependencies Problem**
   ```bash
   cd pl8wrds-game
   rm -rf node_modules package-lock.json
   npm cache clean --force
   npm install
   npm start
   ```

3. **Port Conflict**
   ```bash
   # Check what's using port 3000
   lsof -i :3000
   
   # Kill the process or use different port
   npm start -- --port 3001
   ```

4. **Game Data Loading Issues**
   - **Problem**: 27MB game data file not loading
   - **Solution**: Check browser developer tools network tab
   ```bash
   # Verify data file exists
   ls -la pl8wrds-game/public/pl8wrds_complete.json.gz
   
   # Check file size (should be ~27MB)
   du -h pl8wrds-game/public/pl8wrds_complete.json.gz
   ```

### Game Loads But No Plates Appear

**Symptoms**: UI loads but no game content

**Debug Steps**:
1. Open browser developer tools (F12)
2. Check console for errors
3. Check network tab for failed requests

**Common Fixes**:
```bash
# Verify data file is valid
cd pl8wrds-game/public
gzip -t pl8wrds_complete.json.gz  # Should report no errors

# Re-download data file if corrupted
rm pl8wrds_complete.json.gz
# Copy from main directory if available
cp ../../client_game_data/pl8wrds_complete.json.gz .
```

### Slow Performance / Freezing

**Symptoms**: Game is sluggish or freezes during play

**Solutions**:
1. **Check available memory**
   ```bash
   # The 27MB compressed file expands to ~674MB in memory
   # Ensure you have at least 1GB available RAM
   ```

2. **Browser-specific issues**
   - Try different browser (Chrome, Firefox, Safari)
   - Disable browser extensions
   - Clear browser cache

3. **Reduce data load**
   ```javascript
   // In gameData.ts, you can limit loaded plates for testing
   const limitedData = { ...gameData };
   limitedData.plates = gameData.plates.slice(0, 1000); // Load only 1000 plates
   ```

---

## 🔧 API (Backend) Issues

### API Returns 500 Errors

**Symptoms**: All API calls return Internal Server Error

**Most Common Cause**: Models not built

**Fix**:
```bash
# Option 1: Build models manually
python rebuild_all_models.py

# Option 2: Use Docker (auto-builds)
docker-compose up -d

# Option 3: Check if models exist
ls -la models/
# Should see: information_model.json (~655MB), orthographic_model.json (~310KB)
```

### API Returns "Word not found in corpus"

**Symptoms**: Valid words return not found errors

**Debugging**:
```bash
# Check corpus file exists and has content
ls -la data/words_with_freqs.json  # Should be ~8.5MB

# Verify corpus is loading
python -c "
from app.services.word_service import word_service
print(f'Corpus size: {len(word_service.words)}')
print(f'Sample words: {list(word_service.words.keys())[:10]}')
"
```

**Fix if corpus is empty**:
```bash
# Download/rebuild corpus
python clean_corpus.py  # If available
# Or regenerate from original sources
```

### API Slow Response Times (>1 second)

**Symptoms**: API calls take very long to respond

**Diagnostics**:
```bash
# Test specific endpoints
time curl "http://localhost:8000/solve/ABC"
time curl -X POST "http://localhost:8000/predict/ensemble" \
  -H "Content-Type: application/json" \
  -d '{"word": "about", "plate": "ABC"}'
```

**Common Causes & Fixes**:

1. **Large Model Loading**
   - Information model (655MB) loads on first request
   - **Solution**: Warm up the service or use model caching

2. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats pl8wrds-app  # If using Docker
   
   # Or system memory
   free -h  # Linux
   vm_stat  # macOS
   ```

3. **CPU Intensive Operations**
   ```bash
   # Check CPU usage during requests
   htop  # or top
   ```

### Port Conflicts

**Symptoms**: "Port already in use" errors

**Fix**:
```bash
# Check what's using the port
lsof -i :3000  # Game port
lsof -i :8000  # API port (if using)

# Kill the process or use different port
npm start -- --port 3001  # Use port 3001 instead
```

---

## 💾 Data & Model Issues

### Models Take Forever to Build

**Symptoms**: `python rebuild_all_models.py` runs for hours

**Expected Times**:
- Information model: 2-3 minutes
- Orthographic model: 5-10 minutes  
- **Total: ~10 minutes on modern hardware**

**If taking longer**:
```bash
# Check system resources
htop  # CPU usage should be high during build

# Check progress (look for progress messages)
python rebuild_all_models.py | tee build.log

# For very slow systems, consider using pre-built models
# (if available from project releases)
```

### Corpus Stats Show Wrong Numbers

**Symptoms**: API reports unexpected word counts or statistics

**Debugging**:
```bash
# Check corpus health
python -c "
import json
with open('data/words_with_freqs.json', 'r') as f:
    data = json.load(f)
print(f'Total words: {len(data)}')
print(f'Sample entries: {data[:5]}')

# Check for duplicates
words = [item['word'] for item in data]
print(f'Unique words: {len(set(words))}')
"
```

**Expected Numbers**:
- **Total words**: 103,949
- **All words unique**: No duplicates
- **Frequency range**: 1 to 4,764,010

### Cache Files Corrupted

**Symptoms**: Errors about JSON parsing or invalid cache

**Fix**:
```bash
# Clear all cache files
rm -f cache/*.json

# Regenerate cache
curl http://localhost:8000/corpus/stats  # Will rebuild cache
```

---

## 🐳 Docker-Specific Issues

### Container Builds But Exits Immediately

**Check Logs**:
```bash
docker-compose logs app
docker-compose logs redis
```

**Common Issues**:

1. **Missing Data Files**
   ```bash
   # Ensure data directory exists with required files
   mkdir -p data models cache
   touch data/words_with_freqs.json
   echo '{}' > cache/corpus_stats.json
   ```

2. **Python Import Errors**
   ```bash
   # Test Python environment in container
   docker-compose exec app python -c "from app.main import app; print('OK')"
   ```

3. **File Permissions**
   ```bash
   # Fix ownership for Docker
   sudo chown -R 1000:1000 . # Use your user ID
   ```

### Docker Compose Profiles Not Working

**Symptoms**: Services don't start with profiles

**Fix**:
```bash
# Correct syntax for profiles
docker-compose --profile monitoring up -d
docker-compose --profile database --profile monitoring up -d

# Check which services are defined for profiles
docker-compose config --profiles
```

---

## 🔒 Security & Permission Issues

### Permission Denied Errors

**In Docker**:
```bash
# Fix container permissions
sudo chown -R 1000:1000 ./data ./cache ./models
chmod -R 755 ./data ./cache ./models
```

**Native Python**:
```bash
# Fix local permissions
chown -R $USER:$USER .
chmod -R 755 .
```

### CORS Errors in Browser

**Symptoms**: Browser blocks API requests

**Fix**:
```bash
# Check API CORS settings in app/core/config.py
# Should include your frontend URL

# For development, temporarily allow all origins
export CORS_ORIGINS="*"
```

---

## 🚀 Performance Issues

### High Memory Usage

**Symptoms**: System runs out of memory

**Memory Requirements**:
- **Game Only**: 1GB RAM
- **API Only**: 2GB RAM (models)
- **Full Development**: 4GB+ RAM

**Optimizations**:
```bash
# Use production Docker image (smaller)
docker build --target production -t pl8wrds:prod .

# Reduce Docker memory limits
# Add to docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

### Slow Startup Times

**Causes & Solutions**:

1. **Model Loading**
   - Information model (655MB) takes time to load
   - **Solution**: Use model caching or lazy loading

2. **Docker Image Size**
   ```bash
   # Use smaller base images
   # Check image sizes
   docker images | grep pl8wrds
   
   # Use multi-stage builds (already implemented)
   ```

---

## 🌐 Network Issues

### Can't Reach Services

**Check Network**:
```bash
# Test local connectivity
ping localhost
curl http://localhost:8000/health

# Check Docker network
docker network ls
docker-compose exec app ping redis
```

### Proxy/Firewall Issues

**Corporate Networks**:
- May block Docker registry access
- May block certain ports
- **Solution**: Configure proxy settings or use alternative deployment

---

## 📊 Development Issues

### Tests Failing

**Run Diagnostics**:
```bash
# Check test environment
python run_tests.py --verbose

# Run specific failing test
pytest tests/specific_test.py -v -s

# Check test dependencies
pip list | grep -E "(pytest|test)"
```

**Common Test Issues**:
1. **Missing test data**: Ensure test fixtures are available
2. **Port conflicts**: Tests may conflict with running services
3. **Environment isolation**: Use proper test settings

### IDE/Editor Issues

**Python Path Issues**:
```bash
# Set PYTHONPATH
export PYTHONPATH=/path/to/PL8WRDS:$PYTHONPATH

# Or in your IDE settings, add project root to Python path
```

**Import Resolution**:
- Ensure your IDE recognizes the project structure
- Configure Python interpreter to use project venv

---

## 🆘 Last Resort Solutions

### Nuclear Options (When All Else Fails)

1. **Complete Reset**
   ```bash
   # Stop everything
   docker-compose down
   
   # Clean Docker completely
   docker system prune -a --volumes
   
   # Remove local data
   rm -rf cache/* models/* 
   
   # Start fresh
   docker-compose up --build -d
   ```

2. **Fresh Environment**
   ```bash
   # Create new directory
   cd /tmp
   git clone <repo-url> pl8wrds-fresh
   cd pl8wrds-fresh
   
   # Try setup in clean environment
   docker-compose up -d
   ```

---

## 🌐 Netlify Deployment Issues

### Build Fails on Netlify

**Symptoms**: Netlify build process fails

**Common Fixes**:
```bash
# Check build settings in Netlify dashboard:
# Build command: npm run build
# Publish directory: build
# Node version: 16 or higher
```

### Game Loads But Data Won't Load

**Symptoms**: Game UI loads but plates/data don't appear

**Fix**: Ensure `pl8wrds_complete.json.gz` is in the `public/` folder:
```bash
# Verify data file exists
ls -la pl8wrds-game/public/pl8wrds_complete.json.gz

# Should be ~27MB
```

### Custom Domain Issues

**Symptoms**: `pl8wrds.gbe.games` doesn't work

**Fix**: Configure DNS in Netlify:
1. Go to Netlify site settings
2. Domain management > Add custom domain
3. Add `pl8wrds.gbe.games`
4. Configure DNS records as Netlify shows

### Deploy Preview Issues

**Symptoms**: Deploy previews don't work correctly

**Fix**: Check environment variables and paths are relative, not absolute.

---

## 📞 Getting Help

### Before Asking for Help

✅ **Provide This Information**:
- **Operating System**: macOS/Linux/Windows + version
- **Python Version**: `python --version`
- **Node Version**: `node --version` (if game issues)
- **Docker Version**: `docker --version`
- **Error Messages**: Full error text
- **What You Were Trying**: Exact commands/actions
- **What Happened**: Detailed symptoms
- **Logs**: Relevant log excerpts

### Where to Get Help

1. **Check Documentation**: Review relevant docs first
2. **Search Issues**: Look for similar problems
3. **Create Issue**: With all required information
4. **Community Discussion**: For general questions

### Issue Template
```markdown
**Problem Description**
Brief description of what's not working

**Environment**
- OS: 
- Python Version:
- Docker Version:
- Installation Method:

**Steps to Reproduce**
1. First do this
2. Then do that
3. Error occurs

**Expected Behavior**
What should have happened

**Actual Behavior** 
What actually happened

**Error Messages**
```
Full error text here
```

**Additional Context**
Any other relevant information
```

---

**Still stuck? Don't hesitate to ask for help! 🤝**

The PL8WRDS community is here to help you get up and running.
