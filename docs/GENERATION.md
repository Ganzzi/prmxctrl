# Code Generation Documentation

This document explains how prmxctrl generates its SDK from the Proxmox API schema.

## Overview

prmxctrl uses a code generation approach to create a complete, type-safe Python SDK from the official Proxmox API schema. This ensures the SDK stays up-to-date with API changes and maintains 100% coverage.

## Generation Pipeline

```
1. Schema Fetching     → 2. Schema Parsing     → 3. Code Generation
       ↓                        ↓                        ↓
   apidata.js             Structured dataclasses     Python SDK
   from GitHub                (Endpoint, Method,     (models/, endpoints/,
   (raw JSON)                 Parameter objects)      client.py)
```

## Step 1: Schema Fetching

### Source
- **URL**: `https://raw.githubusercontent.com/proxmox/pve-docs/master/api-viewer/apidata.js`
- **Format**: JavaScript file containing `const apiSchema = [...]`
- **Version**: Currently targets Proxmox v7.4-2

### Process
```python
# generator/fetch_schema.py
def fetch_schema() -> dict:
    """Fetch and parse the Proxmox API schema."""
    response = httpx.get(SCHEMA_URL)
    js_content = response.text

    # Extract JSON from JavaScript
    json_match = re.search(r'const apiSchema = (\[.*?\]);', js_content, re.DOTALL)
    schema = json.loads(json_match.group(1))

    return schema
```

### Caching
- Schema cached to `schemas/v7.4-2.json`
- Avoids repeated downloads during development
- Can be refreshed with `--force` flag

## Step 2: Schema Parsing

### Data Structures

```python
@dataclass
class Parameter:
    name: str
    type: str
    description: str | None = None
    optional: bool = False
    constraints: dict = field(default_factory=dict)

@dataclass
class Method:
    name: str  # GET, POST, PUT, DELETE
    parameters: list[Parameter]
    returns: str | None = None  # Return type description

@dataclass
class Endpoint:
    path: str  # "/nodes/{node}/qemu/{vmid}"
    methods: list[Method]
    description: str | None = None
```

### Parsing Logic

```python
# generator/parse_schema.py
def parse_endpoints(schema: dict) -> list[Endpoint]:
    """Parse raw schema into structured Endpoint objects."""
    endpoints = []

    for api_path, api_data in schema.items():
        # Parse path parameters: /nodes/{node}/qemu/{vmid}
        # Extract methods and their parameters
        # Build hierarchical structure

    return endpoints
```

### Path Parameter Handling

Proxmox uses URL templates with parameters:
- `/nodes/{node}/qemu/{vmid}` → `nodes("node").qemu(vmid)`
- `/cluster/firewall/rules/{rule}` → `cluster.firewall.rules(rule)`

### Dynamic Parameters

Some endpoints use patterns like `link[n]` to represent multiple indexed parameters:
- `link[n]` expands to `link0`, `link1`, `link2`, ..., `link7`
- Handled by `_expand_dynamic_parameters()` method

## Step 3: Code Generation

### Model Generation

**Input**: Parameter definitions from schema
**Output**: Pydantic v2 model classes

```python
# Example generated model
class VMConfig(BaseModel):
    """Configuration for a QEMU virtual machine."""

    model_config = ConfigDict(extra='forbid')

    name: Optional[str] = Field(default=None, description="Name of the VM")
    memory: int = Field(description="Memory in MB")
    cores: int = Field(ge=1, le=128, description="Number of CPU cores")
    net0: Optional[str] = Field(default=None, description="Network interface 0")
```

**Type Mapping**:
- `string` → `str`
- `integer` → `int`
- `boolean` → `bool`
- `array` → `List[T]`
- Custom formats → Specific types (`pve-node`, `pve-vmid`, etc.)

**Constraint Mapping**:
- `minimum`/`maximum` → `ge`/`le` Field parameters
- `pattern` → `pattern` regex validation
- `enum` → `Literal["value1", "value2"]`
- `maxLength` → `max_length`

### Endpoint Generation

**Input**: Endpoint definitions with methods
**Output**: Hierarchical class structure

```python
# Example generated endpoint
class QemuEndpoint(EndpointBase):
    """QEMU virtual machine operations."""

    def __init__(self, client: HTTPClient, node: str, vmid: int):
        super().__init__(client)
        self._node = node
        self._vmid = vmid

    def _build_path(self) -> str:
        return f"/nodes/{self._node}/qemu/{self._vmid}"

    async def config(self) -> VMConfig:
        """Get virtual machine configuration."""
        return await self._get("config", VMConfig)

    async def create(self, config: VMConfigCreate) -> TaskResponse:
        """Create a virtual machine."""
        return await self._post("config", config, TaskResponse)
```

