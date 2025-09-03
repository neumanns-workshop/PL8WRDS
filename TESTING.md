# PL8WRDS Testing Framework

This document describes the comprehensive testing framework for the PL8WRDS application.

## Overview

The testing framework is organized into multiple layers to ensure comprehensive coverage of the application:

- **Unit Tests**: Fast, isolated tests for domain logic
- **Integration Tests**: Tests for repository and service integrations
- **API Tests**: FastAPI endpoint testing
- **End-to-End Tests**: Complete user workflow testing
- **Performance Tests**: Load testing and benchmarking

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test configuration and fixtures
├── factories.py                # Test data factories
├── test_settings.py           # Test-specific settings
├── test_container.py          # Dependency injection for tests
├── unit/                      # Unit tests
│   ├── domain/
│   │   ├── test_value_objects.py
│   │   └── test_entities.py
│   └── application/
├── integration/               # Integration tests
│   ├── test_repositories.py
│   └── test_external_services.py
├── api/                      # API tests
│   ├── test_prediction_endpoints.py
│   ├── test_scoring_endpoints.py
│   └── test_solver_endpoints.py
├── e2e/                      # End-to-end tests
│   └── test_word_scoring_journey.py
├── performance/              # Performance tests
│   └── test_api_performance.py
└── mocks/                    # Mock implementations
    ├── external_services.py
    └── repositories.py
```

## Quick Start

### Running Tests

Use the provided test runner script:

```bash
# Run all tests
python run_tests.py --all

# Run specific test categories
python run_tests.py --unit
python run_tests.py --api
python run_tests.py --e2e

# Run fast tests only (unit + api)
python run_tests.py --fast

# Run with verbose output and coverage
python run_tests.py --unit --verbose

# Run performance tests
python run_tests.py --performance
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific categories
pytest -m unit
pytest -m integration
pytest -m api
pytest -m e2e
pytest -m performance

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/domain/test_value_objects.py

# Run specific test
pytest tests/unit/domain/test_value_objects.py::TestWord::test_word_creation_valid
```

## Test Categories and Markers

### Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit`: Fast, isolated unit tests
- `@pytest.mark.integration`: Tests with external dependencies
- `@pytest.mark.api`: FastAPI endpoint tests
- `@pytest.mark.e2e`: End-to-end workflow tests
- `@pytest.mark.performance`: Performance and load tests
- `@pytest.mark.slow`: Tests that take more than a few seconds
- `@pytest.mark.requires_ollama`: Tests requiring Ollama service
- `@pytest.mark.requires_cache`: Tests requiring cache files

### Test Categories

#### Unit Tests
- **Domain Value Objects**: Test immutable domain objects (Word, LicensePlate, Score, etc.)
- **Domain Entities**: Test business entities and their behavior
- **Application Services**: Test application service logic (mocked dependencies)

#### Integration Tests
- **Repositories**: Test data persistence with real file I/O
- **External Services**: Test service implementations with mocked external dependencies
- **Service Integration**: Test interaction between services

#### API Tests
- **Endpoint Testing**: Test HTTP request/response handling
- **Validation Testing**: Test input validation and error handling
- **Authentication/Authorization**: Test security middleware
- **Content Negotiation**: Test different content types and formats

#### End-to-End Tests
- **User Journeys**: Test complete workflows from API calls
- **Error Recovery**: Test error handling across the full stack
- **Data Consistency**: Test data consistency across endpoints

#### Performance Tests
- **Response Time**: Benchmark API response times
- **Concurrent Load**: Test behavior under concurrent requests
- **Memory Usage**: Test memory efficiency with large datasets
- **Scalability**: Test performance with increasing load

## Test Data Management

### Factories

Test data is generated using Factory Boy factories in `tests/factories.py`:

```python
from tests.factories import WordFactory, LicensePlateFactory, WordScoreFactory

# Create test objects
word = WordFactory()
plate = LicensePlateFactory()
score = WordScoreFactory()

# Create with specific values
word = WordFactory(value="ambulance")
```

### Fixtures

Common test objects are available as pytest fixtures in `conftest.py`:

```python
def test_word_scoring(sample_word, sample_plate, sample_score):
    # Test implementation using fixtures
    assert sample_word.matches_plate(sample_plate)
```

### Mock Data

Mock implementations provide predictable test data:

```python
from tests.mocks.external_services import MockLLMClient

mock_client = MockLLMClient()
mock_client.add_model("test-model")
```

## Mocking Strategy

### External Service Mocks

Mock implementations are provided for all external services:

- **MockLLMClient**: Simulates Ollama LLM interactions
- **MockWordSolver**: Provides deterministic word matching
- **MockFeatureExtractor**: Generates predictable features
- **MockModelPredictor**: Simulates ML model predictions
- **MockCacheManager**: In-memory cache for testing

