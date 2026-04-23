# prmxctrl API Documentation Index

**Version**: 1.0.0 | **SDK**: prmxctrl | **Proxmox VE**: 7.4.2 | **Updated**: December 2025

## Quick Start

New to prmxctrl? Start here:

1. **[Getting Started](./01-getting-started.md)** (10 min read)
   - Installation and environment setup
   - Your first API call
   - Basic concepts

2. **[Authentication](./02-authentication.md)** (10 min read)
   - Password and API token authentication
   - Creating API tokens
   - Security best practices

3. **[Examples](./06-examples.md)** (Reference)
   - Copy-paste code examples
   - Common administrative tasks
   - Real-world scenarios

## Core Documentation

### Understanding the SDK

- **[Core Concepts](./03-core-concepts.md)** - Architecture and design patterns
  - SDK layering and components
  - Hierarchical endpoint navigation
  - Type safety with Pydantic
  - Async/await patterns
  - Request/response models

### API Reference

- **[API Reference](./04-api-reference.md)** - Complete endpoint documentation
  - All 6 major API categories (Cluster, Nodes, Storage, Access, Pools, Version)
  - 280+ endpoints organized by function
  - HTTP method mapping
  - Status codes and responses

### Data Models

- **[Data Models](./05-data-models.md)** - Request and response models
  - Understanding Pydantic v2 models
  - Model categories and structure
  - Type hints and validation
  - Converting models to dictionaries

## Advanced Topics

### Error Handling

- **[Error Handling](./07-error-handling.md)** - Exception handling guide
  - Exception types and hierarchy
  - Handling specific errors
  - Retry patterns
  - Timeout management
  - Common error scenarios

### Advanced Usage

- **[Advanced Usage](./08-advanced-usage.md)** - Production patterns
  - Connection pooling
  - Async patterns (concurrent, producer-consumer)
  - Performance optimization
  - Task monitoring
  - Custom HTTP configuration
  - Type safety with mypy
  - Production deployment

## Documentation Map

```
📚 Documentation Structure
├── 01-getting-started.md
│   ├── Installation
│   ├── Environment Setup
│   └── First API Call
│
├── 02-authentication.md
│   ├── Password Auth
│   ├── API Tokens
│   └── Security
│
├── 03-core-concepts.md
│   ├── Architecture
│   ├── Hierarchical Endpoints
│   ├── Type Safety
│   └── Async Patterns
│
├── 04-api-reference.md
│   ├── Cluster APIs (45+)
│   ├── Node APIs (120+)
│   ├── Storage APIs (25+)
│   ├── Access APIs (35+)
│   ├── Pool APIs (10+)
│   └── Version APIs (5+)
│
├── 05-data-models.md
│   ├── Model Overview
│   ├── Model Categories
│   ├── Type Hints
│   └── Validation
│
├── 06-examples.md
│   ├── Cluster Management
│   ├── Node Management
│   ├── VM Operations
│   ├── Container Operations
│   ├── Storage Management
│   ├── User Management
│   ├── Monitoring
│   └── Advanced Operations
│
├── 07-error-handling.md
│   ├── Exception Types
│   ├── Error Patterns
│   ├── Retry Logic
│   └── Troubleshooting
│
└── 08-advanced-usage.md
    ├── Performance
    ├── Async Patterns
    ├── Production Patterns
    └── Best Practices
```

## API Coverage

The SDK provides type-safe access to **284 endpoints** across Proxmox VE 7.4.2:

| Category | Endpoints | Key Functions |
|----------|-----------|---------------|
| **Cluster** | 45+ | Status, Resources, HA, Backup, Replication |
| **Nodes** | 120+ | Status, QEMU VMs, LXC Containers, Disks |
| **Storage** | 25+ | List, Status, Content, Prune |
| **Access** | 35+ | Users, Groups, Roles, Permissions, Tokens |
| **Pools** | 10+ | Create, List, Manage |
| **Version** | 5+ | API Info, Version |
| **TOTAL** | **284+** | Full Proxmox VE API coverage |

## Finding What You Need

### By Task

