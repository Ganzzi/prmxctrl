# Examples

Practical, real-world examples for common Proxmox administration tasks.

## Table of Contents

1. [Cluster Management](#cluster-management)
2. [Node Management](#node-management)
3. [Virtual Machine Operations](#virtual-machine-operations)
4. [Container Operations](#container-operations)
5. [Storage Management](#storage-management)
6. [User and Access Control](#user-and-access-control)
7. [Monitoring and Status](#monitoring-and-status)
8. [Advanced Operations](#advanced-operations)

---

## Cluster Management

### Get Cluster Status

```python
import asyncio
from prmxctrl import ProxmoxClient

async def cluster_status():
    async with ProxmoxClient(
        host="https://proxmox.example.com:8006",
        user="root@pam",
        password="password"
    ) as client:
        # Get cluster status
        status = await client.cluster.status.get()
        print(f"Cluster: {status.cluster}")
        print(f"ID: {status.id}")
        print(f"Quorate: {status.quorate}")

asyncio.run(cluster_status())
```

### List All Cluster Resources

```python
async def list_resources():
    async with ProxmoxClient(...) as client:
        resources = await client.cluster.resources.get()
        
        print("Nodes:")
        for res in resources:
            if res.type == "node":
                print(f"  {res.node}: {res.status}")
        
        print("\nVMs:")
        for res in resources:
            if res.type == "qemu":
                print(f"  {res.vmid}: {res.name} ({res.status})")
        
        print("\nContainers:")
        for res in resources:
            if res.type == "lxc":
                print(f"  {res.vmid}: {res.name} ({res.status})")

asyncio.run(list_resources())
```

### Get HA Status

```python
async def ha_status():
    async with ProxmoxClient(...) as client:
        ha = await client.cluster.ha.status.get()
        print(f"HA Enabled: {ha.ha_enabled}")
        print(f"Expected Nodes: {ha.expected_nodes}")
        for node, status in ha.node_status.items():
            print(f"  {node}: {status}")

asyncio.run(ha_status())
```

---

## Node Management

### List All Nodes

```python
async def list_nodes():
    async with ProxmoxClient(...) as client:
        nodes = await client.nodes.list()
        
        print("Nodes in cluster:")
        for node in nodes:
            print(f"  {node.node}:")
            print(f"    Status: {node.status}")
            print(f"    CPU: {node.maxcpu} cores")
            print(f"    Memory: {node.memory.total / (1024**3):.0f}GB")
            print(f"    Uptime: {node.uptime}s")

asyncio.run(list_nodes())
```

### Get Node Detailed Status

```python
async def node_status(node_name: str):
    async with ProxmoxClient(...) as client:
        status = await client.nodes(node_name).status.get()
        
        print(f"Node: {status.node}")
        print(f"Status: {status.status}")
        print(f"Uptime: {status.uptime}s")
        print(f"Load: {status.loadavg}")
        
        # CPU info
        print(f"CPU Usage: {status.cpu * 100:.1f}%")
        
        # Memory info
        mem_total = status.memory.total / (1024**3)
        mem_used = status.memory.used / (1024**3)
        print(f"Memory: {mem_used:.1f}GB / {mem_total:.1f}GB")
        
        # Disk info
        disk_total = status.disk.total / (1024**3)
        disk_used = status.disk.used / (1024**3)
        print(f"Disk: {disk_used:.1f}GB / {disk_total:.1f}GB")

asyncio.run(node_status("pve1"))
```

### Reboot Node

```python
async def reboot_node(node_name: str):
    async with ProxmoxClient(...) as client:
        print(f"Rebooting {node_name}...")
        await client.nodes(node_name).reboot.create()
        print("Reboot initiated")

asyncio.run(reboot_node("pve1"))
```

### Shutdown Node

```python
async def shutdown_node(node_name: str):
    async with ProxmoxClient(...) as client:
        print(f"Shutting down {node_name}...")
        await client.nodes(node_name).shutdown.create()
        print("Shutdown initiated")

asyncio.run(shutdown_node("pve1"))
```

---

## Virtual Machine Operations

### List VMs on a Node

```python
async def list_vms(node_name: str):
    async with ProxmoxClient(...) as client:
        vms = await client.nodes(node_name).qemu.list()
        
        print(f"VMs on {node_name}:")
        for vm in vms:
            print(f"  {vm.vmid}: {vm.name}")
            print(f"    Status: {vm.status}")
            if hasattr(vm, 'uptime') and vm.uptime:
                print(f"    Uptime: {vm.uptime}s")

asyncio.run(list_vms("pve1"))
```

### Get VM Configuration

```python
async def vm_config(node_name: str, vmid: int):
    async with ProxmoxClient(...) as client:
        config = await client.nodes(node_name).qemu(vmid).config.get()
        
        print(f"VM {vmid} Configuration:")
        for key, value in config.model_dump().items():
            if not key.startswith('_'):
                print(f"  {key}: {value}")

asyncio.run(vm_config("pve1", 100))
```

### Create a New VM

```python
async def create_vm(
    node_name: str,
    vmid: int,
    name: str,
    memory_mb: int = 2048,
    cores: int = 2
):
    async with ProxmoxClient(...) as client:
        print(f"Creating VM {vmid} ({name})...")
        
        result = await client.nodes(node_name).qemu.create(
            vmid=vmid,
            name=name,
            memory=memory_mb,
            cores=cores,
            net0="virtio,bridge=vmbr0"
        )
        
        print(f"VM created successfully")
        print(f"Task: {result}")

asyncio.run(create_vm("pve1", 100, "test-vm", memory_mb=4096, cores=4))
```

### Start a VM

```python
async def start_vm(node_name: str, vmid: int):
    async with ProxmoxClient(...) as client:
        print(f"Starting VM {vmid}...")
        await client.nodes(node_name).qemu(vmid).status.create(
            command="start"
        )
        print("VM started")

asyncio.run(start_vm("pve1", 100))
```

### Stop a VM

```python
async def stop_vm(node_name: str, vmid: int, force: bool = False):
    async with ProxmoxClient(...) as client:
        command = "stop" if not force else "stop"
        timeout = None if not force else 0
        
        print(f"Stopping VM {vmid}...")
        await client.nodes(node_name).qemu(vmid).status.create(
            command=command,
            timeout=timeout
        )
        print("VM stopped")

asyncio.run(stop_vm("pve1", 100))
```

### Reboot a VM

```python
async def reboot_vm(node_name: str, vmid: int):
    async with ProxmoxClient(...) as client:
        print(f"Rebooting VM {vmid}...")
        await client.nodes(node_name).qemu(vmid).reboot.create()
        print("VM rebooted")

asyncio.run(reboot_vm("pve1", 100))
```

### Shutdown a VM

```python
async def shutdown_vm(node_name: str, vmid: int):
    async with ProxmoxClient(...) as client:
        print(f"Shutting down VM {vmid}...")
        await client.nodes(node_name).qemu(vmid).shutdown.create()
        print("VM shutdown")

asyncio.run(shutdown_vm("pve1", 100))
```

### Resize VM Disk

```python
async def resize_vm_disk(
    node_name: str,
    vmid: int,
    disk: str,
    size: str
):
    """
    Resize VM disk.
    
    Args:
        node_name: Node containing the VM
        vmid: VM ID
        disk: Disk identifier (e.g., 'scsi0', 'virtio0')
        size: Size increase (e.g., '+50G', '+100')
    """
    async with ProxmoxClient(...) as client:
        print(f"Resizing disk {disk} by {size}...")
        await client.nodes(node_name).qemu(vmid).resize.create(
            disk=disk,
            size=size
        )
        print("Disk resized")

asyncio.run(resize_vm_disk("pve1", 100, "scsi0", "+50G"))
```

### Update VM Configuration

```python
async def update_vm_config(
    node_name: str,
    vmid: int,
    **config_updates
):
    """
    Update VM configuration.
    
    Args:
        node_name: Node containing the VM
        vmid: VM ID
        **config_updates: Configuration parameters to update
    """
    async with ProxmoxClient(...) as client:
        print(f"Updating VM {vmid}...")
        await client.nodes(node_name).qemu(vmid).config.update(
            **config_updates
        )
        print("VM configuration updated")

asyncio.run(update_vm_config(
    "pve1", 100,
    memory=4096,
    cores=4,
    description="Updated VM"
))
```

### Delete a VM

```python
async def delete_vm(node_name: str, vmid: int, force: bool = False):
    async with ProxmoxClient(...) as client:
        print(f"Deleting VM {vmid}...")
        await client.nodes(node_name).qemu(vmid).delete(
            force=1 if force else 0
        )
        print("VM deleted")

asyncio.run(delete_vm("pve1", 100))
```

---

## Container Operations

### List Containers

```python
async def list_containers(node_name: str):
    async with ProxmoxClient(...) as client:
        containers = await client.nodes(node_name).lxc.list()
        
        print(f"Containers on {node_name}:")
        for container in containers:
            print(f"  {container.vmid}: {container.hostname}")
            print(f"    Status: {container.status}")

asyncio.run(list_containers("pve1"))
```

### Create a Container

```python
async def create_container(
    node_name: str,
    vmid: int,
    hostname: str,
    ostype: str = "debian"
):
    async with ProxmoxClient(...) as client:
        print(f"Creating container {vmid} ({hostname})...")
        
        result = await client.nodes(node_name).lxc.create(
            vmid=vmid,
            hostname=hostname,
            ostype=ostype
        )
        
        print(f"Container created")
        print(f"Task: {result}")

asyncio.run(create_container("pve1", 101, "web-server"))
```

### Start a Container

```python
async def start_container(node_name: str, vmid: int):
    async with ProxmoxClient(...) as client:
        print(f"Starting container {vmid}...")
        await client.nodes(node_name).lxc(vmid).status.create(
            command="start"
        )
        print("Container started")

asyncio.run(start_container("pve1", 101))
```

### Stop a Container

```python
async def stop_container(node_name: str, vmid: int):
    async with ProxmoxClient(...) as client:
        print(f"Stopping container {vmid}...")
        await client.nodes(node_name).lxc(vmid).status.create(
            command="stop"
        )
        print("Container stopped")

asyncio.run(stop_container("pve1", 101))
```

---

## Storage Management

### List Storage Resources

```python
async def list_storage():
    async with ProxmoxClient(...) as client:
        storage_list = await client.storage.list()
        
        print("Storage Resources:")
        for storage in storage_list:
            total = storage.size / (1024**3) if storage.size else 0
            used = storage.used / (1024**3) if storage.used else 0
            print(f"  {storage.storage}:")
            print(f"    Type: {storage.type}")
            print(f"    Used: {used:.2f}GB / {total:.2f}GB")

asyncio.run(list_storage())
```

### List Storage Content

```python
async def list_storage_content(storage_name: str):
    async with ProxmoxClient(...) as client:
        content = await client.storage(storage_name).content.get()
        
        print(f"Content in {storage_name}:")
        for item in content:
            print(f"  {item.volid}")
            if hasattr(item, 'size'):
                print(f"    Size: {item.size / (1024**3):.2f}GB")

asyncio.run(list_storage_content("local"))
```

### Prune Old Backups

```python
async def prune_backups(
    storage_name: str,
    keep_last: int = 3,
    keep_hourly: int = 24
):
    async with ProxmoxClient(...) as client:
        prune_backups = f"keep-last={keep_last},keep-hourly={keep_hourly}"
        
        print(f"Pruning backups in {storage_name}...")
        await client.storage(storage_name).prunebackups.create(
            prune_backups=prune_backups
        )
        print("Pruned")

asyncio.run(prune_backups("backup", keep_last=5))
```

---

## User and Access Control

### List Users

```python
async def list_users():
    async with ProxmoxClient(...) as client:
        users = await client.access.users.list()
        
        print("Users:")
        for user in users:
            print(f"  {user.userid}")
            if hasattr(user, 'email'):
                print(f"    Email: {user.email}")

asyncio.run(list_users())
```

### Create a User

```python
async def create_user(
    username: str,
    password: str,
    realm: str = "pam",
    email: str = ""
):
    async with ProxmoxClient(...) as client:
        userid = f"{username}@{realm}"
        print(f"Creating user {userid}...")
        
        await client.access.users.create(
            userid=userid,
            password=password,
            email=email
        )
        print(f"User created")

asyncio.run(create_user("newuser", "password123", email="user@example.com"))
```

### Change User Password

```python
async def change_password(username: str, new_password: str):
    async with ProxmoxClient(...) as client:
        userid = f"{username}@pam"
        print(f"Changing password for {userid}...")
        
        await client.access.users(userid).update(
            password=new_password
        )
        print("Password changed")

asyncio.run(change_password("testuser", "newpassword123"))
```

### List Roles

```python
async def list_roles():
    async with ProxmoxClient(...) as client:
        roles = await client.access.roles.list()
        
        print("Roles:")
        for role in roles:
            print(f"  {role.roleid}")
            if hasattr(role, 'privs'):
                print(f"    Privileges: {role.privs}")

asyncio.run(list_roles())
```

---

## Monitoring and Status

### Monitor System Resources

```python
async def monitor_resources():
    async with ProxmoxClient(...) as client:
        nodes = await client.nodes.list()
        
        print("Node Resources:")
        for node in nodes:
            status = await client.nodes(node.node).status.get()
            
            cpu_percent = status.cpu * 100
            mem_percent = (status.memory.used / status.memory.total) * 100
            
            print(f"\n{status.node}:")
            print(f"  CPU: {cpu_percent:.1f}%")
            print(f"  Memory: {mem_percent:.1f}%")
            print(f"  Uptime: {status.uptime}s")

asyncio.run(monitor_resources())
```

### Get VM Resource Usage

```python
async def vm_resources(node_name: str, vmid: int):
    async with ProxmoxClient(...) as client:
        status = await client.nodes(node_name).qemu(vmid).status.current.get()
        
        print(f"VM {vmid} Resources:")
        print(f"  Status: {status.status}")
        if hasattr(status, 'cpu'):
            print(f"  CPU: {status.cpu * 100:.1f}%")
        if hasattr(status, 'memory'):
            mem_gb = status.memory / (1024**3)
            print(f"  Memory: {mem_gb:.2f}GB")

asyncio.run(vm_resources("pve1", 100))
```

---

## Advanced Operations

### Backup a VM

```python
async def backup_vm(
    node_name: str,
    vmid: int,
    storage: str = "local",
    mode: str = "snapshot"
):
    async with ProxmoxClient(...) as client:
        print(f"Backing up VM {vmid}...")
        
        result = await client.nodes(node_name).backup.create(
            vmid=vmid,
            storage=storage,
            mode=mode
        )
        
        print(f"Backup started")
        print(f"Task: {result}")

asyncio.run(backup_vm("pve1", 100))
```

### Concurrent Operations

```python
async def manage_multiple_vms():
    """Start multiple VMs concurrently."""
    async with ProxmoxClient(...) as client:
        # Start multiple VMs at the same time
        tasks = [
            client.nodes("pve1").qemu(100).status.create(command="start"),
            client.nodes("pve1").qemu(101).status.create(command="start"),
            client.nodes("pve1").qemu(102).status.create(command="start"),
        ]
        
        # Wait for all to complete
        await asyncio.gather(*tasks)
        print("All VMs started")

asyncio.run(manage_multiple_vms())
```

### Error Handling in Complex Operations

```python
import asyncio
from prmxctrl.base.exceptions import ProxmoxAPIError, ProxmoxAuthError

async def safe_cluster_operation():
    try:
        async with ProxmoxClient(...) as client:
            # Perform operations with error handling
            try:
                nodes = await client.nodes.list()
                print(f"Found {len(nodes)} nodes")
            except ProxmoxAPIError as e:
                print(f"API Error: {e.status_code} - {e.message}")
            except Exception as e:
                print(f"Unexpected error: {e}")
                
    except ProxmoxAuthError:
        print("Authentication failed")
    except ConnectionError:
        print("Cannot connect to Proxmox")

asyncio.run(safe_cluster_operation())
```

---

**See Also**: [API Reference](./04_API_REFERENCE.md) | [Data Models](./05_DATA_MODELS.md) | [Error Handling](./07_ERROR_HANDLING.md) | [Advanced Usage](./08_ADVANCED_USAGE.md)