**Hierarchy Creation**:
- Root endpoints: `client.nodes`, `client.cluster`
- Callable endpoints: `client.nodes("pve1")` → `NodeEndpoint`
- Nested endpoints: `client.nodes("pve1").qemu(100)` → `QemuEndpoint`

### Client Generation

**Input**: List of root endpoints
**Output**: Main `ProxmoxClient` class

```python
class ProxmoxClient(HTTPClient):
    """Main client for the Proxmox VE API."""

    @property
    def cluster(self) -> ClusterEndpoint:
        """Cluster management endpoints."""
        return ClusterEndpoint(self._client)

    @property
    def nodes(self) -> NodesEndpoint:
        """Node management endpoints."""
        return NodesEndpoint(self._client)
```

## Template System

### Jinja2 Templates

Templates are stored in `generator/templates/`:

- `model.py.jinja` - Single model class template
- `endpoint.py.jinja` - Endpoint class template
- `client.py.jinja` - Main client template

### Template Variables

```python
# Model template context
{
    "model_name": "VMConfig",
    "docstring": "Configuration for a QEMU VM",
    "fields": [
        {
            "name": "memory",
            "type": "int",
            "constraints": {"ge": 128, "le": 1048576},
            "description": "Memory in MB"
        }
    ]
}
```

## Generation Commands

### Full Generation

```bash
python tools/generate.py
```

This runs the complete pipeline:
1. Fetch/update schema
2. Parse into dataclasses
3. Generate models
4. Generate endpoints
5. Generate client
6. Format code with black/ruff

### Validation

```bash
python tools/validate.py
```

Validates generated code:
- Syntax checking (AST compilation)
- Import resolution
- mypy type checking
- ruff linting

## Customization

### Adding New Types

1. Update `generator/generators/type_mapper.py`
2. Add mapping for new Proxmox format
3. Regenerate code

### Modifying Templates

1. Edit `generator/templates/*.jinja`
2. Test with small schema subset
3. Regenerate and validate

### Schema Extensions

1. Modify `generator/parse_schema.py`
2. Add new parsing logic
3. Update dataclasses if needed
4. Regenerate code

## Troubleshooting

### Common Issues

**Schema parsing fails**:
- Check if Proxmox updated their schema format
- Verify network connectivity to GitHub
- Check for JavaScript syntax changes

**Type mapping errors**:
- New constraint types in schema
- Unknown format strings
- Invalid parameter combinations

**Import errors in generated code**:
- Missing imports in templates
- Circular import issues
- Type annotation problems

**mypy errors**:
- Incompatible type annotations
- Missing type stubs
- Complex generic types

### Debugging

1. **Check schema parsing**:
   ```bash
   python -c "from generator.parse_schema import parse_endpoints; print(parse_endpoints(fetch_schema())[:5])"
   ```

2. **Test single endpoint generation**:
   ```bash
   python -c "from generator.generators.endpoint_generator import generate_endpoint; print(generate_endpoint(endpoint))"
   ```

3. **Validate single file**:
   ```bash
   python -m py_compile prmxctrl/models/cluster.py
   mypy prmxctrl/models/cluster.py
   ```

## Performance

### Generation Speed
- Schema parsing: ~2 seconds
- Model generation: ~5 seconds (909 models)
- Endpoint generation: ~10 seconds (284 endpoints)
- Total: ~20 seconds for full generation

### Memory Usage
- Schema JSON: ~2MB
- Parsed dataclasses: ~5MB
- Generated code: ~50MB total

### Optimization Opportunities
- Parallel generation for large schemas
- Incremental regeneration
- Template precompilation

## Future Enhancements

### Multi-Version Support
- Generate SDKs for multiple Proxmox versions
- Version-specific type mappings
- Backward compatibility handling

### Advanced Features
- Streaming response support
- Automatic retries with backoff
- Request/response middleware

### Developer Tools
- Interactive schema explorer
- Code generation debugging tools
- Performance profiling

## Maintenance

### Schema Updates
1. Monitor Proxmox release notes
2. Update schema URL when new versions release
3. Test generation with new schema
4. Update version constraints

### Template Updates
1. Review generated code quality regularly
2. Update templates for new Python features
3. Optimize for performance

### Tool Updates
1. Keep dependencies updated
2. Monitor for breaking changes in Pydantic/Jinja2
3. Update CI/CD configurations