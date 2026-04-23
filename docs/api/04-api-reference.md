# API Reference

Complete reference to all Proxmox VE API endpoints exposed through the prmxctrl SDK.

## Proxmox VE 7.4.2 API Endpoints

The SDK provides type-safe access to 284 endpoints across 6 major categories:

- **Cluster**: 45+ endpoints for cluster management
- **Nodes**: 120+ endpoints for node and VM/container management
- **Storage**: 25+ endpoints for storage operations
- **Access**: 35+ endpoints for user and permission management
- **Pools**: 10+ endpoints for pool management
- **Version**: 5+ endpoints for API information

## Endpoint Categories

### 1. CLUSTER Endpoints

**Base Path**: `/api2/json/cluster`

Access cluster-level operations, status, and management functions.

```python
client.cluster.*
```

#### Common Operations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/cluster` | Get cluster index |
| GET | `/cluster/status` | Get cluster status |
| GET | `/cluster/resources` | List cluster resources |
| GET | `/cluster/ha` | High Availability configuration |
| GET | `/cluster/backup` | List backups |
| POST | `/cluster/backup` | Create backup |
| GET | `/cluster/replication` | Replication status |
| GET | `/cluster/tasks` | List cluster tasks |
| GET | `/cluster/log` | Get cluster logs |
| GET | `/cluster/metrics` | Metrics data |
| GET | `/cluster/firewall` | Firewall rules |
| GET | `/cluster/sdn` | Software Defined Networking |
| GET | `/cluster/acme` | ACME certificates |

#### Usage Examples

```python
# Get cluster status
status = await client.cluster.status.get()

# List all cluster resources
resources = await client.cluster.resources.get()

# Get HA status
ha_status = await client.cluster.ha.status.get()

# List backups
backups = await client.cluster.backup.list()
```

---

### 2. NODES Endpoints

**Base Path**: `/api2/json/nodes`

Node management, VM/container operations, and system configuration.

```python
client.nodes.*
```

#### Node-Level Operations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nodes` | List all nodes |
| GET | `/nodes/{node}` | Get node status |
| GET | `/nodes/{node}/status` | Get node system status |
| GET | `/nodes/{node}/qemu` | List QEMU VMs |
| GET | `/nodes/{node}/lxc` | List LXC containers |
| GET | `/nodes/{node}/storage` | List node storage |

#### QEMU VM Operations

```python
# List all VMs on a node
vms = await client.nodes("pve1").qemu.list()

# Get VM configuration
config = await client.nodes("pve1").qemu(100).config.get()

# Create new VM
task = await client.nodes("pve1").qemu.create(
    vmid=100,
    name="my-vm",
    memory=2048,
    cores=2,
    net0="virtio,bridge=vmbr0"
)

# Get VM status
status = await client.nodes("pve1").qemu(100).status.current.get()

# Start VM
await client.nodes("pve1").qemu(100).status.create(command="start")

# Stop VM
await client.nodes("pve1").qemu(100).status.create(command="stop")

# Reboot VM
await client.nodes("pve1").qemu(100).reboot.create()

# Shutdown VM
await client.nodes("pve1").qemu(100).shutdown.create()

# Delete VM
await client.nodes("pve1").qemu(100).delete()

# Resize disk
await client.nodes("pve1").qemu(100).resize.create(
    disk="virtio0",
    size="+50G"
)
```

#### LXC Container Operations

```python
# List all containers on a node
containers = await client.nodes("pve1").lxc.list()

# Get container configuration
config = await client.nodes("pve1").lxc(101).config.get()

# Create new container
task = await client.nodes("pve1").lxc.create(
    vmid=101,
    hostname="my-container",
    ostype="debian",
    osid="debian-11"
)

# Get container status
status = await client.nodes("pve1").lxc(101).status.current.get()

# Start container
await client.nodes("pve1").lxc(101).status.create(command="start")

# Stop container
await client.nodes("pve1").lxc(101).status.create(command="stop")

# Delete container
await client.nodes("pve1").lxc(101).delete()
```

#### Node System Operations

```python
# Get node system status
status = await client.nodes("pve1").status.get()

# Get node uptime and system load
print(f"Uptime: {status.uptime} seconds")
print(f"CPU: {status.cpu * 100:.1f}%")
print(f"Memory: {status.memory.used} / {status.memory.total}")

# Get system logs
logs = await client.nodes("pve1").syslog.get()

# List apt packages
packages = await client.nodes("pve1").apt.list()

# Get package versions
versions = await client.nodes("pve1").apt.versions.get()

# Reboot node
await client.nodes("pve1").reboot.create()

# Shutdown node
await client.nodes("pve1").shutdown.create()
```

#### Disk and Storage Operations

```python
# List disks
disks = await client.nodes("pve1").disks.list.get()

# List LVM volumes
lvmvolumes = await client.nodes("pve1").disks.lvmvolumes.get()

# List partitions
partitions = await client.nodes("pve1").disks.partitions.get()

# Smart data for disk
smart = await client.nodes("pve1").disks.smart.get(disk="sda")
```

