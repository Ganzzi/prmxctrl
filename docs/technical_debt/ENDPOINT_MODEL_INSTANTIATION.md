# Technical Debt: Endpoint Model Instantiation

## Issue Summary

Generated endpoint methods return raw `dict` objects instead of properly instantiated Pydantic model instances, breaking type safety and runtime validation.

## Impact

### Type Safety
- **Current**: Methods return `dict[str, Any]`, losing all type information
- **Impact**: No compile-time type checking for API response handling
- **Risk**: Runtime type errors when accessing response data

### Runtime Validation
- **Current**: No validation of API response structure
- **Impact**: Invalid API responses pass through unchecked
- **Risk**: Silent data corruption or unexpected behavior

### Developer Experience
- **Current**: No IDE autocomplete for response fields
- **Impact**: Manual API documentation lookup required
- **Risk**: Increased development time and errors

## Root Cause

The endpoint code generation template (`generator/templates/endpoint.py.jinja`) generates methods like:

```python
# Current (incorrect)
async def get_cluster_status(self) -> Cluster_StatusGETResponse:
    return await self._get("status")  # Returns dict
```

Instead of:

```python
# Correct
async def get_cluster_status(self) -> Cluster_StatusGETResponse:
    data = await self._get("status")  # Returns dict
    return Cluster_StatusGETResponse(**data)  # Instantiate model
```

## Affected Code

- **Template**: `generator/templates/endpoint.py.jinja`
- **Generator**: `generator/generators/endpoint_generator.py`
- **Files**: All generated endpoint methods (~284 endpoints)
- **Coverage**: 100% of API response methods

## Current Workaround

The `pyproject.toml` mypy configuration excludes generated endpoints:

```toml
exclude = [
    "prmxctrl/endpoints/*/*/*", # Exclude deeply nested directories
]

[[tool.mypy.overrides]]
module = "prmxctrl.endpoints.*.*"
ignore_errors = true
```

This masks the problem but doesn't solve it.

## Technical Debt Metrics

- **Severity**: High
- **Scope**: ~284 endpoint methods
- **Impact**: Type safety, runtime validation, developer experience
- **Effort**: Medium (template changes + regeneration)
- **Risk**: Low (changes are localized to generation)

## Resolution Plan

### Phase 1: Template Update
1. Modify `endpoint.py.jinja` to instantiate models from response data
2. Add error handling for model instantiation failures
3. Handle partial response data gracefully

### Phase 2: Testing
1. Regenerate all endpoints
2. Run full mypy check to verify type safety
3. Test runtime validation with mock API responses

### Phase 3: Configuration Cleanup
1. Remove mypy exclusions
2. Update CI/CD to run full type checking
3. Add type coverage metrics

## Benefits After Resolution

### Type Safety
- 100% type coverage across entire SDK
- Compile-time error detection for API misuse
- IDE autocomplete for all response fields

### Runtime Safety
- Automatic validation of all API responses
- Early detection of API contract changes
- Consistent error handling for malformed data

### Developer Experience
- Complete type hints throughout the codebase
- Self-documenting API through types
- Reduced time spent on API integration

## Dependencies

- Requires Pydantic models to be correctly generated
- Depends on stable API response schemas
- Needs error handling strategy for validation failures

## Related Issues

- Type checking exclusions in `pyproject.toml`
- Unused `# type: ignore` comments in generated code
- Import analysis issues in complex endpoint hierarchies

## Success Criteria

1. All endpoint methods return proper model instances
2. Full mypy coverage (346/346 files) with zero errors
3. Runtime validation catches invalid API responses
4. IDE provides complete autocomplete for API responses
5. CI/CD enforces type safety on all changes

## Timeline

- **Estimated Effort**: 2-3 days
- **Priority**: High (blocks full type safety)
- **Dependencies**: None (can be done incrementally)
- **Risk**: Low (changes isolated to code generation)