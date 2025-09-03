# CI/CD Pipeline Guide for PL8WRDS

This comprehensive guide covers the CI/CD pipeline setup for the PL8WRDS FastAPI application, including development workflows, deployment strategies, and best practices.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Pipeline Components](#pipeline-components)
4. [Environment Setup](#environment-setup)
5. [Docker Configuration](#docker-configuration)
6. [GitHub Actions Workflows](#github-actions-workflows)
7. [Security & Quality Gates](#security--quality-gates)
8. [Deployment Strategies](#deployment-strategies)
9. [Monitoring & Observability](#monitoring--observability)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

## Overview

The PL8WRDS CI/CD pipeline provides:

- **Automated Testing**: Unit, integration, API, and E2E tests
- **Code Quality**: Linting, formatting, and type checking
- **Security Scanning**: Vulnerability detection and dependency auditing
- **Performance Testing**: Load testing and benchmarking
- **Multi-Environment Deployment**: Development, staging, and production
- **Container Management**: Docker images with multi-stage builds
- **Release Management**: Automated versioning and GitHub releases

### Pipeline Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Code Commit   │───▶│  Quality Checks  │───▶│  Build & Test   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Deploy Prod   │◀───│ Security Scans   │◀───│  Performance    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Prerequisites

### Required Tools

- **Git**: Version control
- **Docker**: Container runtime
- **Docker Compose**: Multi-container orchestration
- **Python 3.11+**: Development environment
- **GitHub Account**: Repository hosting and CI/CD

### Optional Tools

- **kubectl**: Kubernetes deployment
- **Helm**: Kubernetes package management
- **Terraform**: Infrastructure as code
- **Ansible**: Configuration management

### Repository Secrets

Configure these secrets in your GitHub repository settings:

```bash
# Container Registry
GITHUB_TOKEN                 # GitHub Container Registry access

# Production Environment
SECRET_KEY                   # Application secret key
API_KEY                      # API authentication key
POSTGRES_PASSWORD           # Database password
REDIS_PASSWORD              # Redis password
OPENAI_API_KEY              # OpenAI API key (if used)

# Deployment
SSH_PRIVATE_KEY             # Server SSH key (if using SSH deployment)
KUBECONFIG                  # Kubernetes config (if using K8s)

# Notifications (Optional)
SLACK_WEBHOOK               # Slack notifications
ALERT_EMAIL                 # Email alerts
```

## Environment Setup

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/PL8WRDS.git
   cd PL8WRDS
   ```

2. **Set up environment**:
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit environment variables
   vim .env
   ```

3. **Start development environment**:
   ```bash
   # Using Docker Compose (recommended)
   docker-compose up -d
   
   # Or using Python virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   uvicorn app.main:app --reload
   ```

4. **Verify setup**:
   ```bash
   # Check API health
   curl http://localhost:8000/health
   
   # View API documentation
   open http://localhost:8000/docs
   ```

### Environment Files

The project includes multiple environment configurations:

- **`.env.example`**: Template with all available options
- **`.env.development`**: Local development settings
- **`.env.staging`**: Staging environment configuration
- **`.env.production`**: Production environment settings
- **`.env.testing`**: CI/CD testing configuration

### Docker Profiles

Use Docker Compose profiles for different setups:

```bash
# Development (default)
docker-compose up -d

# With database
docker-compose --profile database up -d

# With monitoring
docker-compose --profile monitoring up -d

# With proxy
docker-compose --profile proxy up -d

# Testing environment
docker-compose --profile testing up -d

# Load testing
docker-compose --profile load-testing up -d
```

## Docker Configuration

### Multi-Stage Dockerfile

The Dockerfile uses multi-stage builds for optimization:

1. **Base**: Common Python setup
2. **Builder**: Compile dependencies
3. **Runtime**: Production runtime
4. **Development**: Development tools
5. **Testing**: Testing environment
6. **Production**: Final optimized image

### Building Images

```bash
# Development image
docker build --target development -t pl8wrds:dev .

# Production image
docker build --target production -t pl8wrds:prod .

# Testing image
docker build --target testing -t pl8wrds:test .
```

### Image Size Optimization

- Multi-stage builds reduce final image size
- Non-root user for security
- Minimal base images (Python slim)
- Layer caching optimization
- .dockerignore for excluding unnecessary files

## GitHub Actions Workflows

### 1. Main CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

**Triggers**: Push to `main`/`develop`, Pull requests

**Stages**:
- **Code Quality**: Linting, formatting, type checking
- **Security**: Vulnerability scanning, secret detection
- **Testing**: Unit, integration, API tests
- **Build**: Docker image creation
- **Deploy**: Environment-specific deployments

**Key Features**:
- Matrix testing across Python versions
- Parallel job execution
- Artifact collection
- Environment-specific deployments
- Notification system

### 2. Security Scanning (`.github/workflows/security.yml`)

**Triggers**: Daily schedule, Push, Pull requests

**Components**:
- **Dependency Scanning**: Safety, pip-audit
- **Code Security**: Bandit, Semgrep
- **Secret Detection**: TruffleHog, GitLeaks
- **Container Security**: Trivy scanning
- **SAST**: CodeQL analysis
- **License Compliance**: License checking

### 3. Performance Testing (`.github/workflows/performance.yml`)

**Triggers**: Pull requests, Daily schedule

**Tests**:
- **API Performance**: Pytest benchmarks
- **Load Testing**: Locust-based testing
- **Memory Profiling**: Memory usage analysis
- **CPU Profiling**: Performance profiling
- **Regression Detection**: Performance comparison

### 4. Release Management (`.github/workflows/release.yml`)

**Triggers**: Version tags, Manual dispatch

**Process**:
- **Version Management**: Automated versioning
- **Changelog Generation**: Commit-based changelog
- **Asset Building**: Source and binary distributions
- **GitHub Release**: Automated release creation
- **Deployment**: Production deployment
- **Notification**: Release notifications

## Security & Quality Gates

### Code Quality Gates

1. **Linting**: Ruff for Python linting
2. **Formatting**: Black for code formatting
3. **Type Checking**: MyPy for static type analysis
4. **Import Sorting**: Ruff for import organization
5. **Security**: Bandit for security issue detection

### Quality Thresholds

- **Test Coverage**: 80% minimum
- **Performance**: No regression > 20%
- **Security**: Zero high-severity vulnerabilities
- **Code Quality**: All linting checks must pass

### Branch Protection Rules

Configure these in GitHub repository settings:

```yaml
# Required status checks
required_status_checks:
  - "Code Quality"
  - "Test Suite"
  - "Security Scan"
  - "API Tests"

# Additional protections
dismiss_stale_reviews: true
require_code_owner_reviews: true
required_approving_review_count: 1
```

## Deployment Strategies

### Development Deployment

- **Trigger**: Push to `develop` branch
- **Environment**: Development/staging server
- **Features**: Latest features, debugging enabled
- **Rollback**: Automatic on failure

### Production Deployment

- **Trigger**: Push to `main` branch or release tag
- **Environment**: Production server
- **Features**: Stable releases only
- **Strategy**: Blue-green or rolling deployment
- **Rollback**: Manual approval required

### Deployment Methods

#### 1. Docker-based Deployment

```bash
# Pull latest image
docker pull ghcr.io/username/pl8wrds:latest

# Stop existing container
docker-compose -f docker-compose.prod.yml down

# Start new container
docker-compose -f docker-compose.prod.yml up -d
```

#### 2. Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pl8wrds-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pl8wrds-api
  template:
    metadata:
      labels:
        app: pl8wrds-api
    spec:
      containers:
      - name: api
        image: ghcr.io/username/pl8wrds:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
```

#### 3. Cloud Platform Deployment

**AWS ECS**:
```json
{
  "family": "pl8wrds-api",
  "containerDefinitions": [{
    "name": "api",
    "image": "ghcr.io/username/pl8wrds:latest",
    "memory": 512,
    "cpu": 256,
    "essential": true,
    "portMappings": [{
      "containerPort": 8000,
      "protocol": "tcp"
    }]
  }]
}
```

**Google Cloud Run**:
```bash
gcloud run deploy pl8wrds-api \
  --image ghcr.io/username/pl8wrds:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Monitoring & Observability

### Health Checks

The application provides comprehensive health checks:

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check with dependencies
curl http://localhost:8000/health/detailed
```

### Metrics Collection

**Prometheus Integration**:
- Application metrics
- Request/response metrics
- Performance metrics
- Error rates

**Grafana Dashboards**:
- API performance overview
- Error tracking
- Resource utilization
- User activity

### Logging

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()
logger.info("Request processed", 
           request_id="123", 
           duration=0.5, 
           status_code=200)
```

**Log Aggregation**:
- Centralized logging with JSON format
- Log rotation and retention policies
- Error alerting and notification

### Alerting

**Prometheus Alertmanager Rules**:
```yaml
groups:
- name: pl8wrds-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
    annotations:
      summary: High error rate detected
```

## Troubleshooting

### Common Issues

#### 1. Build Failures

**Dependency Issues**:
```bash
# Clear pip cache
pip cache purge

# Reinstall dependencies
pip install --no-cache-dir -r requirements.txt

# Update dependencies
pip-compile --upgrade requirements.in
```

**Docker Build Issues**:
```bash
# Clear Docker cache
docker system prune -a

# Build with no cache
docker build --no-cache -t pl8wrds:latest .

# Check build context
docker build --progress=plain -t pl8wrds:latest .
```

#### 2. Test Failures

**Environment Issues**:
```bash
# Check environment variables
printenv | grep PL8WRDS

# Reset test database
docker-compose exec postgres psql -U pl8wrds -c "DROP DATABASE IF EXISTS pl8wrds_test; CREATE DATABASE pl8wrds_test;"

# Clear test cache
rm -rf .pytest_cache
```

**Coverage Issues**:
```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage details
open htmlcov/index.html
```

#### 3. Deployment Issues

**Container Issues**:
```bash
# Check container logs
docker-compose logs app

# Check container health
docker-compose ps

# Debug container
docker-compose exec app bash
```

**Network Issues**:
```bash
# Check port availability
netstat -tlnp | grep 8000

# Test container connectivity
docker-compose exec app curl http://localhost:8000/health
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with debug output
uvicorn app.main:app --reload --log-level debug
```

### Performance Debugging

```bash
# Memory profiling
python -m memory_profiler your_script.py

# CPU profiling
py-spy record -o profile.svg -d 30 -p PID

# Load testing
locust -f tests/performance/locustfile.py --host http://localhost:8000
```

## Best Practices

### Development Workflow

1. **Feature Branch Workflow**:
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "feat: add new feature"
   git push origin feature/new-feature
   # Create pull request
   ```

2. **Commit Message Format**:
   ```
   type(scope): description
   
   feat: add new API endpoint
   fix: resolve authentication bug
   docs: update API documentation
   test: add unit tests for service
   refactor: improve code structure
   ```

3. **Code Review Process**:
   - All code must be reviewed
   - Automated checks must pass
   - Security scan must be clean
   - Tests must achieve 80% coverage

### Security Best Practices

1. **Secrets Management**:
   - Never commit secrets to repository
   - Use environment variables
   - Rotate secrets regularly
   - Use secret management services

2. **Container Security**:
   - Use non-root users
   - Minimal base images
   - Regular security updates
   - Vulnerability scanning

3. **API Security**:
   - Rate limiting
   - Input validation
   - Authentication and authorization
   - HTTPS only in production

### Performance Optimization

1. **Application Performance**:
   - Async/await patterns
   - Connection pooling
   - Caching strategies
   - Database optimization

2. **Infrastructure Performance**:
   - Load balancing
   - CDN usage
   - Resource optimization
   - Monitoring and alerting

### Maintenance

1. **Regular Updates**:
   - Dependency updates
   - Security patches
   - Python version updates
   - Base image updates

2. **Monitoring**:
   - Performance metrics
   - Error tracking
   - Resource usage
   - User analytics

3. **Backup and Recovery**:
   - Database backups
   - Configuration backups
   - Disaster recovery planning
   - Data retention policies

## Additional Resources

### Documentation Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/best-practices/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

### Tools and Services

- **Code Quality**: SonarQube, CodeClimate
- **Security**: Snyk, WhiteSource
- **Monitoring**: DataDog, New Relic
- **Error Tracking**: Sentry, Rollbar

### Support

For issues and questions:
1. Check the troubleshooting section
2. Search existing GitHub issues
3. Create a new issue with detailed information
4. Contact the development team

---

This guide provides a comprehensive overview of the CI/CD pipeline for PL8WRDS. Keep this document updated as the pipeline evolves and new features are added.