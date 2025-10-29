# Contributing to prmxctrl

Thank you for your interest in contributing to prmxctrl! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Access to a Proxmox VE instance (for integration testing)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/prmxctrl.git
   cd prmxctrl
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .[dev]
   ```

4. **Verify setup:**
   ```bash
   # Run tests
   pytest

   # Type checking
   mypy --strict

   # Linting
   ruff check .
   ```

## Development Workflow

### 1. Choose an Issue

- Check the [issue tracker](https://github.com/your-repo/prmxctrl/issues) for open issues
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Test Your Changes

```bash
# Run the full test suite
pytest

# Run with coverage
pytest --cov=prmxctrl --cov-report=html

# Type checking
mypy --strict

# Linting
ruff check .

# Format code
black .
ruff check --fix .
```

### 5. Commit Your Changes

- Use clear, descriptive commit messages
- Reference issue numbers when applicable

```bash
git add .
git commit -m "feat: add support for new Proxmox endpoint

- Add new endpoint generation for /cluster/firewall/aliases
- Update type mapping for alias constraints
- Add tests for alias validation

Closes #123"
```

### 6. Create a Pull Request

- Push your branch to GitHub
- Create a pull request with a clear description
- Reference any related issues
- Request review from maintainers

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints everywhere
- Use docstrings for all public functions/classes
- Keep line length under 88 characters (Black default)

### Type Hints

- Use modern Python 3.10+ type hints
- Prefer `T | None` over `Optional[T]`
- Use `list[T]` instead of `List[T]`
- Use `dict[K, V]` instead of `Dict[K, V]`
- Use `Callable` for function types

```python
from typing import Any, Callable

def process_data(data: dict[str, Any]) -> list[str] | None:
    # Function implementation
    pass
```

### Naming Conventions

- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_CASE`
- Private methods: `_leading_underscore`

### Imports

- Standard library imports first
- Third-party imports second
- Local imports last
- Use absolute imports
- Sort imports with `ruff`

```python
import os
import sys
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from prmxctrl.base.exceptions import ProxmoxError
```

## Testing Guidelines

### Unit Tests

- Test functions should be named `test_function_name`
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

```python
def test_endpoint_path_building():
    """Test that endpoint paths are built correctly."""
    endpoint = NodeEndpoint(client=mock_client, node="pve1")

    assert endpoint._build_path() == "/nodes/pve1"
    assert endpoint.qemu(100)._build_path() == "/nodes/pve1/qemu/100"
```

### Integration Tests

- Test real API interactions (use test instance)
- Use fixtures for common setup
- Clean up resources after tests

```python
@pytest.mark.asyncio
async def test_vm_creation_integration(proxmox_client):
    """Test creating a VM through the full API."""
    # Test implementation
    pass
```

### Test Coverage

- Aim for 80%+ code coverage
- Cover edge cases and error conditions
- Test generated code thoroughly

## Code Generation

### Modifying Generated Code

**Important**: Never edit generated files directly. Instead:

1. Modify the generation templates in `generator/templates/`
2. Update the generator logic in `generator/generators/`
3. Regenerate the code: `python tools/generate.py`

### Adding New Endpoints

1. Update the schema parsing if needed
2. Modify the endpoint generator
3. Add tests for the new functionality
4. Update documentation

### Schema Updates

When Proxmox releases a new API version:

1. Update the schema URL in `generator/fetch_schema.py`
2. Test the schema parsing
3. Regenerate all code
4. Update version constraints if needed

## Documentation

### Code Documentation

- Use docstrings for all public APIs
- Follow Google docstring format
- Include type information in docstrings

```python
def get_node_status(self, node: str) -> NodeStatus:
    """Get the status of a Proxmox node.

    Args:
        node: The name of the node to query.

    Returns:
        NodeStatus: The current status of the node.

    Raises:
        ProxmoxAPIError: If the API request fails.
    """
    pass
```

### User Documentation

- Update README.md for new features
- Add examples to the documentation
- Keep API documentation up to date

## Pull Request Process

### Before Submitting

- [ ] All tests pass
- [ ] Code is properly formatted (`black .`)
- [ ] Linting passes (`ruff check .`)
- [ ] Type checking passes (`mypy --strict`)
- [ ] Documentation is updated
- [ ] Commit messages are clear

### PR Description

A good PR description includes:

- What the change does
- Why the change is needed
- How the change was tested
- Any breaking changes
- Related issues

### Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged

## Issue Reporting

When reporting bugs or requesting features:

- Use the issue templates
- Provide clear reproduction steps
- Include error messages and stack traces
- Specify your environment (Python version, Proxmox version, etc.)

## Community Guidelines

- Be respectful and inclusive
- Help other contributors
- Follow the code of conduct
- Ask questions if you're unsure

## Getting Help

- Check the [documentation](README.md)
- Search existing issues
- Ask in discussions
- Contact maintainers

Thank you for contributing to prmxctrl! 🎉