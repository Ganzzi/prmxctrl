"""
Pytest configuration and fixtures for prmxctrl tests.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_http_client():
    """Mock HTTPClient for testing."""
    client = Mock()
    client.request = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client


@pytest.fixture
def sample_endpoint():
    """Sample endpoint for testing."""
    from generator.parse_schema import Endpoint, Method, Parameter, Response

    return Endpoint(
        path="/test/endpoint",
        text="endpoint",
        leaf=True,
        methods={
            "GET": Method(
                method="GET",
                name="get_test",
                description="Get test data",
                parameters=[
                    Parameter(name="id", type="integer", description="Test ID", minimum=1),
                    Parameter(name="name", type="string", description="Test name", optional=True),
                ],
                returns=Response(type="object"),
                protected=False,
            ),
            "POST": Method(
                method="POST",
                name="create_test",
                description="Create test",
                parameters=[
                    Parameter(name="name", type="string", description="Test name"),
                    Parameter(name="value", type="integer", description="Test value", minimum=0),
                ],
                returns=Response(type="object"),
                protected=False,
            ),
        },
        children=[],
    )


@pytest.fixture
def sample_schema():
    """Sample schema data for testing."""
    return [
        {
            "path": "/test",
            "text": "test",
            "leaf": 0,
            "info": {
                "GET": {
                    "name": "get_test",
                    "description": "Get test data",
                    "parameters": {
                        "properties": {
                            "id": {"type": "integer", "description": "Test ID", "minimum": 1},
                            "name": {"type": "string", "description": "Test name", "optional": 1},
                        }
                    },
                    "returns": {"type": "object"},
                }
            },
            "children": [],
        }
    ]


@pytest.fixture(scope="session")
def generated_sdk_available():
    """Check if generated SDK is available for testing."""
    try:
        from prmxctrl import ProxmoxClient, endpoints, models

        return True
    except ImportError:
        return False


@pytest.fixture
def skip_if_no_sdk(generated_sdk_available):
    """Skip test if SDK is not generated."""
    if not generated_sdk_available:
        pytest.skip("Generated SDK not available - run code generation first")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "generated: marks tests that require generated code")


def pytest_collection_modifyitems(config, items):
    """Tag tests so PR gating can exclude integration and e2e runs."""
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        stem = Path(path).stem

        if "/tests/e2e/" in path or "e2e" in stem:
            item.add_marker(pytest.mark.e2e)
        elif "/tests/integration/" in path or "integration" in stem:
            item.add_marker(pytest.mark.integration)
        elif "/tests/generated/" in path or "generated" in stem:
            item.add_marker(pytest.mark.generated)
        else:
            item.add_marker(pytest.mark.unit)