### Repository Mocks

In-memory repository implementations for fast testing:

- **InMemoryWordRepository**: Word data without file I/O
- **InMemoryScoringRepository**: Scoring data in memory
- **InMemoryCorpusRepository**: Corpus data in memory

### Test Container

Dependency injection container with all mocks configured:

```python
from tests.test_container import create_test_container

container = create_test_container()
app.container = container
```

## Configuration

### Test Settings

Test-specific configuration in `tests/test_settings.py`:

- Disabled external services
- In-memory databases
- Reduced logging
- Test-specific file paths

### Environment Variables

Set these environment variables for testing:

```bash
export TESTING=1
export LOG_LEVEL=WARNING
export PYTHONPATH=/path/to/project
```

## Coverage Requirements

- **Minimum Overall Coverage**: 80%
- **Domain Layer Coverage**: 95%+ (critical business logic)
- **API Layer Coverage**: 85%+ (all endpoints)
- **Service Layer Coverage**: 80%+ (application logic)

### Generating Coverage Reports

```bash
# Terminal coverage report
pytest --cov=app --cov-report=term-missing

# HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# XML coverage report (for CI/CD)
pytest --cov=app --cov-report=xml
```

## Performance Testing

### Benchmarking

Performance tests use pytest-benchmark for reliable measurements:

```python
@pytest.mark.benchmark
def test_endpoint_performance(client, benchmark):
    result = benchmark(client.get, "/api/endpoint")
    assert result.status_code == 200
```

### Load Testing

Concurrent request testing:

```python
@pytest.mark.performance
def test_concurrent_requests(client):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [future.result() for future in futures]
```

## Continuous Integration

### GitHub Actions

Example workflow for CI:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py --all
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Pre-commit Hooks

Install pre-commit hooks for automatic testing:

```bash
pip install pre-commit
pre-commit install
```

## Troubleshooting

### Common Issues

1. **ImportError**: Ensure PYTHONPATH includes project root
2. **Fixture not found**: Check `conftest.py` is in correct location
3. **Mock not working**: Verify mock is properly patched
4. **Async test failing**: Use `@pytest.mark.asyncio` decorator

### Debug Mode

Run tests with debugging:

```bash
# Drop into debugger on failure
pytest --pdb

# Run specific test with verbose output
pytest -v tests/path/to/test.py::test_name

# Show test output (disable capture)
pytest -s
```

### Test Data Inspection

Access test data for debugging:

```python
def test_debug_data(sample_word_score):
    import pprint
    pprint.pprint(sample_word_score.__dict__)
    assert False  # Force test to fail and show output
```

## Best Practices

### Writing Tests

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **One Assertion Per Test**: Focus on single behavior
3. **Descriptive Names**: Test names should describe the scenario
4. **Independent Tests**: Tests should not depend on each other
5. **Use Factories**: Generate test data with factories

### Test Organization

1. **Group Related Tests**: Use test classes for related functionality
2. **Separate Concerns**: Unit, integration, and E2E tests in different files
3. **Mock External Dependencies**: Keep tests isolated and fast
4. **Test Edge Cases**: Include boundary conditions and error scenarios

### Performance Considerations

1. **Fast Feedback**: Unit tests should run in milliseconds
2. **Parallel Execution**: Use pytest-xdist for parallel test runs
3. **Resource Cleanup**: Clean up test data and connections
4. **Efficient Fixtures**: Share expensive setup across tests

## Advanced Testing

### Property-Based Testing

Use Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, alphabet=st.characters(whitelist_categories=['L'])))
def test_word_always_valid(word_text):
    word = Word(word_text.lower())
    assert len(word) == len(word_text)
```

### Mutation Testing

Use mutmut for mutation testing:

```bash
pip install mutmut
mutmut run
mutmut results
```

### Contract Testing

Test API contracts with consumers:

```python
def test_api_contract():
    response = client.get("/api/endpoint")
    schema = load_api_schema()
    validate(response.json(), schema)
```

## Maintenance

### Keeping Tests Updated

1. **Update with Code Changes**: Modify tests when behavior changes
2. **Remove Obsolete Tests**: Delete tests for removed functionality
3. **Refactor Test Code**: Apply same quality standards as production code
4. **Update Dependencies**: Keep testing libraries up to date

### Test Metrics

Monitor test suite health:

- **Test Execution Time**: Keep total time under 5 minutes
- **Test Reliability**: Address flaky tests immediately
- **Coverage Trends**: Maintain or improve coverage over time
- **Test Count**: Ensure adequate test count for new features