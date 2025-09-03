# PL8WRDS Architecture Refactor

## Overview

The PL8WRDS FastAPI application has been comprehensively refactored to implement Clean Architecture principles with Domain-Driven Design (DDD). This document outlines the changes, benefits, and migration path.

## Architecture Changes

### Before: Monolithic Service Layer
- Services mixed within routers (corpus.py contained service classes)
- Dangerous sys.path manipulation for imports
- Singleton pattern abuse (word_service.py)
- Hardcoded file paths throughout the codebase
- No dependency injection
- Services with mixed responsibilities
- Tight coupling between layers

### After: Clean Architecture with DDD

#### 1. Domain Layer (`app/domain/`)
**Pure business logic without external dependencies**
- **Entities** (`entities.py`): Core business objects with identity
  - `WordMatch`, `WordScore`, `ScoringSession`, `CorpusStatistics`, etc.
- **Value Objects** (`value_objects.py`): Immutable objects representing concepts
  - `Word`, `LicensePlate`, `Score`, `Frequency`, `ModelName`, etc.

#### 2. Application Layer (`app/application/`)
**Use cases and application services**
- **Interfaces** (`interfaces.py`): Abstractions for external services
  - `LLMClient`, `FeatureExtractor`, `ModelPredictor`, `WordSolver`, etc.
- **Use Cases** (`use_cases.py`): High-level business operations
  - `ScoreWordUseCase`, `PredictWordScoreUseCase`, `FindWordsForPlateUseCase`, etc.
- **Services** (`services.py`): Coordinate use cases and provide high-level API
  - `WordScoringService`, `WordDiscoveryService`, `CorpusManagementService`, etc.

#### 3. Infrastructure Layer (`app/infrastructure/`)
**External concerns and implementations**
- **Repositories** (`repositories.py`): Data access implementations
  - `JsonWordRepository`, `JsonScoringRepository`, `JsonCorpusRepository`
- **External Services** (`external_services.py`): Service implementations
  - `OllamaLLMClient`, `SimpleWordSolver`, `JoblibModelPredictor`, etc.

#### 4. Core Layer (`app/core/`)
**Configuration and cross-cutting concerns**
- **Configuration** (`config.py`): Centralized settings using Pydantic
- **Container** (`container.py`): Dependency injection setup

#### 5. API Layer (`app/routers/`)
**HTTP endpoints using dependency injection**
- Clean routers that depend on application services
- No business logic in controllers
- Proper error handling and response formatting

## Key Improvements

### 1. Separation of Concerns
- **Domain**: Pure business logic
- **Application**: Use cases and orchestration
- **Infrastructure**: External dependencies
- **API**: HTTP concerns only

### 2. Dependency Injection
- Uses `dependency-injector` for proper DI
- Eliminates singleton pattern abuse
- Makes testing easier with mockable dependencies
- Configurable service implementations

### 3. Configuration Management
- Centralized configuration with Pydantic Settings
- Environment variable support
- Path management with proper abstractions
- Type-safe configuration access

### 4. Repository Pattern
- Abstract data access behind interfaces
- Easy to swap implementations (JSON -> Database)
- Proper domain object mapping
- Async-first design

### 5. Clean Imports
- Eliminated dangerous `sys.path` manipulation
- Safe dynamic imports where needed
- Proper module structure
- Clear dependency direction

### 6. Type Safety
- Full type hints throughout the codebase
- Domain objects enforce business rules
- Compile-time error detection
- Better IDE support

### 7. Testability
- Dependency injection enables easy mocking
- Pure domain logic is easily testable
- Use cases can be tested in isolation
- Infrastructure concerns are abstracted

## Migration Guide

### Dependencies
Added new dependencies:
```bash
pip install pydantic-settings>=2.0.0 dependency-injector>=4.41.0
```

### Configuration
The application now uses centralized configuration. Environment variables can be prefixed with `PL8WRDS_`:

```bash
# Example environment variables
PL8WRDS_DEBUG=true
PL8WRDS_DATA_DIRECTORY=/custom/data/path
PL8WRDS_OLLAMA_BASE_URL=http://localhost:11434
```

### Service Usage
Instead of importing singleton services directly:

**Before:**
```python
from app.services.word_service import word_service
frequency = word_service.lookup_word("ambulance")
```

**After:**
```python
# In routers, use dependency injection
@inject
async def some_endpoint(
    word_service: WordDiscoveryService = Depends(Provide[Container.word_discovery_service])
):
    frequency = await word_service.get_word_frequency("ambulance")
```

