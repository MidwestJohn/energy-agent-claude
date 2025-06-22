# Contributing to Energy Grid Management Agent

Thank you for your interest in contributing to the Energy Grid Management Agent! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style and Standards](#code-style-and-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Security](#security)
- [Documentation](#documentation)
- [Release Process](#release-process)
- [Community Guidelines](#community-guidelines)

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.9+** installed
- **Git** installed and configured
- **Neo4j Database** (local or cloud instance)
- **Claude AI API Key** from Anthropic
- **Basic knowledge** of:
  - Python programming
  - Streamlit framework
  - Neo4j database
  - Git workflow

### Quick Start

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/energy-agent-claude.git
   cd energy-agent-claude
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configure environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your credentials
   nano .env
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🔧 Development Setup

### Project Structure

```
energy-agent-claude/
├── app.py                 # Main Streamlit application
├── app_enhanced.py        # Enhanced version with performance features
├── app_cloud.py           # Cloud-optimized version
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── database.py        # Database operations
│   ├── analytics.py       # Analytics functions
│   └── helpers.py         # Helper functions
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── performance/      # Performance tests
├── docs/                 # Documentation
├── k8s/                  # Kubernetes manifests
├── docker/               # Docker configurations
└── scripts/              # Utility scripts
```

### Development Tools

Install development tools for code quality:

```bash
# Code formatting and linting
pip install black isort flake8 mypy

# Testing
pip install pytest pytest-cov pytest-mock

# Security scanning
pip install bandit safety

# Performance testing
pip install locust

# Documentation
pip install sphinx sphinx-rtd-theme
```

### Pre-commit Hooks

Set up pre-commit hooks for automatic code quality checks:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 📝 Code Style and Standards

### Python Code Style

We follow **PEP 8** with some modifications:

- **Line length:** 88 characters (Black default)
- **Import sorting:** Use `isort`
- **Type hints:** Required for all functions
- **Docstrings:** Google style docstrings

### Code Formatting

```bash
# Format code with Black
black .

# Sort imports with isort
isort .

# Check code style with flake8
flake8 .
```

### Type Hints

All functions must include type hints:

```python
from typing import List, Dict, Optional, Union
import pandas as pd

def analyze_equipment(
    equipment_data: pd.DataFrame,
    threshold: float = 0.8
) -> Dict[str, Union[List[str], float]]:
    """
    Analyze equipment data and return insights.
    
    Args:
        equipment_data: DataFrame containing equipment information
        threshold: Risk threshold for analysis
        
    Returns:
        Dictionary containing analysis results
    """
    # Implementation here
    pass
```

### Naming Conventions

- **Functions and variables:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Files:** `snake_case.py`
- **Directories:** `snake_case/`

### Error Handling

Always include proper error handling:

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def safe_database_operation(query: str) -> Optional[pd.DataFrame]:
    """Execute database query with error handling."""
    try:
        result = execute_query(query)
        return result
    except ConnectionError as e:
        logger.error(f"Database connection failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
```

## 🧪 Testing Guidelines

### Test Structure

Organize tests by type:

```
tests/
├── unit/                 # Unit tests
│   ├── test_database.py
│   ├── test_analytics.py
│   └── test_helpers.py
├── integration/          # Integration tests
│   ├── test_app.py
│   └── test_api.py
├── performance/          # Performance tests
│   └── test_load.py
└── conftest.py          # Test configuration
```

### Writing Tests

Follow these guidelines:

1. **Test naming:** `test_<function_name>_<scenario>`
2. **Use fixtures:** For common setup
3. **Mock external dependencies:** Database, APIs
4. **Test edge cases:** Invalid inputs, error conditions
5. **Maintain test isolation:** Each test should be independent

### Example Test

```python
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from utils.analytics import analyze_equipment

class TestAnalytics:
    """Test analytics functions."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample equipment data for testing."""
        return pd.DataFrame({
            'equipment_id': ['EQ001', 'EQ002'],
            'risk_score': [0.7, 0.9],
            'status': ['operational', 'maintenance']
        })
    
    def test_analyze_equipment_success(self, sample_data):
        """Test successful equipment analysis."""
        result = analyze_equipment(sample_data, threshold=0.8)
        
        assert isinstance(result, dict)
        assert 'high_risk_equipment' in result
        assert len(result['high_risk_equipment']) == 1
    
    def test_analyze_equipment_empty_data(self):
        """Test analysis with empty data."""
        empty_df = pd.DataFrame()
        result = analyze_equipment(empty_df)
        
        assert result['high_risk_equipment'] == []
    
    @patch('utils.analytics.logger')
    def test_analyze_equipment_invalid_input(self, mock_logger):
        """Test analysis with invalid input."""
        with pytest.raises(ValueError):
            analyze_equipment(None)
        
        mock_logger.error.assert_called_once()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_database.py

# Run tests in parallel
pytest -n auto

# Run integration tests only
pytest tests/integration/
```

### Test Coverage

Maintain at least **80% code coverage**:

```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# View coverage report
open htmlcov/index.html
```

## 🔄 Pull Request Process

### Before Submitting

1. **Ensure tests pass**
   ```bash
   pytest
   ```

2. **Check code quality**
   ```bash
   black --check .
   isort --check-only .
   flake8 .
   mypy .
   ```

3. **Run security scan**
   ```bash
   bandit -r .
   safety check
   ```

4. **Update documentation**
   - Update README.md if needed
   - Add docstrings for new functions
   - Update API documentation

### Creating a Pull Request

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new analytics feature"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create Pull Request**
   - Use the provided PR template
   - Fill out all required sections
   - Request reviews from maintainers

### Commit Message Format

Use conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

Examples:
```
feat(analytics): add risk assessment algorithm
fix(database): resolve connection timeout issue
docs(readme): update installation instructions
test(api): add integration tests for equipment endpoints
```

### PR Review Process

1. **Automated checks** must pass
2. **Code review** by at least one maintainer
3. **Security review** for sensitive changes
4. **Performance review** for major changes
5. **Documentation review** for new features

## 🐛 Issue Reporting

### Before Reporting

1. **Search existing issues** to avoid duplicates
2. **Check documentation** for solutions
3. **Try the latest version** of the application
4. **Reproduce the issue** consistently

### Issue Templates

Use the appropriate issue template:

- **Bug Report:** For bugs and issues
- **Feature Request:** For new features
- **Security Issue:** For security vulnerabilities

### Required Information

Include in your issue:

- **Environment details** (OS, Python version, etc.)
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages and logs**
- **Screenshots** (if applicable)

## 🔒 Security

### Security Guidelines

1. **Never commit secrets** (API keys, passwords)
2. **Use environment variables** for sensitive data
3. **Validate all inputs** to prevent injection attacks
4. **Follow OWASP guidelines** for web security
5. **Report security issues** privately

### Security Reporting

For security vulnerabilities:

1. **DO NOT** create public issues
2. **Email** security issues to maintainers
3. **Use** the security issue template
4. **Include** detailed reproduction steps
5. **Wait** for acknowledgment before disclosure

### Security Best Practices

```python
# ✅ Good: Use parameterized queries
def safe_query(equipment_id: str) -> pd.DataFrame:
    query = "SELECT * FROM equipment WHERE id = %s"
    return execute_query(query, (equipment_id,))

# ❌ Bad: String concatenation
def unsafe_query(equipment_id: str) -> pd.DataFrame:
    query = f"SELECT * FROM equipment WHERE id = {equipment_id}"
    return execute_query(query)
```

## 📚 Documentation

### Documentation Standards

1. **Code documentation:** Google style docstrings
2. **API documentation:** OpenAPI/Swagger format
3. **User documentation:** Clear and concise
4. **Developer documentation:** Technical details

### Writing Documentation

```python
def calculate_risk_score(
    equipment_data: pd.DataFrame,
    weights: Dict[str, float] = None
) -> pd.Series:
    """
    Calculate risk scores for equipment based on various factors.
    
    This function analyzes equipment data and calculates a composite
    risk score based on multiple factors including age, maintenance
    history, and operational status.
    
    Args:
        equipment_data: DataFrame containing equipment information
            with columns: ['equipment_id', 'age', 'maintenance_count', 'status']
        weights: Dictionary of factor weights. Default weights are:
            - age: 0.3
            - maintenance_count: 0.4
            - status: 0.3
            
    Returns:
        pd.Series: Risk scores indexed by equipment_id
        
    Raises:
        ValueError: If equipment_data is empty or missing required columns
        KeyError: If weights contains invalid factor names
        
    Example:
        >>> data = pd.DataFrame({
        ...     'equipment_id': ['EQ001', 'EQ002'],
        ...     'age': [5, 10],
        ...     'maintenance_count': [2, 5],
        ...     'status': ['operational', 'maintenance']
        ... })
        >>> scores = calculate_risk_score(data)
        >>> print(scores)
        EQ001    0.45
        EQ002    0.78
        dtype: float64
    """
    # Implementation here
    pass
```

### Building Documentation

```bash
# Install documentation tools
pip install sphinx sphinx-rtd-theme

# Build documentation
cd docs
make html

# View documentation
open _build/html/index.html
```

## 🚀 Release Process

### Version Management

We use semantic versioning (SemVer):

- **MAJOR.MINOR.PATCH**
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes (backward compatible)

### Release Checklist

Before each release:

- [ ] **All tests pass**
- [ ] **Documentation updated**
- [ ] **Security scan clean**
- [ ] **Performance benchmarks met**
- [ ] **Changelog updated**
- [ ] **Version bumped**
- [ ] **Release notes written**

### Creating a Release

1. **Update version**
   ```bash
   # Update version in setup.py and __init__.py
   git tag v1.2.3
   git push origin v1.2.3
   ```

2. **Create GitHub release**
   - Use release template
   - Include changelog
   - Attach release artifacts

3. **Deploy to production**
   - Follow deployment guide
   - Run health checks
   - Monitor for issues

## 👥 Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Be patient** with newcomers
- **Be helpful** and supportive

### Communication

- **GitHub Issues:** For bugs and feature requests
- **GitHub Discussions:** For questions and ideas
- **Pull Requests:** For code contributions
- **Email:** For security issues

### Recognition

Contributors will be recognized in:

- **README.md** contributors section
- **Release notes** for significant contributions
- **GitHub profile** for active contributors

## 🤝 Getting Help

### Resources

- **Documentation:** Check the README and docs/
- **Issues:** Search existing issues
- **Discussions:** Ask questions in GitHub Discussions
- **Wiki:** Check project wiki for guides

### Contact

- **Maintainers:** @maintainer1, @maintainer2
- **Security:** security@example.com
- **General:** discussions tab on GitHub

## 📋 Checklist for Contributors

Before submitting your contribution:

- [ ] **Code follows style guidelines**
- [ ] **Tests written and passing**
- [ ] **Documentation updated**
- [ ] **Security considerations addressed**
- [ ] **Performance impact assessed**
- [ ] **Pull request template completed**
- [ ] **Self-review performed**

---

**Thank you for contributing to the Energy Grid Management Agent! 🚀**

Your contributions help make this project better for everyone in the energy management community. 