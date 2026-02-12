# Testing Framework Documentation

## Overview

This document describes the testing framework setup for the Haki FMCG 2.0 project, covering unit tests, integration tests, mock data generation, and CI/CD configuration.

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py          # Pytest fixtures and configuration
├── mock_data.py         # Mock data generators
├── unit/
│   ├── __init__.py
│   ├── test_normalizers.py   # Tests for normalization utilities
│   └── test_database.py      # Tests for database operations
└── integration/
    ├── __init__.py
    └── test_workflows.py     # End-to-end workflow tests
```

## Configuration Files

- `pytest.ini` - Pytest configuration
- `.coveragerc` - Coverage configuration
- `.github/workflows/tests.yml` - CI/CD pipeline

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_normalizers.py
```

### Run Specific Test Class
```bash
pytest tests/unit/test_normalizers.py::TestSpecificationNormalizer
```

### Run Specific Test
```bash
pytest tests/unit/test_normalizers.py::TestSpecificationNormalizer::test_normalize_conductor_size_sqmm
```

### Run with Markers
```bash
# Run only unit tests
pytest -m unit

# Run only database tests
pytest -m database

# Run only normalizer tests
pytest -m normalizer

# Skip slow tests
pytest -m "not slow"
```

### Run with Coverage
```bash
# Generate coverage report
pytest --cov=agents --cov=database --cov-report=html

# View HTML report
open htmlcov/index.html
```

## Test Fixtures

### Database Fixtures

- `test_db_path` - Temporary database path
- `db_engine` - Database engine instance
- `db_session` - Database session (auto-rollback)

### Sample Data Fixtures

- `sample_product_data` - Sample product dictionary
- `sample_vendor_data` - Sample vendor dictionary
- `sample_rfp_data` - Sample RFP dictionary
- `sample_conductor_specs` - List of conductor specifications
- `sample_standards` - List of electrical standards

### Utility Fixtures

- `spec_normalizer` - SpecificationNormalizer instance
- `unit_converter` - UnitConverter instance
- `standard_mapper` - StandardMapper instance
- `text_cleaner` - TextCleaner instance
- `param_extractor` - ParameterExtractor instance
- `validator` - Validator instance

### Mock Data Fixtures

- `mock_rfp_text` - Sample RFP text for extraction testing
- `mock_product_catalog` - List of mock products

## Mock Data Generator

The `MockDataGenerator` class generates realistic test data:

```python
from tests.mock_data import MockDataGenerator

generator = MockDataGenerator()

# Generate single items
product = generator.generate_product()
vendor = generator.generate_vendor()
rfp = generator.generate_rfp(num_items=3)
rfp_text = generator.generate_rfp_text()

# Generate batches
products = generator.generate_products_batch(count=10)
vendors = generator.generate_vendors_batch(count=5)
```

### Deterministic Data

For tests requiring consistent data:

```python
from tests.mock_data import DETERMINISTIC_PRODUCTS, DETERMINISTIC_VENDORS
```

## Test Categories

### Unit Tests

Located in `tests/unit/`:

1. **test_normalizers.py**
   - SpecificationNormalizer tests
   - UnitConverter tests
   - StandardMapper tests
   - TextCleaner tests
   - ParameterExtractor tests
   - Validator tests

2. **test_database.py**
   - DatabaseEngine tests
   - Model CRUD tests
   - Constraint tests
   - Transaction tests

### Integration Tests

Located in `tests/integration/`:

1. **test_workflows.py**
   - Product lifecycle tests
   - Normalization workflow tests
   - Data validation workflow tests
   - Standard mapping workflow tests
   - End-to-end RFP processing tests

## Writing New Tests

### Test Class Template

```python
import pytest

class TestMyFeature:
    """Tests for MyFeature"""
    
    def test_basic_functionality(self, fixture_name):
        """Test description"""
        # Arrange
        input_data = "test input"
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_value
    
    @pytest.mark.slow
    def test_slow_operation(self):
        """Test that takes a long time"""
        pass
    
    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_with_parameters(self, input, expected):
        """Parametrized test"""
        assert my_function(input) == expected
```

### Using Fixtures

```python
def test_with_database(self, db_session, sample_product_data):
    """Test using database fixtures"""
    from database.crud import ProductCRUD
    
    crud = ProductCRUD(db_session)
    product = crud.create(sample_product_data)
    
    assert product.id is not None
```

## CI/CD Pipeline

The GitHub Actions workflow runs:

1. **Test Job** (Python 3.10, 3.11, 3.12)
   - Install dependencies
   - Run unit tests
   - Run integration tests
   - Generate coverage report
   - Upload to Codecov

2. **Lint Job**
   - Run flake8
   - Check formatting with black

3. **Security Job**
   - Run bandit security checks
   - Check dependencies with safety

## Coverage Requirements

Target coverage: 80%

Key modules to cover:
- `agents/shared/utils/` - Utility functions
- `database/` - Database operations
- `agents/*/` - Agent implementations

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Use clear test method names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Use Fixtures**: Leverage pytest fixtures for setup
5. **Mock External Dependencies**: Use mocks for external services
6. **Parametrize**: Use parametrize for multiple test cases
7. **Mark Tests**: Use markers for categorization
