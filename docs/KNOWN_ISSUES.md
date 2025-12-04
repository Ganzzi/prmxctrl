# Known Issues and Fixes

## Issue #1: Field Name Serialization (FIXED in v0.1.2)

### Problem
Parameters with hyphens in their names (e.g., `generate-password`) are converted to underscores for Python compatibility (e.g., `generate_password`). However, when these fields are serialized to send to the Proxmox API, they were using the Python name instead of the original API parameter name.

**Error Example:**
```
b'{"data":null,"errors":{"generate_password":"property is not defined in schema and the schema does not allow additional properties"}}'
```

The API expects `generate-password` but was receiving `generate_password`.

### Root Cause
- The code generator sanitized field names for Python (hyphens → underscores)
- No `serialization_alias` was added to Pydantic Field definitions
- When models were serialized to JSON/form data, they used the Python field names
- Endpoints used `model_dump(exclude_none=True)` without `by_alias=True`

### Solution
Three fixes were applied:

1. **Model Generator** (`generator/generators/model_generator.py`):
   - Added `original_name` field to `ModelField` dataclass to track sanitized vs original names
   - When a field name is sanitized (e.g., hyphens to underscores), automatically add `serialization_alias` pointing to the original API parameter name

2. **Endpoint Generator** (`generator/generators/endpoint_generator.py`):
   - Added `by_alias=True` to all `model_dump()` calls to ensure serialization uses aliases

3. **Model Template** (`generator/templates/model.py.jinja`):
   - Added `populate_by_name=True` to `ConfigDict` to allow both names during deserialization

**Example Generated Model:**
```python
class Nodes_Node_Qemu_Vmid_VncproxyPOSTRequest(BaseModel):
    # Python field name: generate_password
    # API parameter name: generate-password
    # Serialization will use: generate-password
    generate_password: bool | int | str | None = Field(
        default=0,
        serialization_alias="generate-password",  # ← Added by generator
        description="Generates a random password to be used as ticket...",
    )
    
    model_config = ConfigDict(extra="forbid", validate_assignment=True, populate_by_name=True)
```

### Status
✅ **FIXED in v0.1.2** - Code generator now automatically:
1. Adds `serialization_alias` for all fields where the Python field name differs from the original API parameter name
2. Uses `by_alias=True` when serializing models to API requests
3. Supports both names during deserialization with `populate_by_name=True`

### Affected Parameters
This fix affects all Proxmox API parameters with special characters that get sanitized:
- `generate-password` → `generate_password`
- Any other parameters with hyphens, dots, or other non-Python-identifier characters

### Technical Details
Pydantic v2 uses `serialization_alias` to specify the field name when serializing models to dictionaries/JSON. Combined with `by_alias=True` in `model_dump()`, this allows:
- Python code to use `snake_case` field names (idiomatic Python)
- API communication to use original parameter names (required by Proxmox API)
- Automatic conversion between the two during serialization