| Task | Documentation |
|------|---------------|
| Install SDK | [Getting Started](./01-getting-started.md#installation) |
| Authenticate | [Authentication](./02-authentication.md) |
| List resources | [Examples - Cluster Management](./06-examples.md#cluster-management) |
| Create VM | [Examples - VM Operations](./06-examples.md#create-a-new-vm) |
| Handle errors | [Error Handling](./07-error-handling.md) |
| Optimize performance | [Advanced Usage - Performance](./08-advanced-usage.md#performance-optimization) |
| Type checking | [Advanced Usage - Type Safety](./08-advanced-usage.md#type-safety-and-mypy) |
| Production deploy | [Advanced Usage - Production](./08-advanced-usage.md#production-deployment) |

### By API Endpoint

| Endpoint | Documentation |
|----------|---------------|
| `/cluster/*` | [API Reference - Cluster](./04-api-reference.md#1-cluster-endpoints) |
| `/nodes/*` | [API Reference - Nodes](./04-api-reference.md#2-nodes-endpoints) |
| `/storage/*` | [API Reference - Storage](./04-api-reference.md#3-storage-endpoints) |
| `/access/*` | [API Reference - Access](./04-api-reference.md#4-access-endpoints) |
| `/pools/*` | [API Reference - Pools](./04-api-reference.md#5-pools-endpoints) |
| `/version/*` | [API Reference - Version](./04-api-reference.md#6-version-endpoints) |

### By Problem

| Problem | Solution |
|---------|----------|
| "Can't connect" | [Troubleshooting](./01-getting-started.md#troubleshooting) |
| "Invalid credentials" | [Authentication](./02-authentication.md#troubleshooting-authentication) |
| "Permission denied" | [Access Control](./04-api-reference.md#4-access-endpoints) |
| "Operation timed out" | [Timeout Handling](./07-error-handling.md#timeout-handling) |
| "Slow performance" | [Performance Optimization](./08-advanced-usage.md#performance-optimization) |
| "Type errors in IDE" | [Type Safety](./08-advanced-usage.md#type-safety-and-mypy) |

## Key Features Highlight

✅ **100% Type Safe**
- Full type hints with mypy --strict compliance
- IDE autocomplete and validation
- Pydantic v2 validation on all models

✅ **Async/Await Support**
- Modern async HTTP client with httpx
- Connection pooling
- Concurrent operations support

✅ **Hierarchical API**
- Navigate like `client.nodes("pve1").qemu(100).config.get()`
- Intuitive, discoverable API design
- Mirrors Proxmox API structure

✅ **Fully Auto-Generated**
- Generated from official Proxmox API schema
- 284 endpoints covered
- Stays up-to-date with API changes

✅ **Production Ready**
- Full error handling with specific exception types
- Retry patterns and timeout management
- Logging and monitoring support

✅ **Comprehensive Documentation**
- 8 documentation files
- 50+ code examples
- Best practices and patterns

## Common Patterns

### Basic Usage
```python
async with ProxmoxClient(...) as client:
    status = await client.cluster.status.get()
```

### Error Handling
```python
try:
    result = await client.cluster.status.get()
except ProxmoxAPIError as e:
    print(f"Error: {e.status_code} - {e.message}")
```

### Concurrent Operations
```python
results = await asyncio.gather(
    client.nodes.list(),
    client.storage.list(),
    client.cluster.status.get()
)
```

### Type Safety
```python
from prmxctrl.models.nodes import NodeStatusResponse

status: NodeStatusResponse = await client.nodes("pve1").status.get()
print(status.cpu)  # IDE knows this is float
```

## Learning Path

**Beginner** (0-30 minutes)
1. Read [Getting Started](./01-getting-started.md)
2. Read [Authentication](./02-authentication.md)
3. Try examples from [Examples](./06-examples.md)

**Intermediate** (30 minutes - 2 hours)
1. Study [Core Concepts](./03-core-concepts.md)
2. Review [API Reference](./04-api-reference.md)
3. Reference [Data Models](./05-data-models.md)

**Advanced** (2+ hours)
1. Master [Error Handling](./07-error-handling.md)
2. Learn [Advanced Usage](./08-advanced-usage.md)
3. Implement production patterns

## IDE Setup

For best IDE support:

1. **Type Hints**
   ```python
   from prmxctrl.models.nodes import NodeStatusResponse
   status: NodeStatusResponse = await client.nodes("pve1").status.get()
   ```

2. **mypy Checking**
   ```bash
   mypy --strict your_script.py
   ```

3. **Autocomplete**
   - Import models explicitly for full autocomplete
   - Use `await client.` to see available endpoints

## SDK Compatibility

- **Python**: 3.10+
- **Proxmox VE**: 7.4.2 (primary target, may work with other versions)
- **Type Checking**: mypy --strict compatible
- **Linting**: ruff compatible

## Get Help

1. **Check [Examples](./06-examples.md)** - Common patterns
2. **Read [Error Handling](./07-error-handling.md)** - Troubleshooting
3. **Review [Core Concepts](./03-core-concepts.md)** - Understanding the SDK
4. **Check [Proxmox API Docs](https://pve.proxmox.com/wiki/Proxmox_VE_API2)** - Official documentation

## SDK Information

- **Project**: prmxctrl
- **Repository**: [GitHub](https://github.com/Ganzzi/prmxctrl)
- **License**: MIT
- **Type Checking**: Strict mypy compliance
- **Code Generation**: Full SDK auto-generated from schema

## Documentation Statistics

- **Total Files**: 8 markdown files + index
- **Total Words**: 15,000+
- **Code Examples**: 100+
- **API Endpoints Covered**: 284+
- **Endpoints by Category**: 6 major categories
- **Topics Covered**: 15+ major topics

---

**Last Updated**: December 2025  
**SDK Version**: 1.0.0  
**Proxmox Version**: 7.4.2

**Quick Links**: [README](./README.md) | [Getting Started](./01-getting-started.md) | [API Reference](./04-api-reference.md) | [Examples](./06-examples.md)
