# Proxmox VE API Schema Documentation (v7.4-2)

## Overview

This document provides comprehensive analysis of the Proxmox VE API schema v7.4-2, parsed from the official `apidata.js` file. The schema defines 6 endpoints with complex parameter structures and custom validation formats.

## Schema Statistics

- **Total Endpoints**: 6
- **Total Methods**: 6 (all endpoints have single methods)
- **Total Parameters**: 1,234 (across all endpoints)
- **Average Parameters per Endpoint**: 205.67
- **Maximum Parameters in Single Endpoint**: 83 (`/nodes/{node}/qemu/{vmid}/config PUT`)

## Parameter Types

### Standard JSON Schema Types
- `string`: Text values, most common type (67% of parameters)
- `integer`: Whole numbers with min/max constraints
- `boolean`: True/false values
- `number`: Floating point numbers (unusual, only in bandwidth limits)
- `array`: Lists of values (rare, mostly for complex configurations)

### Unusual Type Patterns
- `number` type used instead of `integer` for bandwidth limits (KiB/s values)
- Complex nested object definitions within parameter format fields

## Constraint Types

### Numeric Constraints
- `minimum`: Lower bounds (e.g., `minimum: 1` for VM IDs)
- `maximum`: Upper bounds (e.g., `maximum: 4094` for VLAN tags)

### String Constraints
- `pattern`: Regular expressions for validation
  - MAC addresses: `(?^:^(0x)[0-9a-fA-F]{16})`
  - VLAN lists: `(?^:\\d+(?:-\\d+)?(?:;\\d+(?:-\\d+)?)*)`
  - Domain names and identifiers
- `maxLength`: Maximum string length (e.g., `maxLength: 60` for serial numbers)
- `minLength`: Minimum string length (rare)

### Enumeration Constraints
- `enum`: Fixed set of allowed values
  - VM states: `["stopped", "running", "paused"]`
  - Disk formats: `["raw", "cow", "qcow", "qcow2", "vmdk", "cloop"]`
  - Network models: `["e1000", "e1000-82540em", ..., "virtio"]`

### Format-Based Validation
- `format`: Custom Proxmox format validators (see Custom Formats section)
- `format_description`: Human-readable format descriptions

## Custom Proxmox Formats

The schema uses extensive custom format validation. Here are all identified formats:

### Node and Cluster Formats
- `pve-node`: Node names in cluster
- `pve-node-list`: List of node names
- `pve-bridge-id`: Bridge interface names
- `pve-bridge-id-list`: List of bridge interfaces

### Virtual Machine Formats
- `pve-vmid`: Virtual machine/container IDs
- `pve-vmid-list`: List of VM/container IDs
- `pve-vm-cpu-conf`: CPU configuration strings
- `pve-qm-boot`: QEMU boot order configuration
- `pve-qm-bootdisk`: QEMU boot disk specification
- `pve-qm-ide`: IDE drive configuration
- `pve-qm-cicustom`: Cloud-init custom configuration
- `pve-qm-usb-device`: USB device specifications
- `pve-qm-watchdog`: QEMU watchdog configuration
- `pve-qm-smbios1`: SMBIOS configuration
- `pve-startup-order`: VM startup order
- `pve-tag-list`: VM tag lists

### Storage Formats
- `pve-volume-id`: Storage volume identifiers
- `pve-volume-id-or-qm-path`: Volume ID or QEMU path
- `pve-volume-id-or-absolute-path`: Volume ID or absolute filesystem path
- `pve-storage-id`: Storage configuration IDs
- `pve-storage-id-list`: List of storage IDs
- `pve-storage-content`: Storage content types
- `pve-storage-content-list`: List of content types
- `pve-storage-server`: Storage server addresses
- `pve-storage-portal-dns`: iSCSI portal DNS names
- `pve-storage-portal-dns-list`: List of iSCSI portals
- `pve-storage-path`: Storage filesystem paths
- `pve-storage-format`: Storage format types
- `pve-storage-options`: Storage configuration options
- `pve-storage-vgname`: LVM volume group names

### Network Formats
- `mac-addr`: MAC addresses (`XX:XX:XX:XX:XX:XX`)
- `ipv4`: IPv4 addresses
- `ipv6`: IPv6 addresses
- `CIDR`: CIDR notation networks
- `CIDRv4`: IPv4 networks in CIDR
- `CIDRv6`: IPv6 networks in CIDR
- `ipv4mask`: IPv4 netmasks
- `pve-ipv4-config`: IPv4 configuration strings
- `pve-ipv6-config`: IPv6 configuration strings
- `pve-iface`: Network interface names
- `pve-iface-list`: List of network interfaces
- `address`: Generic IP addresses
- `address-list`: List of IP addresses

