# Core Concepts

Understanding the fundamental concepts and architecture of the prmxctrl SDK.

## Table of Contents

1. [SDK Architecture](#sdk-architecture)
2. [Hierarchical Endpoints](#hierarchical-endpoints)
3. [Type Safety with Pydantic](#type-safety-with-pydantic)
4. [Async/Await Patterns](#asyncawait-patterns)
5. [HTTP Methods](#http-methods)
6. [Request/Response Models](#requestresponse-models)

## SDK Architecture

### Layered Design

The SDK is organized in layers, each with specific responsibilities:

```
┌─────────────────────────────────────┐
│   Your Application Code             │
├─────────────────────────────────────┤
│   ProxmoxClient (Main Entry Point)  │
├─────────────────────────────────────┤
│   Endpoint Classes (Generated)       │
│   ├─ ClusterEndpoints               │
│   ├─ NodesEndpoints                 │
│   ├─ StorageEndpoints               │
│   ├─ AccessEndpoints                │
│   └─ ...                            │
├─────────────────────────────────────┤
│   Data Models (Pydantic v2)         │
│   ├─ Request Models                 │
│   ├─ Response Models                │
│   └─ Constraint Validation          │
├─────────────────────────────────────┤
│   HTTP Client (httpx)               │
│   ├─ Connection Pooling             │
│   ├─ Authentication                 │
│   ├─ Session Management             │
│   └─ Error Handling                 │
├─────────────────────────────────────┤
│   Proxmox VE API                    │
└─────────────────────────────────────┘
```

### Component Responsibilities

**ProxmoxClient**
- Main entry point for SDK
- Provides access to top-level endpoints
- Manages HTTP client lifecycle

**Endpoint Classes**
- Mirror Proxmox API structure
- Provide hierarchical navigation
- Implement HTTP methods (GET, POST, PUT, DELETE)
- Generated from official API schema

**Data Models**
- Pydantic v2 models for type safety
- Validate request parameters
- Type hints for response data
- Constraint enforcement (min/max, patterns, etc.)

**HTTP Client**
- Manages HTTP connections with pooling
- Handles authentication (tickets, tokens)
- Manages CSRF tokens
- Implements retry logic
- Parses responses

## Hierarchical Endpoints

### The Proxmox API is Hierarchical

Proxmox API endpoints follow a clear hierarchical structure:

```
/api2/json/
├── /cluster
│   ├── /status
│   ├── /resources
│   ├── /backup
│   ├── /ha
│   └── ...
├── /nodes
│   ├── /{node}
│   │   ├── /status
│   │   ├── /qemu
│   │   │   ├── /{vmid}
│   │   │   │   ├── /config
│   │   │   │   ├── /status
│   │   │   │   └── ...
│   │   │   └── ...
│   │   ├── /lxc
│   │   └── ...
│   └── ...
├── /storage
│   ├── /{storage}
│   │   └── ...
│   └── ...
└── ...
```

### SDK Mirrors This Structure

The SDK classes mirror this hierarchy:

```python
# Top-level endpoints
client.cluster.*
client.nodes.*
client.storage.*
client.access.*
client.pools.*
client.version.*

# Single-level deep endpoints
await client.cluster.status.get()
await client.nodes.list()

# Multi-level navigation
# /nodes/{node}
client.nodes("pve1")

# /nodes/{node}/qemu/{vmid}
client.nodes("pve1").qemu(100)

# /nodes/{node}/qemu/{vmid}/config
await client.nodes("pve1").qemu(100).config.get()
```

### Callable Parameters

Endpoints that require path parameters use callable syntax:

```python
# Pass parameter as string
node_endpoint = client.nodes("pve1")

# Can chain multiple parameters
vm_endpoint = client.nodes("pve1").qemu(100)

# These are equivalent to API paths:
# /nodes/pve1
# /nodes/pve1/qemu/100
```

### Endpoint Methods

Each endpoint exposes HTTP methods as Python methods:

```python
# GET request
result = await client.cluster.status.get()

# POST request (create)
result = await client.nodes("pve1").qemu.create(
    vmid=100,
    name="my-vm"
)

# PUT request (update)
await client.nodes("pve1").qemu(100).config.update(
    memory=4096
)

# DELETE request
await client.nodes("pve1").qemu(100).delete()
```

## Type Safety with Pydantic

### What is Pydantic?

Pydantic is a Python library for data validation using Python type hints. It ensures:

1. **Type Validation**: Parameters match expected types
2. **Constraint Validation**: Values satisfy min/max, pattern, enum constraints
3. **Automatic Conversion**: Attempts to convert compatible types
4. **Error Reporting**: Clear error messages for invalid data

### Type-Safe Requests

Request parameters are validated before being sent:

```python
# Valid request - passes validation
result = await client.nodes("pve1").qemu.create(
    vmid=100,              # int - correct type
    name="my-vm",          # str - correct type
    memory=2048            # int - correct type
)

# Invalid request - fails validation
try:
    result = await client.nodes("pve1").qemu.create(
        vmid="not-a-number",  # ❌ Should be int
        name=123,             # ❌ Should be str
        memory="2048"         # ⚠️ Will be converted to 2048
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

### Type-Safe Responses

Response data is automatically typed:

```python
from prmxctrl.models.nodes import NodeStatusResponse

# IDE knows the exact type
status: NodeStatusResponse = await client.nodes("pve1").status.get()

# IDE shows available fields with type hints
print(status.uptime)      # IDE knows this is int
print(status.cpu)         # IDE knows this is float
print(status.memory)      # IDE knows this is NodeMemory (nested object)
```

### Constraint Validation

Pydantic enforces constraints from the API schema:

```python
# Valid: vmid between 100 and 999999
result = await client.nodes("pve1").qemu.create(vmid=100)

# Invalid: vmid must be positive integer
try:
    result = await client.nodes("pve1").qemu.create(vmid=-1)
except ValueError as e:
    print(f"VMID must be positive: {e}")

# Valid: name matches pattern
result = await client.nodes("pve1").qemu.create(
    vmid=100,
    name="my-vm"  # Alphanumeric, hyphens, underscores
)

# Invalid: name with invalid characters
try:
    result = await client.nodes("pve1").qemu.create(
        vmid=100,
        name="my vm!"  # ❌ Invalid character (space, !)
    )
except ValueError as e:
    print(f"Invalid name: {e}")
```

## Async/Await Patterns

### Why Async?

Async/await allows efficient handling of I/O operations:

```python
# Sequential requests (slow) - 30 seconds for 3 requests
result1 = await client.cluster.status.get()  # 10 seconds
result2 = await client.cluster.resources.get()  # 10 seconds
result3 = await client.nodes.list()  # 10 seconds

# Concurrent requests (fast) - ~10 seconds for 3 requests
results = await asyncio.gather(
    client.cluster.status.get(),
    client.cluster.resources.get(),
    client.nodes.list()
)
```

### Basic Async Patterns

```python
import asyncio
from prmxctrl import ProxmoxClient

# Pattern 1: Simple async function
async def get_cluster_status():
    async with ProxmoxClient(...) as client:
        return await client.cluster.status.get()

# Pattern 2: Main async function
async def main():
    async with ProxmoxClient(...) as client:
        status = await client.cluster.status.get()
        print(status)

# Run the async function
asyncio.run(main())

# Pattern 3: Concurrent operations
async def get_all_info():
    async with ProxmoxClient(...) as client:
        status, nodes, storage = await asyncio.gather(
            client.cluster.status.get(),
            client.nodes.list(),
            client.storage.list()
        )
        return status, nodes, storage
```

### Error Handling in Async

```python
import asyncio
from prmxctrl.base.exceptions import ProxmoxAPIError

async def safe_get_nodes():
    async with ProxmoxClient(...) as client:
        try:
            nodes = await client.nodes.list()
            return nodes
        except ProxmoxAPIError as e:
            print(f"Failed to get nodes: {e}")
            return []

# Run with timeout protection
try:
    nodes = asyncio.wait_for(safe_get_nodes(), timeout=30.0)
except asyncio.TimeoutError:
    print("Operation timed out")
```

## HTTP Methods

### GET - Retrieve Data

Get methods fetch data without modifying resources:

```python
# List all nodes
nodes = await client.nodes.list()

# Get specific node status
status = await client.nodes("pve1").status.get()

# Get VM configuration
config = await client.nodes("pve1").qemu(100).config.get()
```

### POST - Create/Execute

POST methods create new resources or execute actions:

```python
# Create new VM
result = await client.nodes("pve1").qemu.create(
    vmid=100,
    name="new-vm",
    memory=2048
)

# Start a VM
await client.nodes("pve1").qemu(100).status.create(command="start")

# Create a backup
await client.nodes("pve1").backup.create(
    vmid=100,
    mode="snapshot"
)
```

### PUT - Update

PUT methods update existing resources:

```python
# Update VM memory
await client.nodes("pve1").qemu(100).config.update(
    memory=4096
)

# Update storage name
await client.storage("local").update(
    content="images,rootdir"
)
```

### DELETE - Remove

DELETE methods remove resources:

```python
# Delete VM
await client.nodes("pve1").qemu(100).delete()

# Delete storage
await client.storage("backup").delete()
```

## Request/Response Models

### Understanding Models

Every API endpoint has associated request and response models:

```python
# Response model type
from prmxctrl.models.nodes import NodeStatusResponse

# Returned data is typed
status: NodeStatusResponse = await client.nodes("pve1").status.get()

# IDE provides full autocomplete
print(status.uptime)      # int
print(status.cpu)         # float
print(status.memory)      # NodeMemory (nested type)
```

### Optional vs Required Parameters

```python
# All required parameters must be provided
result = await client.nodes("pve1").qemu.create(
    vmid=100,      # Required
    name="my-vm"   # Required
)

# Optional parameters can be omitted
result = await client.nodes("pve1").qemu.create(
    vmid=100,
    name="my-vm",
    # Optional parameters (if needed):
    memory=2048,      # Optional
    cores=2,          # Optional
    description=""    # Optional
)
```

### Nested Models

Responses often contain nested objects:

```python
status = await client.nodes("pve1").status.get()

# Nested memory object
print(status.memory)           # NodeMemory object
print(status.memory.used)      # int - memory used in bytes
print(status.memory.free)      # int - free memory in bytes
print(status.memory.total)     # int - total memory in bytes

# Access nested data
memory_percent = (status.memory.used / status.memory.total) * 100
print(f"Memory usage: {memory_percent:.1f}%")
```

## Best Practices

### 1. Always Use Context Manager

```python
# ✅ Good - automatic cleanup
async with ProxmoxClient(...) as client:
    result = await client.cluster.status.get()

# ❌ Bad - potential resource leak
client = ProxmoxClient(...)
result = await client.cluster.status.get()
```

### 2. Handle Exceptions

```python
# ✅ Good - proper error handling
try:
    result = await client.nodes("invalid").status.get()
except ProxmoxAPIError as e:
    print(f"Error: {e.status_code} - {e.message}")

# ❌ Bad - silently fails
result = await client.nodes("invalid").status.get()
```

### 3. Use Type Hints

```python
# ✅ Good - explicit types
from prmxctrl.models.nodes import NodeListResponse

nodes: list[NodeListResponse] = await client.nodes.list()

# ❌ Bad - no type information
nodes = await client.nodes.list()
```

### 4. Leverage IDE Features

```python
# With proper types, IDE provides:
# - Autocomplete on response fields
# - Parameter validation before runtime
# - Jump-to-definition for models
# - Quick documentation lookup

status = await client.nodes("pve1").status.get()
# Hover over 'status' to see full type information
```

---

**See Also**: [Getting Started](./01-getting-started.md) | [API Reference](./04-api-reference.md) | [Data Models](./05-data-models.md)
