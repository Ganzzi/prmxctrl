# Changelog

All notable changes to prmxctrl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-29

### Added
- **Complete Proxmox VE API SDK**: Auto-generated from Proxmox v7.4-2 API schema
- **284 API Endpoints**: Full coverage of Proxmox VE API including:
  - Cluster management (`/cluster/*`)
  - Node operations (`/nodes/{node}/*`)
  - QEMU VM management (`/nodes/{node}/qemu/{vmid}/*`)
  - LXC container management (`/nodes/{node}/lxc/{vmid}/*`)
  - Storage operations (`/storage/*`)
  - Access control (`/access/*`)
  - Pool management (`/pools/*`)
- **909 Pydantic Models**: Type-safe request/response validation
- **Hierarchical API Design**: Navigate API like `client.nodes("pve1").qemu(100).config.get()`
- **Async/Await Support**: Modern Python async HTTP client using httpx
- **Authentication Methods**:
  - Password-based authentication with ticket/CSRF tokens
  - API token authentication
- **Type Safety**: 100% mypy --strict compliance with full type hints
- **Validation**: Pydantic v2 models with comprehensive constraint mapping
- **Error Handling**: Custom exception hierarchy for different error types
- **Code Generation Pipeline**: Automated SDK generation from API schema
- **Comprehensive Testing**: 57 tests with 100% pass rate
- **Documentation**: Complete README, architecture docs, and contribution guidelines

### Technical Features
- **HTTP Client**: httpx-based with connection pooling, SSL verification control
- **Path Parameter Validation**: Runtime validation of path parameters
- **Dynamic Parameter Expansion**: Support for Proxmox patterns like `link[n]`
- **Custom Type Mapping**: Proxmox-specific formats (pve-node, pve-vmid, etc.)
- **Constraint Mapping**: Full mapping of API constraints to Pydantic validators
- **Context Manager Support**: Proper async context management
- **Import Optimization**: Efficient package structure with proper exports

### Development Tools
- **Code Generation**: `tools/generate.py` for complete SDK regeneration
- **Validation**: `tools/validate.py` for code quality checks
- **Testing**: pytest with async support and comprehensive test coverage
- **Type Checking**: mypy --strict with zero errors
- **Linting**: ruff with zero violations
- **Formatting**: black code formatting

### Quality Metrics
- **Type Coverage**: 100% (mypy --strict)
- **Test Coverage**: Comprehensive test suite (57 tests, 1 skipped)
- **Code Quality**: 0 linting errors, 0 type checking errors
- **Package Integrity**: Successful build and import validation

### Dependencies
- **Runtime**: `pydantic>=2.0.0`, `httpx>=0.24.0`
- **Development**: `pytest>=7.0.0`, `pytest-asyncio>=0.21.0`, `mypy>=1.0.0`, `ruff>=0.1.0`, `black>=23.0.0`

### Known Limitations
- Supports Proxmox VE v7.4-2 API schema
- Requires Python 3.10+
- Self-signed SSL certificates need explicit verification disable

### Future Plans
- Support for multiple Proxmox API versions
- Streaming response support for large file operations
- Automatic token refresh
- CLI tool for SDK operations
- Web documentation site

---

## Development History

This SDK was developed following a comprehensive 7-phase implementation plan:

### Phase 1: Schema Processing ✅
- Parsed Proxmox API schema from `apidata.js`
- Built hierarchical endpoint tree
- Extracted all parameters and constraints

### Phase 2: Base Framework ✅
- Implemented HTTP client with authentication
- Created base classes and exception hierarchy
- Set up development tools and testing infrastructure

### Phase 3: Model Generation ✅
- Generated 909 Pydantic v2 models
- Mapped all Proxmox types and constraints
- Achieved 100% type safety

### Phase 4: Endpoint Generation ✅
- Generated 284 endpoint classes
- Implemented hierarchical navigation
- Added callable pattern support

### Phase 5: Client Integration ✅
- Created main ProxmoxClient class
- Integrated all components
- Added comprehensive testing

### Phase 6: Testing & Validation ✅
- Achieved 100% mypy compliance
- Zero linting errors
- Full test suite passing

### Phase 7: Documentation & Polish ✅
- Created comprehensive documentation
- Package distribution ready
- Ready for public release

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT License