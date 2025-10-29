# Architecture Documentation

## Overview

prmxctrl is a fully auto-generated, type-safe Python SDK for the Proxmox Virtual Environment API. The architecture emphasizes code generation, type safety, and modern Python patterns.

## Core Principles

### 1. Code Generation First
- **Why**: Proxmox API is large (~600 endpoints) and evolves with each release
- **How**: Auto-generate 99% of the SDK from the official API schema
- **Benefit**: Always up-to-date, zero manual maintenance for API changes

### 2. 100% Type Safety
- **Why**: Proxmox API has complex parameter validation requirements
- **How**: Pydantic v2 models with mypy --strict compliance
- **Benefit**: Catch errors at development time, not runtime

### 3. Hierarchical API Design
- **Why**: Proxmox API is naturally hierarchical (`/nodes/{node}/qemu/{vmid}`)
- **How**: Generated classes mirror the URL structure
- **Benefit**: Intuitive navigation, discoverable API

### 4. Modern Python Patterns
- **Why**: Async/await is the future of Python networking
- **How**: httpx for async HTTP, context managers, type hints everywhere
- **Benefit**: Performant, idiomatic Python code

## Architecture Layers

```
┌─────────────────┐
│   ProxmoxClient │  ← Main entry point
├─────────────────┤
│   Endpoints     │  ← Generated hierarchical classes
├─────────────────┤
│   Models        │  ← Pydantic v2 validation
├─────────────────┤
│   Base Classes  │  ← Hand-written infrastructure
├─────────────────┤
│   HTTP Client   │  ← httpx with auth & pooling
└─────────────────┘
```

### HTTP Client Layer (`prmxctrl/base/http_client.py`)

**Responsibilities:**
- Authentication (password tickets, API tokens)
- CSRF token handling
- Connection pooling
- SSL verification control
- Request/response lifecycle

**Key Classes:**
- `HTTPClient`: Base async HTTP client with authentication

### Base Classes Layer (`prmxctrl/base/`)

**Responsibilities:**
- Common functionality for generated code
- Exception hierarchy
- Type definitions
- Path building utilities

**Key Classes:**
- `EndpointBase`: Base class for all generated endpoints
- `ProxmoxError`: Exception hierarchy
- Custom types for Proxmox formats

### Models Layer (`prmxctrl/models/`)

**Responsibilities:**
- Request parameter validation
- Response data validation
- Type-safe data structures

**Generated From:**
- Proxmox API schema parameter definitions
- Response type specifications

**Key Features:**
- Pydantic v2 with ConfigDict(forbid_extra=True)
- Full constraint mapping (min/max, patterns, enums)
- Nested object support

### Endpoints Layer (`prmxctrl/endpoints/`)

**Responsibilities:**
- Hierarchical API navigation
- HTTP method implementation
- Path parameter substitution

**Generated From:**
- Proxmox API endpoint paths
- HTTP method definitions
- Parameter specifications

**Key Patterns:**
- Callable classes: `nodes("pve1")` returns node-specific endpoints
- Property navigation: `client.nodes.qemu` for sub-resources
- Method generation: `get()`, `create()`, `update()`, `delete()`

### Client Layer (`prmxctrl/client.py`)

**Responsibilities:**
- Main entry point for users
- Root endpoint properties
- Context manager support

**Generated From:**
- List of root API endpoints
- Authentication configuration

## Code Generation Pipeline

```
Proxmox API Schema (apidata.js)
        ↓
Schema Parser (parse_schema.py)
        ↓
Structured Data (dataclasses)
        ↓
├── Model Generator (model_generator.py)
│   └── Pydantic Models (models/*.py)
├── Endpoint Generator (endpoint_generator.py)
│   └── Hierarchical Classes (endpoints/*)
└── Client Generator (client_generator.py)
    └── ProxmoxClient (client.py)
```

### Schema Processing

1. **Fetch Schema**: Load `apidata.js` from Proxmox repository
2. **Parse JavaScript**: Extract JSON schema from `const apiSchema = [...]`
3. **Validate Structure**: Ensure schema integrity
4. **Cache**: Store as `schemas/v7.4-2.json`

### Model Generation

1. **Type Mapping**: Convert Proxmox types to Python types
2. **Constraint Mapping**: Map validation rules to Pydantic Field parameters
3. **Template Rendering**: Use Jinja2 to generate model classes
4. **File Organization**: Group models by API module

