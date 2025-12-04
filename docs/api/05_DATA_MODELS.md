# Data Models

Comprehensive guide to Pydantic models used in request and response handling.

## Understanding Data Models

Data models in prmxctrl are Pydantic v2 classes that:

1. **Validate Input** - Ensure request parameters are correct type and format
2. **Provide Type Hints** - Enable IDE autocomplete and type checking
3. **Document API** - Show what fields are available and expected
4. **Enforce Constraints** - Min/max values, patterns, enums

## Model Organization

Models are organized by endpoint category:

```
prmxctrl/models/
├── cluster.py      # Cluster endpoint models
├── nodes.py        # Nodes endpoint models
├── storage.py      # Storage endpoint models
├── access.py       # Access endpoint models
├── pools.py        # Pools endpoint models
└── version.py      # Version endpoint models
```

## Working with Models

### Using Response Models

Response models are automatically applied to endpoint results:

```python
from prmxctrl.models.nodes import NodeStatusResponse

# The return type is automatically set
status: NodeStatusResponse = await client.nodes("pve1").status.get()

# IDE knows exact fields available
print(status.uptime)              # int
print(status.cpu)                 # float
print(status.memory)              # NodeMemory (nested model)
print(status.memory.used)         # int
print(status.memory.free)         # int
```

### Accessing Model Fields

All response models are dataclasses with typed fields:

```python
# Access fields as attributes
status = await client.nodes("pve1").status.get()

for attr_name in dir(status):
    if not attr_name.startswith('_'):
        value = getattr(status, attr_name)
        print(f"{attr_name}: {value}")
```

### Inspecting Model Schema

Get information about model structure:

```python
from prmxctrl.models.nodes import NodeStatusResponse
import json

# Get model JSON schema
schema = NodeStatusResponse.model_json_schema()
print(json.dumps(schema, indent=2))

# Check available fields
for field_name, field_info in NodeStatusResponse.model_fields.items():
    print(f"{field_name}: {field_info.annotation}")
```

## Common Model Patterns

### Lists and Collections

Many endpoints return lists:

```python
# List returns list of models
nodes: list[NodeListResponse] = await client.nodes.list()

# Iterate over items
for node in nodes:
    print(f"{node.node}: {node.status} ({node.uptime}s uptime)")
```

### Nested Models

Response models can contain nested models:

```python
# Status response contains nested memory info
status = await client.nodes("pve1").status.get()

# Access nested model
memory = status.memory
print(f"Used: {memory.used}")
print(f"Free: {memory.free}")
print(f"Total: {memory.total}")
```

### Optional Fields

Some fields are optional and may not always be present:

```python
from typing import Optional

status = await client.nodes("pve1").status.get()

# Check if field exists before accessing
if status.description is not None:
    print(status.description)

# Or use getattr with default
description = getattr(status, 'description', 'No description')
```

### Field Validation

Request parameters are validated by Pydantic:

```python
# Valid - all constraints satisfied
await client.nodes("pve1").qemu.create(
    vmid=100,           # Integer, 100-999999
    name="my-vm",       # String, 1-255 chars, alphanumeric/hyphen/underscore
    memory=2048,        # Integer, multiple of 4 megabytes
    cores=2             # Integer, 1-8192
)

# Invalid - constraint violation
try:
    await client.nodes("pve1").qemu.create(
        vmid=-1,        # ❌ Must be >= 100
        name="my vm!",  # ❌ Invalid characters
        memory=123,     # ❌ Not multiple of 4
        cores=0         # ❌ Must be >= 1
    )
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Major Model Categories

### Cluster Models

**ClusterGETResponse** - Cluster index information
```python
status = await client.cluster.status.get()
# Fields: cluster, id, quorate, etc.
```

**ClusterResourcesResponse** - Resource status
```python
resources = await client.cluster.resources.get()
# Returns list of resource objects
```

**HAStatusResponse** - High Availability status
```python
ha = await client.cluster.ha.status.get()
# Fields: expected_nodes, ha_enabled, etc.
```

### Node Models

**NodeListResponse** - Node information
```python
nodes = await client.nodes.list()
# Fields: node, status, uptime, cpu, maxcpu, memory, etc.
```

**NodeStatusResponse** - Detailed node status
```python
status = await client.nodes("pve1").status.get()
# Includes: cpu, memory, disk, uptime, load averages
```

**QemuVMResponse** - QEMU VM information
```python
vms = await client.nodes("pve1").qemu.list()
# Fields: vmid, name, status, uptime, pid, etc.
```

**LXCContainerResponse** - LXC container information
```python
containers = await client.nodes("pve1").lxc.list()
# Fields: vmid, hostname, status, uptime, pid, etc.
```

### Storage Models

**StorageResponse** - Storage resource information
```python
storage = await client.storage.list()
# Fields: storage, type, content, used, size, etc.
```

**StorageContentResponse** - Content in storage
```python
content = await client.storage("local").content.get()
# Fields: volid, content, size, ctime, vmid, etc.
```

### Access Models

**UserResponse** - User account information
```python
users = await client.access.users.list()
# Fields: userid, email, comment, expire, mtime, etc.
```

**GroupResponse** - Group information
```python
groups = await client.access.groups.list()
# Fields: groupid, comment
```

**RoleResponse** - Role information
```python
roles = await client.access.roles.list()
# Fields: roleid, privs
```

**TokenResponse** - API token information
```python
tokens = await client.access.users("root@pam").token.list()
# Fields: tokenid, expire
```

### Pool Models

**PoolResponse** - Pool information
```python
pools = await client.pools.list()
# Fields: poolid, comment, members
```

### Version Models

**VersionResponse** - API version information
```python
version = await client.version.get()
# Fields: version, release, major, minor, patch
```

## Type Hints and Validation

### Annotated Types

Complex types use Python's `Annotated` for constraints:

```python
from typing import Annotated
from pydantic import Field

