# prmxctrl - Proxmox VE Python SDK

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Type Checking](https://img.shields.io/badge/mypy-strict-green.svg)](https://mypy-lang.org/)
[![Linting](https://img.shields.io/badge/ruff-passing-green.svg)](https://github.com/astral-sh/ruff)

A fully type-safe, auto-generated Python SDK for the Proxmox Virtual Environment (VE) API. Built with Pydantic v2, httpx, and modern Python async patterns.

## Features

- **100% Type Safe**: Full type hints with mypy --strict compliance
- **Auto-Generated**: Complete SDK generated from Proxmox API schema
- **Async/Await**: Modern async HTTP client with connection pooling
- **Hierarchical API**: Navigate the API like `client.nodes("pve1").qemu(100).config.get()`
- **Authentication**: Support for both password and API token authentication
- **Validation**: Pydantic models ensure request/response data integrity
- **Comprehensive**: 284 endpoints covering the full Proxmox VE API

## Quick Start

### Installation

```bash
pip install prmxctrl
```

### Basic Usage

```python
import asyncio
from prmxctrl import ProxmoxClient

async def main():
    async with ProxmoxClient(
        host="your-proxmox-host",
        user="your-username@pve",
        password="your-password"
    ) as client:
        # Get cluster status
        status = await client.cluster.status.get()
        print(f"Cluster status: {status}")

        # List all nodes
        nodes = await client.nodes.get()
        for node in nodes:
            print(f"Node: {node.node}")

        # Get VM configuration
        vm_config = await client.nodes("pve1").qemu(100).config.get()
        print(f"VM config: {vm_config}")

asyncio.run(main())
```

### API Token Authentication

```python
async with ProxmoxClient(
    host="your-proxmox-host",
    token_name="your-token-name",
    token_secret="your-token-secret"
) as client:
    # Use the client...
    pass
```

## API Structure

The SDK mirrors the Proxmox API structure hierarchically:

- `client.cluster.*` - Cluster management
- `client.nodes(node).*` - Node-specific operations
- `client.nodes(node).qemu(vmid).*` - QEMU VM operations
- `client.nodes(node).lxc(vmid).*` - LXC container operations
- `client.access.*` - User and permission management
- `client.pools.*` - Pool management
- `client.storage.*` - Storage operations

## Advanced Usage

### Creating Resources

```python
# Create a new QEMU VM
vm_config = {
    "name": "test-vm",
    "memory": 2048,
    "cores": 2,
    "net0": "virtio,bridge=vmbr0",
    "ide2": "local:iso/ubuntu-22.04.iso,media=cdrom"
}

result = await client.nodes("pve1").qemu.create(
    node="pve1",
    vmid=100,
    **vm_config
)
```

### Error Handling

```python
from prmxctrl import ProxmoxAPIError, ProxmoxAuthError

try:
    result = await client.nodes("pve1").qemu(100).config.get()
except ProxmoxAuthError:
    print("Authentication failed")
except ProxmoxAPIError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

### Working with Models

All request/response data is validated using Pydantic models:

```python
from prmxctrl.models.nodes import NodeListResponse

# Type-safe response handling
nodes: list[NodeListResponse] = await client.nodes.get()
for node in nodes:
    # IDE will show available fields with type hints
    print(f"Node {node.node}: {node.status} ({node.cpu:.1%} CPU)")
```

## Development

### Prerequisites

- Python 3.10+
- Access to Proxmox VE API documentation

### Setup

```bash
git clone https://github.com/your-repo/prmxctrl.git
cd prmxctrl
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev]
```

### Code Generation

The SDK is auto-generated from the Proxmox API schema:

```bash
# Generate the complete SDK
python tools/generate.py

# Validate the generated code
python tools/validate.py
```

### Testing

```bash
# Run the full test suite
pytest

# Run with coverage
pytest --cov=prmxctrl --cov-report=html

# Type checking
mypy --strict

# Linting
ruff check .
```

## Architecture

This SDK is built with a code generation approach:

1. **Schema Processing**: Parse Proxmox API schema from `apidata.js`
2. **Model Generation**: Create Pydantic v2 models for all request/response types
3. **Endpoint Generation**: Generate hierarchical endpoint classes
4. **Client Integration**: Tie everything together in the main `ProxmoxClient`

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design decisions.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Disclaimer

This SDK is not officially affiliated with Proxmox Server Solutions GmbH. Use at your own risk.