### Endpoint Generation

1. **Hierarchy Analysis**: Build tree structure from API paths
2. **Class Generation**: Create classes for each path level
3. **Method Generation**: Add HTTP methods with proper signatures
4. **Callable Support**: Implement `__call__` for parameter substitution

### Client Integration

1. **Root Properties**: Generate properties for top-level endpoints
2. **Import Management**: Ensure all generated code is properly imported
3. **Documentation**: Add usage examples and docstrings

## Design Decisions

### Why Pydantic v2?
- **Modern**: Latest Pydantic with improved performance
- **Strict**: `ConfigDict(extra='forbid')` catches typos
- **Typed**: Better mypy integration
- **Validated**: Runtime validation of all data

### Why httpx?
- **Async**: Native async/await support
- **Modern**: Active development, great performance
- **Features**: Connection pooling, timeouts, retries
- **Standards**: Follows HTTP standards properly

### Why Code Generation?
- **Maintenance**: API changes don't require manual updates
- **Consistency**: All endpoints follow the same patterns
- **Coverage**: 100% API coverage without manual work
- **Quality**: Generated code is more consistent than manual

### Why Hierarchical Classes?
- **Discovery**: IDE autocomplete shows available operations
- **Safety**: Type system prevents invalid API calls
- **Intuitive**: Mirrors the mental model of the API
- **Composable**: Easy to build complex operations

## File Organization

```
prmxctrl/
├── __init__.py          # Package exports
├── client.py            # Generated main client
├── base/                # Hand-written infrastructure
│   ├── __init__.py
│   ├── exceptions.py    # Exception hierarchy
│   ├── http_client.py   # HTTP client base
│   ├── endpoint_base.py # Endpoint base class
│   └── types.py         # Type definitions
├── models/              # Generated Pydantic models
│   ├── __init__.py
│   ├── access.py
│   ├── cluster.py
│   └── ...
├── endpoints/           # Generated endpoint classes
│   ├── __init__.py
│   ├── access.py
│   ├── cluster.py
│   ├── nodes.py
│   ├── nodes/
│   │   ├── _item.py     # Per-node endpoints
│   │   ├── qemu/
│   │   └── ...
│   └── ...
└── ...

generator/               # Code generation tools
├── __init__.py
├── parse_schema.py      # Schema parsing
├── analyze_schema.py    # Schema analysis
├── generators/
│   ├── __init__.py
│   ├── type_mapper.py   # Type mapping logic
│   ├── model_generator.py
│   ├── endpoint_generator.py
│   └── client_generator.py
└── templates/           # Jinja2 templates
    ├── model.py.jinja
    ├── endpoint.py.jinja
    └── client.py.jinja

tools/                   # CLI utilities
├── generate.py          # Main generation script
├── validate.py          # Validation script
└── ...

tests/                   # Test suite
├── conftest.py
├── test_base.py
├── test_generated_models.py
├── test_endpoint_generation.py
└── ...

schemas/                 # Cached API schemas
└── v7.4-2.json

docs/                    # Documentation
├── plan/
│   ├── v1.md           # Original plan
│   └── v1_checklist.md # Implementation checklist
└── SCHEMA_ANALYSIS.md   # Schema analysis results
```

## Performance Considerations

### Memory Usage
- **Lazy Loading**: Endpoints created on-demand
- **Shared Models**: Reuse common model classes
- **Efficient Parsing**: httpx with connection pooling

### Type Checking
- **Incremental**: mypy can check files independently
- **Cached**: .mypy_cache avoids re-checking unchanged files
- **Strict**: All type issues caught at development time

### Generation Speed
- **Template Caching**: Jinja2 templates compiled once
- **Parallel Processing**: Could be added for large schemas
- **Incremental**: Only regenerate changed endpoints

## Future Enhancements

### Multiple API Versions
- Support Proxmox v7.x, v8.x, v9.x
- Version-specific code generation
- Backward compatibility handling

### Advanced Features
- Streaming responses for large downloads
- Automatic token refresh
- Rate limiting and backoff
- Prometheus metrics integration

### Developer Experience
- CLI tool with shell completion
- Interactive API explorer
- Better error messages
- Performance profiling tools