# prmxctrl API Documentation

**Version:** 1.0.0 | **Proxmox VE:** 7.4.2

Welcome to the comprehensive API documentation for the prmxctrl Python SDK. This documentation covers all aspects of the Proxmox Virtual Environment API as implemented in the SDK.

## Quick Navigation

- **[Getting Started](./01-getting-started.md)** - Installation and basic usage
- **[Authentication](./02-authentication.md)** - Authentication methods and security best practices
- **[Core Concepts](./03-core-concepts.md)** - Key concepts and patterns
- **[API Reference](./04-api-reference.md)** - Detailed endpoint reference
- **[Data Models](./05-data-models.md)** - Request/response model documentation
- **[Examples](./06-examples.md)** - Practical usage examples
- **[Error Handling](./07-error-handling.md)** - Exception handling and error recovery
- **[Advanced Usage](./08-advanced-usage.md)** - Advanced patterns and optimization

## Documentation Overview

### 1. Getting Started
Installation instructions, environment setup, and your first API call.

### 2. Authentication
Detailed guide on password and API token authentication methods.

### 3. Core Concepts
Understanding the SDK structure, hierarchical endpoints, and type safety.

### 4. API Reference
Complete reference to all Proxmox API endpoints organized by category:
- **Cluster** - Cluster management, status, and configuration
- **Nodes** - Node operations, VM/container management
- **Storage** - Storage operations and management
- **Access** - User, permission, and ACL management
- **Pools** - Pool management
- **Version** - API version information

### 5. Data Models
Comprehensive guide to all Pydantic models used for request/response validation.

### 6. Examples
Real-world usage examples covering common tasks:
- Listing resources
- Creating VMs
- Managing containers
- Monitoring cluster health
- User and permission management

### 7. Error Handling
Understanding and handling various error conditions and exceptions.

### 8. Advanced Usage
Advanced patterns including custom headers, connection pooling, and performance optimization.

## API Endpoints by Category

### Cluster Management
```python
client.cluster.*
```
- Cluster status and information
- Backup and restore operations
- Replication management
- Job scheduling
- HA (High Availability) configuration
- SDN (Software Defined Networking)
- ACME certificate management
- Metrics and monitoring
- Firewall configuration

### Node Operations
```python
client.nodes(node).*
```
- Node status and information
- QEMU VM management
- LXC container management
- Storage operations
- Network configuration
- System services

### Storage Management
```python
client.storage.*
```
- Storage availability status
- Storage content operations
- Storage configuration

### User & Access Control
```python
client.access.*
```
- User account management
- Group management
- Role and permission management
- API token management
- TFA (Two-Factor Authentication) configuration
- Domain and realm management

### Resource Pooling
```python
client.pools.*
```
- Pool creation and management
- Pool membership

### Version Information
```python
client.version.*
```
- API version and server information

## Key Features

✅ **100% Type Safe** - Full type hints with mypy --strict compliance  
✅ **Auto-Generated** - Complete SDK generated from official Proxmox API schema  
✅ **Async/Await** - Modern async HTTP client with connection pooling  
✅ **Hierarchical** - Navigate API like `client.nodes("pve1").qemu(100).config.get()`  
✅ **Validated** - Pydantic v2 models ensure data integrity  
✅ **Comprehensive** - 284 endpoints covering Proxmox VE 7.4.2  

## Proxmox API Versions

This documentation covers **Proxmox VE 7.4.2**. The SDK may be compatible with other versions but is specifically tested against this release.

## Getting Help

- Check the [Examples](./06-examples.md) section for common usage patterns
- Review [Error Handling](./07-error-handling.md) for troubleshooting
- Check [Advanced Usage](./08-advanced-usage.md) for optimization tips
- Refer to the [Proxmox API Documentation](https://pve.proxmox.com/wiki/Proxmox_VE_API2) for official endpoint documentation

## SDK Repository

- **GitHub**: [prmxctrl](https://github.com/Ganzzi/prmxctrl)
- **License**: MIT

---

**Last Updated**: December 2025  
**SDK Version**: 1.0.0  
**Proxmox Version**: 7.4.2
