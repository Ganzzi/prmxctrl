# Getting Started with prmxctrl

This guide covers installation, basic setup, and your first API call.

## Installation

### From PyPI (Recommended)

```bash
pip install prmxctrl
```

### From Source

```bash
git clone https://github.com/Ganzzi/prmxctrl.git
cd prmxctrl
pip install -e .
```

### Requirements

- **Python**: 3.10 or higher
- **Dependencies**:
  - `httpx >= 0.24.0` - Async HTTP client
  - `pydantic >= 2.0.0` - Data validation
  - `python-dotenv` - Environment variable management

## Environment Setup

### Create Environment Variables File

Create a `.env` file in your project root (copy from `.env.example` if available):

```bash
# Proxmox Connection Settings
PROXMOX_HOST=https://your-proxmox-host:8006
PROXMOX_VERIFY_SSL=true
PROXMOX_TIMEOUT=30

# Authentication Method 1: Password Authentication
PROXMOX_USERNAME=your_username
PROXMOX_PASSWORD=your_password
PROXMOX_REALM=pam  # or 'pve' for Proxmox realm

# Authentication Method 2: API Token (Recommended)
PROXMOX_TOKEN_ID=your_token_name
PROXMOX_TOKEN_SECRET=your_token_uuid

# Optional: Default node and VM ID for examples
PROXMOX_NODE=pve
PROXMOX_VMID=100
```

### Load Environment Variables

In your Python code:

```python
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("PROXMOX_HOST")
username = os.getenv("PROXMOX_USERNAME")
password = os.getenv("PROXMOX_PASSWORD")
realm = os.getenv("PROXMOX_REALM", "pam")
```

## Your First API Call

### Basic Example (Async Context Manager)

```python
import asyncio
from prmxctrl import ProxmoxClient

async def main():
    # Initialize client using context manager
    async with ProxmoxClient(
        host="https://your-proxmox-host:8006",
        user="root@pam",
        password="your_password"
    ) as client:
        # Get cluster status
        status = await client.cluster.status.get()
        print(f"Cluster status: {status}")

        # List all nodes
        nodes = await client.nodes.list()
        print(f"Found {len(nodes)} nodes")
        for node in nodes:
            print(f"  - {node.node}: {node.status}")

asyncio.run(main())
```

### Environment Variable Example

```python
import os
import asyncio
from dotenv import load_dotenv
from prmxctrl import ProxmoxClient

async def main():
    load_dotenv()
    
    async with ProxmoxClient(
        host=os.getenv("PROXMOX_HOST"),
        user=f"{os.getenv('PROXMOX_USERNAME')}@{os.getenv('PROXMOX_REALM')}",
        password=os.getenv("PROXMOX_PASSWORD")
    ) as client:
        status = await client.cluster.status.get()
        print(status)

asyncio.run(main())
```

## Client Initialization Methods

The SDK supports two initialization patterns:

### Method 1: Async Context Manager (Recommended)

```python
async with ProxmoxClient(...) as client:
    result = await client.version.get()
```

**Advantages:**
- ✅ Automatic resource cleanup
- ✅ Exception-safe (cleanup happens even on errors)
- ✅ Production-ready pattern

**Disadvantages:**
- ⚠️ Type hints may show as `Any` due to context manager limitations

### Method 2: Manual Initialization (Development)

```python
client = ProxmoxClient(...)
try:
    await client._setup_client()
    result = await client.version.get()
finally:
    await client._cleanup_client()
```

**Advantages:**
- ✅ Full IDE type hints and autocomplete
- ✅ Better for exploration and development

**Disadvantages:**
- ⚠️ Manual resource management required
- ⚠️ Easy to forget cleanup calls

## Basic Concepts

### Hierarchical Endpoints

The SDK mirrors Proxmox API structure hierarchically:

```python
# Top-level endpoints
client.cluster.*        # Cluster operations
client.nodes.*          # Node operations
client.storage.*        # Storage operations
client.access.*         # User/permission management
client.pools.*          # Pool operations
client.version.*        # Version information

# Node-specific operations
client.nodes("pve1").*

# VM operations
client.nodes("pve1").qemu(100).*
client.nodes("pve1").lxc(101).*

# Nested endpoints
client.nodes("pve1").qemu(100).config.get()
```

### HTTP Methods

The SDK automatically maps HTTP methods to Python methods:

```python
# GET requests
result = await client.nodes.list()
result = await client.nodes("pve1").status.get()

# POST requests (create/action)
result = await client.nodes("pve1").qemu.create(vmid=100, ...)

# PUT requests (update)
await client.nodes("pve1").qemu(100).config.update(memory=4096)

# DELETE requests
await client.nodes("pve1").qemu(100).delete()
```

### Type Safety

All requests and responses are validated with Pydantic:

```python
from prmxctrl.models.nodes import NodeListResponse

# Type-safe response handling
nodes: list[NodeListResponse] = await client.nodes.list()
for node in nodes:
    print(f"{node.node}: {node.status}")  # IDE knows available fields
```

## Common Patterns

### 1. Listing Resources

```python
# List all nodes
nodes = await client.nodes.list()
for node in nodes:
    print(f"Node: {node.node}")

# List all storage
storage = await client.storage.list()
for store in storage:
    print(f"Storage: {store.storage}")
```

### 2. Getting Resource Details

```python
# Get specific node status
node_status = await client.nodes("pve1").status.get()

# Get VM configuration
vm_config = await client.nodes("pve1").qemu(100).config.get()
```

### 3. Creating Resources

```python
# Create a new VM
result = await client.nodes("pve1").qemu.create(
    vmid=100,
    name="test-vm",
    memory=2048,
    cores=2,
    net0="virtio,bridge=vmbr0"
)
```

### 4. Error Handling

```python
from prmxctrl.base.exceptions import ProxmoxAPIError, ProxmoxAuthError

try:
    result = await client.nodes("invalid").status.get()
except ProxmoxAuthError:
    print("Authentication failed")
except ProxmoxAPIError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

## Troubleshooting

### SSL Certificate Errors

If you get SSL certificate verification errors:

```python
# Disable SSL verification (not recommended for production)
client = ProxmoxClient(
    host="https://your-proxmox-host:8006",
    user="root@pam",
    password="password",
    verify_ssl=False  # Only for development/testing!
)
```

### Connection Timeouts

Adjust the timeout if needed:

```python
client = ProxmoxClient(
    host="https://your-proxmox-host:8006",
    user="root@pam",
    password="password",
    timeout=60.0  # 60 seconds instead of default 30
)
```

### Invalid Credentials

Ensure credentials are correct and in the right format:

```python
# Password auth format: username@realm
async with ProxmoxClient(
    host="https://your-proxmox-host:8006",
    user="root@pam",  # username@realm
    password="your_password"
) as client:
    ...

# Token auth format: token-id!token-secret (optional, or use separate parameters)
async with ProxmoxClient(
    host="https://your-proxmox-host:8006",
    user="root@pam",  # Still required for token auth
    token_name="api-token",
    token_value="token-uuid"
) as client:
    ...
```

## Next Steps

- Read [Authentication](./02-authentication.md) for detailed auth options
- Check [Core Concepts](./03-core-concepts.md) for SDK architecture
- Review [API Reference](./04-api-reference.md) for endpoint details
- See [Examples](./06-examples.md) for real-world usage patterns

---

**See Also**: [README](./README.md) | [Authentication](./02-authentication.md) | [Error Handling](./07-error-handling.md)