### Access Control Formats
- `pve-userid`: User identifiers
- `pve-userid-list`: List of user IDs
- `pve-groupid`: Group identifiers
- `pve-groupid-list`: List of group IDs
- `pve-roleid`: Role identifiers
- `pve-roleid-list`: List of role IDs
- `pve-priv-list`: Privilege lists
- `pve-tokenid-list`: API token ID lists
- `pve-realm`: Authentication realm names
- `pve-tfa-config`: Two-factor authentication configuration
- `email-opt`: Optional email addresses
- `email-or-username-list`: List of emails/usernames

### Task and Job Formats
- `pve-task-status-type-list`: Task status type filters
- `pve-replication-job-id`: Replication job identifiers
- `pve-configid`: Generic configuration IDs
- `pve-configid-list`: List of configuration IDs

### Backup Formats
- `backup-performance`: Backup performance settings
- `prune-backups`: Backup pruning configuration
- `pve-dir-override-list`: Directory override lists

### Firewall Formats
- `pve-fw-addr-spec`: Firewall address specifications
- `pve-fw-dport-spec`: Firewall destination port specs
- `pve-fw-sport-spec`: Firewall source port specs
- `pve-fw-icmp-type-spec`: ICMP type specifications
- `pve-fw-protocol-spec`: Protocol specifications
- `pve-fw-conntrack-helper`: Connection tracking helpers

### Certificate Formats
- `pem-certificate-chain`: PEM certificate chains
- `pem-string`: PEM-encoded strings

### ACME Formats
- `pve-acme-domain`: ACME domain names
- `pve-acme-domain-list`: List of ACME domains
- `pve-acme-alias`: ACME domain aliases

### SDN Formats
- `pve-sdn-zone-id`: SDN zone identifiers

### Miscellaneous Formats
- `disk-size`: Disk size specifications (e.g., "10G", "500M")
- `urlencoded`: URL-encoded strings
- `string-list`: Generic string lists
- `string-alist`: Associative string lists
- `realm-sync-options`: Realm synchronization options
- `pve-command-batch`: Batch command specifications
- `pve-poolid`: Pool identifiers
- `pve-ct-timezone`: Container timezone settings
- `dns-name`: DNS names
- `dns-name-list`: List of DNS names
- `IPorCIDR`: IP address or CIDR notation
- `IPorCIDRorAlias`: IP/CIDR or alias
- `proxmox-remote`: Remote Proxmox instance specs
- `storage-pair-list`: Storage mapping pairs
- `bridge-pair-list`: Bridge mapping pairs
- `wwn`: World Wide Names (16-byte hex)
- `ldap-simple-attr`: LDAP simple attributes
- `ldap-simple-attr-list`: List of LDAP attributes

## Complex Parameter Structures

### Nested Format Definitions

Many parameters use complex nested format definitions instead of simple strings. These appear as full JSON objects within the `format` field, containing complete parameter specifications for sub-parameters.

Example from `/nodes/{node}/qemu/{vmid}/config`:
```json
"format": {
  "aio": {"description": "AIO type", "enum": ["native", "threads", "io_uring"], "optional": 1, "type": "string"},
  "backup": {"description": "Backup inclusion", "optional": 1, "type": "boolean"},
  // ... many more sub-parameters
}
```

### Dynamic Parameter Patterns

The schema uses dynamic parameter expansion patterns like `link[n]` that should expand to `link0`, `link1`, ..., `link7`. However, the current parser treats these as literal parameter names.

### High-Parameter Endpoints

Several endpoints have unusually high parameter counts:
- `/nodes/{node}/qemu/{vmid}/config PUT`: 83 parameters
- `/nodes/{node}/lxc POST`: 42 parameters
- `/nodes/{node}/network POST`: 28 parameters
- `/storage POST`: 59 parameters

These complex endpoints likely represent comprehensive configuration interfaces for VMs, containers, and storage.

## Common Parameter Patterns

The analyzer identified 34 common parameter sets (CommonParams43 through CommonParams149) that appear across multiple endpoints. These represent shared configuration patterns that could be extracted into reusable model classes.

## Edge Cases and Challenges

1. **Format Type Inconsistency**: Some formats are strings, others are complex nested objects
2. **Dynamic Parameters**: `link[n]` style patterns need expansion logic
3. **Custom Validation**: Extensive use of Proxmox-specific format validators
4. **Complex Nesting**: Parameters containing sub-parameter definitions
5. **Type Inconsistencies**: Using `number` instead of `integer` for whole numbers

## Code Generation Implications

### Type Mapping Requirements
- Map Proxmox custom formats to appropriate Python/Pydantic types
- Handle nested parameter structures
- Implement custom validators for format-specific constraints

### Model Generation Strategy
- Extract common parameter sets into shared base models
- Handle dynamic parameter expansion
- Support complex nested configurations

### Validation Strategy
- Implement format-specific Pydantic validators
- Handle optional vs required parameters correctly
- Support enum constraints and pattern matching

This schema analysis provides the foundation for generating a comprehensive, type-safe Python SDK for the Proxmox VE API v7.4-2.