# String with constraints
name: Annotated[str, Field(min_length=1, max_length=255)]

# Integer with range
vmid: Annotated[int, Field(ge=100, le=999999)]

# String with pattern
hostname: Annotated[str, Field(pattern=r'^[a-z0-9\-]+$')]
```

### Union Types

Some fields accept multiple types:

```python
from typing import Union

# Field can be string or number
value: Union[str, int]
```

### Optional Types

Optional fields may or may not be present:

```python
from typing import Optional

# Field is optional
description: Optional[str] = None
email: Optional[str] = None
```

## Practical Examples

### Accessing Node Information

```python
from prmxctrl.models.nodes import NodeStatusResponse

async def get_node_info(node: str) -> NodeStatusResponse:
    async with ProxmoxClient(...) as client:
        return await client.nodes(node).status.get()

# Usage
status = await get_node_info("pve1")
print(f"Node: {status.node}")
print(f"Status: {status.status}")
print(f"Uptime: {status.uptime} seconds")
print(f"CPU: {status.cpu * 100:.1f}%")
print(f"Memory: {status.memory.used / (1024**3):.2f}GB / {status.memory.total / (1024**3):.2f}GB")
```

### Processing VM List

```python
from prmxctrl.models.nodes import QemuVMResponse

async def list_vms(node: str) -> list[QemuVMResponse]:
    async with ProxmoxClient(...) as client:
        return await client.nodes(node).qemu.list()

# Usage
vms = await list_vms("pve1")
for vm in vms:
    print(f"VMID: {vm.vmid}")
    print(f"  Name: {vm.name}")
    print(f"  Status: {vm.status}")
    if vm.uptime:
        print(f"  Uptime: {vm.uptime}s")
```

### Validating User Input

```python
from pydantic import ValidationError

async def create_vm_safe(
    node: str, vmid: int, name: str, memory: int
):
    try:
        async with ProxmoxClient(...) as client:
            # Validation happens in the SDK
            result = await client.nodes(node).qemu.create(
                vmid=vmid,
                name=name,
                memory=memory
            )
            return result
    except ValidationError as e:
        # Handle validation errors
        for error in e.errors():
            print(f"Field {error['loc']}: {error['msg']}")
        return None
```

## Best Practices

### 1. Use Type Hints

```python
# ✅ Good - enables IDE features
from prmxctrl.models.nodes import NodeStatusResponse

status: NodeStatusResponse = await client.nodes("pve1").status.get()

# ❌ Bad - no type information
status = await client.nodes("pve1").status.get()
```

### 2. Leverage IDE Autocomplete

```python
# Type hints enable autocomplete:
status = await client.nodes("pve1").status.get()
status.  # Press Ctrl+Space to see available fields
```

### 3. Check Model Schema

```python
# Inspect schema before using
import json
from prmxctrl.models.nodes import NodeStatusResponse

print(json.dumps(
    NodeStatusResponse.model_json_schema(),
    indent=2
))
```

### 4. Handle Optional Fields

```python
# Check before accessing optional fields
status = await client.nodes("pve1").status.get()

if hasattr(status, 'description') and status.description:
    print(status.description)
```

### 5. Use List Comprehensions

```python
# Filter and transform model lists
nodes = await client.nodes.list()

# Get only online nodes
online = [n for n in nodes if n.status == "online"]

# Extract specific fields
node_names = [n.node for n in nodes]
```

## Converting Models to Dictionaries

If you need dict/JSON representation:

```python
status = await client.nodes("pve1").status.get()

# Convert to dictionary
status_dict = status.model_dump()

# Convert to JSON string
status_json = status.model_dump_json()

# With specific fields
subset = status.model_dump(include={'node', 'uptime', 'cpu'})
```

---

**See Also**: [Core Concepts](./03_CORE_CONCEPTS.md) | [API Reference](./04_API_REFERENCE.md) | [Examples](./06_EXAMPLES.md)