---

### 3. STORAGE Endpoints

**Base Path**: `/api2/json/storage`

Storage management and configuration.

```python
client.storage.*
```

#### Storage Operations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/storage` | List all storage |
| GET | `/storage/{storage}` | Get storage status |
| POST | `/storage/{storage}/prune-backups` | Prune backups |
| GET | `/storage/{storage}/content` | List storage content |

#### Usage Examples

```python
# List all storage resources
storage = await client.storage.list()

# Get storage details
storage_info = await client.storage("local").get()

# List content in storage
content = await client.storage("local").content.get()

# Prune old backups
await client.storage("backup").prunebackups.create(
    prune_backups="keep-last=3"
)
```

---

### 4. ACCESS Endpoints

**Base Path**: `/api2/json/access`

User management, permissions, roles, and authentication.

```python
client.access.*
```

#### User Management

```python
# List all users
users = await client.access.users.list()

# Get user details
user = await client.access.users("root@pam").get()

# Create new user
await client.access.users.create(
    userid="newuser@pam",
    password="password123",
    email="user@example.com"
)

# Update user
await client.access.users("newuser@pam").update(
    email="newemail@example.com"
)

# Delete user
await client.access.users("newuser@pam").delete()

# Change user password
await client.access.users("newuser@pam").update(
    password="newpassword123"
)
```

#### Group Management

```python
# List all groups
groups = await client.access.groups.list()

# Get group members
group = await client.access.groups("admin").get()

# Create group
await client.access.groups.create(
    groupid="developers",
    comment="Developer team"
)

# Delete group
await client.access.groups("developers").delete()
```

#### Role Management

```python
# List all roles
roles = await client.access.roles.list()

# Get role privileges
role = await client.access.roles("Administrator").get()

# Create custom role
await client.access.roles.create(
    roleid="my-role",
    privs="Sys.Audit,VM.Allocate,VM.Audit"
)

# Delete role
await client.access.roles("my-role").delete()
```

#### Permission Management

```python
# Get permissions
perms = await client.access.permissions.get()

# Update ACL
await client.access.acl.update(
    path="/vms/100",
    roles="Administrator",
    users="root@pam",
    groups="admin"
)
```

#### API Token Management

```python
# List user tokens
tokens = await client.access.users("root@pam").token.list()

# Create API token
token = await client.access.users("root@pam").token.create(
    tokenid="my-token"
)

# Delete token
await client.access.users("root@pam").token("my-token").delete()
```

#### Domain Management

```python
# List authentication domains
domains = await client.access.domains.list()

# Get domain details
domain = await client.access.domains("pam").get()
```

---

### 5. POOLS Endpoints

**Base Path**: `/api2/json/pools`

Resource pool management.

```python
client.pools.*
```

#### Pool Operations

```python
# List all pools
pools = await client.pools.list()

# Get pool details
pool = await client.pools("mypool").get()

# Create pool
await client.pools.create(
    poolid="dev-pool",
    comment="Development resources"
)

# Update pool
await client.pools("dev-pool").update(
    comment="Development and testing resources"
)

# Delete pool
await client.pools("dev-pool").delete()
```

---

### 6. VERSION Endpoints

**Base Path**: `/api2/json/version`

API version and server information.

```python
client.version.*
```

#### Version Information

```python
# Get API version info
version = await client.version.get()
print(f"Version: {version.version}")
print(f"Release: {version.release}")
```

---

## Common Patterns

### Listing Resources

```python
# List items at any level
items = await client.resource.list()

for item in items:
    print(f"{item.name}: {item.status}")
```

### Getting Details

```python
# Get details for a specific item
details = await client.resource("id").get()
```

### Creating Resources

```python
# Create with required parameters
result = await client.resource.create(
    param1="value1",
    param2="value2"
)
```

### Updating Resources

```python
# Update specific fields
await client.resource("id").update(
    field="new_value"
)
```

### Deleting Resources

```python
# Delete resource
await client.resource("id").delete()
```

---

## Response Status and Error Codes

The API returns standard HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success - GET/DELETE completed |
| 201 | Created - POST/PUT successful |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication failed |
| 403 | Forbidden - Permission denied |
| 404 | Not Found - Resource doesn't exist |
| 500 | Server Error - API error |

See [Error Handling](./07-error-handling.md) for exception handling.

---

## Rate Limiting

Proxmox API does not have formal rate limiting but:

- Avoid excessive requests in loops
- Use concurrent requests where appropriate
- Implement exponential backoff for retries

---

## Task Operations

Many operations are asynchronous and return task IDs:

```python
# Create VM returns a task
task = await client.nodes("pve1").qemu.create(...)

# The returned task contains:
# - upid: Task ID
# - id: Task number
# - node: Node it's running on
# - type: Operation type
# - user: User who initiated

# You can monitor the task
# See Advanced Usage for task monitoring patterns
```

---

**See Also**: [Core Concepts](./03-core-concepts.md) | [Data Models](./05-data-models.md) | [Examples](./06-examples.md) | [Error Handling](./07-error-handling.md)
