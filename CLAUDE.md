# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PL8WRDS is a license plate word game system with two main components:
1. **React Frontend** (`pl8wrds-game/`) - Complete client-side word game with 15,715+ collectible plates
2. **FastAPI Backend** (`app/`) - Optional API for scoring algorithms and customization

The game features real ensemble scoring (Vocabulary + Information + Orthography) with pre-computed scores for 7+ million English word solutions.

## Common Development Commands

### Frontend (React Game) - Primary Development Target
```bash
# Start development server
cd pl8wrds-game
npm start  # Opens http://localhost:3000

# Build for production
npm run build

# Run tests
npm test
npm run test:coverage  # With coverage report
npm run test:ci        # CI mode

# Code quality
npm run lint           # Check linting
npm run lint:fix       # Auto-fix linting issues
npm run format         # Format code with Prettier
npm run format:check   # Check formatting
npm run type-check     # TypeScript type checking

# Bundle analysis
npm run analyze        # Analyze bundle size
npm run analyze:bundle # Detailed bundle analysis
```

### Backend (FastAPI API) - Optional
```bash
# Development server
uvicorn app.main:app --reload  # Opens http://localhost:8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Testing
python -m pytest                    # Run all tests
python -m pytest tests/ -v         # Verbose output
python -m pytest --cov=app         # With coverage
python -m pytest -k "test_name"    # Specific test

# Code quality  
ruff .                    # Lint with Ruff
ruff --fix .             # Auto-fix issues
black .                  # Format with Black
mypy .                   # Type checking
bandit -r app/           # Security scanning

# Pre-commit hooks
pre-commit run --all-files
```

### Development Dependencies
```bash
# Install all development dependencies
pip install -e ".[dev]"     # Backend dev dependencies
cd pl8wrds-game && npm install  # Frontend dependencies
```

## Architecture Overview

### Dual Architecture Pattern
This project uses a **dual architecture** approach:

1. **Client-Side Complete**: The React game (`pl8wrds-game/`) is fully self-contained with pre-computed game data (~27MB)
2. **Optional API**: The FastAPI backend (`app/`) provides advanced customization and can regenerate scoring models

### Backend Architecture (FastAPI)
- **Clean Architecture**: Domain → Application → Infrastructure layers
- **Dependency Injection**: Using `dependency-injector` for IoC
- **Monitoring Stack**: OpenTelemetry + Prometheus + Sentry
- **Error Handling**: Structured error responses with proper HTTP codes
- **Configuration**: Environment-based settings with Pydantic

Key directories:
```
app/
├── core/                  # Configuration, DI container, error handlers  
├── domain/               # Business entities and value objects
├── application/          # Use cases and service interfaces
├── infrastructure/       # External service implementations
├── routers/              # FastAPI route handlers
├── services/             # Business logic services
└── monitoring/           # Observability and health checks
```

### Frontend Architecture (React)
- **Component-Based**: Reusable React components in TypeScript
- **Custom Hooks**: Game logic separated into custom hooks
- **Client-Side Data**: Pre-loaded game data with compression (pako/gzip)
- **State Management**: React hooks for game state (no external state library)

Key directories:
```
pl8wrds-game/src/
├── components/           # React UI components
├── hooks/               # Game logic hooks  
├── services/            # Data loading and API calls
├── types/               # TypeScript type definitions
└── utils/               # Helper functions
```

### Data Architecture
- **Pre-computed Scoring**: All ensemble scores calculated offline for performance
- **Split Storage**: Word properties separate from plate-specific context scores
- **Efficient Format**: `{word_id: info_score}` mapping with shared dictionary
- **Compression**: Gzip compression reduces ~25MB data to practical size

### Scoring System (3-Dimensional Ensemble)
1. **Vocabulary Score** (0-100): Corpus frequency and word rarity
2. **Information Score** (0-100): Context-dependent plate-word relationships  
3. **Orthographic Score** (0-100): Letter pattern complexity
4. **Ensemble Score**: Simple average of all three components

## Key Configuration Files

- `pyproject.toml` - Python project config with extensive tool configurations
- `pl8wrds-game/package.json` - React app dependencies and scripts
- `.pre-commit-config.yaml` - Pre-commit hooks for code quality
- `requirements.txt` - Python production dependencies

## Development Workflow

### Working on the Game (Most Common)
1. Focus on `pl8wrds-game/` directory
2. Use `npm start` for development server
3. Game loads pre-built data automatically
4. Test changes in browser at localhost:3000

### Working on Scoring/API
1. Install Python dependencies: `pip install -r requirements.txt`
2. Build models if needed: `python rebuild_all_models.py`
3. Start API: `uvicorn app.main:app --reload`
4. API available at localhost:8000

### Code Quality Standards
- **Python**: Ruff + Black + MyPy + Bandit (configured in pyproject.toml)
- **React**: ESLint + Prettier + TypeScript strict mode
- **Pre-commit hooks**: Automatically run quality checks
- **Testing**: pytest for backend, React Testing Library for frontend

### Testing Strategy
- **Backend**: Unit tests with pytest, 80% coverage requirement
- **Frontend**: Component tests with React Testing Library, 80% coverage requirement  
- **Integration**: FastAPI TestClient for API endpoints
- **Performance**: Benchmark tests for scoring algorithms

## Important Notes

### Data Handling
- Game data is pre-computed and should not be regenerated casually
- The `ultra_fast_final_scoring.py` script generates the complete dataset
- Client game loads compressed data automatically

### Performance Considerations  
- Frontend uses lazy loading for large datasets
- Backend implements caching for expensive operations
- Pre-computed scores eliminate runtime ML inference

### Security
- API includes rate limiting, security headers, and input validation
- Frontend sanitizes all user inputs
- No sensitive data should be committed to repository

### Deployment
- **Frontend**: Build with `npm run build`, deploy to static hosting (Netlify recommended)
- **Backend**: Docker-ready with comprehensive monitoring and health checks
- **Environment**: Separate configurations for dev/staging/production