### Router Changes
Routers now use application services instead of containing business logic:

**Before:**
```python
# Business logic mixed in router
class CorpusStatsService:
    # Service class defined in router file
    pass
```

**After:**
```python
# Clean router with injected dependencies
@inject
async def get_stats(
    corpus_service: CorpusManagementService = Depends(Provide[Container.corpus_management_service])
):
    return await corpus_service.get_corpus_statistics()
```

### Error Handling
Domain objects now enforce business rules:

```python
# Value objects validate input
word = Word("ambulance")  # ✓ Valid
word = Word("123")        # ✗ Raises ValueError

plate = LicensePlate("ABC")  # ✓ Valid  
plate = LicensePlate("123")  # ✗ Raises ValueError
```

## File Structure

```
app/
├── core/                   # Configuration and DI
│   ├── __init__.py
│   ├── config.py          # Pydantic settings
│   └── container.py       # DI container
├── domain/                # Pure business logic
│   ├── __init__.py
│   ├── entities.py        # Business entities
│   └── value_objects.py   # Value objects
├── application/           # Use cases and services
│   ├── __init__.py
│   ├── interfaces.py      # Service abstractions
│   ├── use_cases.py       # Business use cases
│   └── services.py        # Application services
├── infrastructure/        # External concerns
│   ├── __init__.py
│   ├── repositories.py    # Data access implementations
│   └── external_services.py # Service implementations
├── routers/               # HTTP endpoints
│   └── ... (existing routers, now using DI)
├── models/                # Pydantic models (API layer)
│   └── ... (existing models)
└── main.py               # Application entry point
```

## Benefits

### 1. Maintainability
- Clear separation of concerns
- Easier to locate and modify code
- Reduced coupling between components
- Self-documenting architecture

### 2. Testability
- Easy to mock dependencies
- Test business logic in isolation
- Integration tests at proper boundaries
- Faster test execution

### 3. Flexibility
- Easy to swap implementations
- Support for multiple data stores
- Configurable external services
- Environment-specific behavior

### 4. Scalability
- Clean dependency direction
- Easy to add new features
- Proper abstraction layers
- Support for different deployment scenarios

### 5. Security
- Eliminated dangerous import patterns
- Proper input validation
- Centralized configuration
- Clear trust boundaries

## Migration Checklist

- [x] ✅ Create domain layer with entities and value objects
- [x] ✅ Implement repository pattern for data access
- [x] ✅ Create application layer with use cases and services
- [x] ✅ Set up dependency injection container
- [x] ✅ Create centralized configuration system
- [x] ✅ Refactor main.py to use DI container
- [x] ✅ Extract services from corpus router
- [x] ✅ Create new corpus router using application services
- [x] ✅ Update FastAPI to use modern lifespan events
- [ ] 🔄 Refactor remaining routers (scoring, prediction, etc.)
- [ ] 🔄 Implement proper feature extraction service
- [ ] 🔄 Add comprehensive tests for new architecture
- [ ] 🔄 Update remaining legacy services
- [ ] 🔄 Add database support (PostgreSQL/SQLite)

## Next Steps

### 1. Complete Router Migration
Refactor remaining routers to use the new application services:
- `scoring.py` - Use `WordScoringService`
- `prediction.py` - Use `PredictionService` 
- `solver.py` - Use `WordDiscoveryService`
- Other routers as needed

### 2. Implement Missing Services
- Complete `FeatureExtractor` implementation
- Enhance `ModelPredictor` with actual ML model loading
- Improve `LLMClient` error handling and retries

### 3. Add Database Support
- Create database repositories (PostgreSQL/SQLite)
- Add proper migrations
- Implement connection pooling

### 4. Testing Strategy
- Unit tests for domain entities and use cases
- Integration tests for repositories and external services  
- API tests for routers
- Performance tests for critical paths

### 5. Monitoring and Observability
- Add structured logging
- Implement metrics collection
- Add health checks for all services
- Monitor resource usage

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all new dependencies are installed
2. **Configuration Issues**: Check environment variables and file paths
3. **DI Container Errors**: Verify all services are properly registered
4. **Missing Files**: Ensure data files exist in configured paths

### Development Tips

1. Use the new health check endpoint: `GET /health`
2. Check service initialization in startup logs
3. Use dependency injection for all service access
4. Follow the established patterns when adding new features

This refactoring establishes a solid foundation for the PL8WRDS application that will support future growth and maintainability.