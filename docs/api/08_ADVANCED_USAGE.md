# Advanced Usage

Advanced patterns, optimization techniques, and production best practices.

## Table of Contents

1. [Connection Pooling](#connection-pooling)
2. [Async Patterns](#async-patterns)
3. [Performance Optimization](#performance-optimization)
4. [Task Monitoring](#task-monitoring)
5. [Streaming and Large Datasets](#streaming-and-large-datasets)
6. [Custom HTTP Configuration](#custom-http-configuration)
7. [Type Safety and Mypy](#type-safety-and-mypy)
8. [Production Deployment](#production-deployment)

---

## Connection Pooling

The SDK automatically uses HTTP connection pooling via httpx.

### Default Pooling Behavior

```python
async with ProxmoxClient(...) as client:
    # Connection pool is automatically managed
    # Multiple requests reuse the same connections
    nodes = await client.nodes.list()
    status = await client.cluster.status.get()
    storage = await client.storage.list()
    
# Pool is cleaned up when exiting context
```

### Configuring Pool Size

The connection pool size can be adjusted (currently 10 connections):

```python
# For high-concurrency scenarios, you may need to adjust
# httpx connection limits. This requires modifying http_client.py

async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",
    password="password"
) as client:
    # The pool handles multiple concurrent requests
    ...
```

### Long-Running Applications

For long-running applications, prefer the context manager pattern:

```python
async def main():
    async with ProxmoxClient(...) as client:
        while True:
            # Check cluster status every minute
            status = await client.cluster.status.get()
            await asyncio.sleep(60)

asyncio.run(main())
```

---

## Async Patterns

### Sequential vs Concurrent Operations

**Sequential** - Execute one after another (slower):

```python
async def sequential():
    async with ProxmoxClient(...) as client:
        nodes = await client.nodes.list()      # Waits...
        storage = await client.storage.list()  # Waits...
        version = await client.version.get()   # Waits...
        # Total time: ~30 seconds (10s each)
```

**Concurrent** - Execute in parallel (faster):

```python
async def concurrent():
    async with ProxmoxClient(...) as client:
        # All requests execute in parallel
        nodes, storage, version = await asyncio.gather(
            client.nodes.list(),
            client.storage.list(),
            client.version.get()
        )
        # Total time: ~10 seconds (max of any single request)
```

### Processing Large Lists Efficiently

```python
async def process_all_vms():
    """Process VMs from all nodes efficiently."""
    async with ProxmoxClient(...) as client:
        # Get all nodes
        nodes = await client.nodes.list()
        
        # Get VMs from all nodes concurrently
        vm_tasks = [
            client.nodes(node.node).qemu.list()
            for node in nodes
        ]
        
        all_vm_lists = await asyncio.gather(*vm_tasks)
        
        # Flatten list
        all_vms = []
        for vm_list in all_vm_lists:
            all_vms.extend(vm_list)
        
        return all_vms

vms = asyncio.run(process_all_vms())
```

### Producer-Consumer Pattern

```python
import asyncio
from asyncio import Queue

async def vm_producer(queue: Queue):
    """Produce VM information."""
    async with ProxmoxClient(...) as client:
        nodes = await client.nodes.list()
        for node in nodes:
            vms = await client.nodes(node.node).qemu.list()
            for vm in vms:
                await queue.put(vm)
        # Signal completion
        await queue.put(None)

async def vm_consumer(queue: Queue):
    """Consume VM information."""
    while True:
        vm = await queue.get()
        if vm is None:
            break
        
        # Process VM
        print(f"Processing VM {vm.vmid}: {vm.name}")
        
        queue.task_done()

async def main():
    queue: Queue = asyncio.Queue()
    
    # Run producer and consumer concurrently
    await asyncio.gather(
        vm_producer(queue),
        vm_consumer(queue)
    )

asyncio.run(main())
```

### Timeout Protection for All Operations

```python
async def operation_with_timeout():
    """Wrap any operation with timeout."""
    async def get_cluster_status():
        async with ProxmoxClient(...) as client:
            return await client.cluster.status.get()
    
    try:
        status = await asyncio.wait_for(
            get_cluster_status(),
            timeout=10.0  # seconds
        )
        return status
    except asyncio.TimeoutError:
        print("Operation timed out")
        return None

result = asyncio.run(operation_with_timeout())
```

---

## Performance Optimization

### Batch Operations

```python
async def batch_start_vms(node: str, vmids: list[int]):
    """Start multiple VMs concurrently."""
    async with ProxmoxClient(...) as client:
        # Create all start tasks
        start_tasks = [
            client.nodes(node).qemu(vmid).status.create(command="start")
            for vmid in vmids
        ]
        
        # Execute all at once
        await asyncio.gather(*start_tasks, return_exceptions=True)

asyncio.run(batch_start_vms("pve1", [100, 101, 102, 103]))
```

### Efficient Resource Monitoring

```python
async def monitor_cluster_efficient():
    """Monitor cluster without excessive API calls."""
    async with ProxmoxClient(...) as client:
        # Use resources endpoint (single call)
        resources = await client.cluster.resources.get()
        
        # Filter in memory instead of multiple API calls
        online_nodes = [r for r in resources if r.type == "node" and r.status == "online"]
        running_vms = [r for r in resources if r.type == "qemu" and r.status == "running"]
        
        return online_nodes, running_vms

asyncio.run(monitor_cluster_efficient())
```

### Minimize API Calls

```python
async def get_vm_info_efficient(node: str, vmid: int):
    """Get comprehensive VM info with minimal API calls."""
    async with ProxmoxClient(...) as client:
        # Use gather to parallelize requests
        config, status = await asyncio.gather(
            client.nodes(node).qemu(vmid).config.get(),
            client.nodes(node).qemu(vmid).status.current.get()
        )
        
        return {
            'config': config,
            'status': status
        }
```

### Caching Results

```python
import asyncio
from datetime import datetime, timedelta
from typing import Optional

class CachedProxmoxClient:
    """Client with basic caching."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.cache = {}
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        return str((args, tuple(kwargs.items())))
    
    def _is_valid(self, timestamp: datetime) -> bool:
        return datetime.now() - timestamp < timedelta(seconds=self.ttl)
    
    async def get_cluster_status_cached(self, client):
        """Get cluster status with caching."""
        key = "cluster_status"
        
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if self._is_valid(timestamp):
                return cached_data
        
        # Fetch fresh data
        data = await client.cluster.status.get()
        self.cache[key] = (data, datetime.now())
        return data

cache = CachedProxmoxClient(ttl_seconds=60)

async def get_status_with_cache():
    async with ProxmoxClient(...) as client:
        status = await cache.get_cluster_status_cached(client)
        print(status)

asyncio.run(get_status_with_cache())
```

---

## Task Monitoring

### Monitor Async Tasks

```python
async def monitor_task():
    """Monitor a long-running task."""
    async with ProxmoxClient(...) as client:
        # Create a backup (async task)
        result = await client.nodes("pve1").backup.create(
            vmid=100,
            storage="backup"
        )
        
        # result contains task info like upid, id, node, etc.
        print(f"Task: {result}")
        
        # Monitor task progress
        # (This requires parsing task status - advanced)
        await asyncio.sleep(5)
        
        # Check cluster tasks
        tasks = await client.cluster.tasks.get()
        print(f"Running tasks: {len(tasks)}")
        for task in tasks:
            print(f"  {task.upid}: {task.type}")

asyncio.run(monitor_task())
```

### Wait for Task Completion

```python
import asyncio

async def wait_for_task(upid: str, max_wait: int = 600):
    """Wait for a task to complete."""
    async with ProxmoxClient(...) as client:
        start = asyncio.get_event_loop().time()
        
        while True:
            tasks = await client.cluster.tasks.get()
            
            # Find the task
            task = next((t for t in tasks if t.upid == upid), None)
            
            if task is None:
                # Task completed or doesn't exist
                return
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed > max_wait:
                raise TimeoutError(f"Task {upid} didn't complete in {max_wait}s")
            
            # Wait before checking again
            await asyncio.sleep(5)

asyncio.run(wait_for_task("node/pve1/..."))
```

---

## Streaming and Large Datasets

### Process Large Node Lists

```python
async def process_large_dataset():
    """Process large dataset without loading all in memory."""
    async with ProxmoxClient(...) as client:
        resources = await client.cluster.resources.get()
        
        # Process items one at a time
        vm_count = 0
        running_count = 0
        
        for resource in resources:
            if resource.type == "qemu":
                vm_count += 1
                if resource.status == "running":
                    running_count += 1
        
        print(f"Total VMs: {vm_count}")
        print(f"Running: {running_count}")

asyncio.run(process_large_dataset())
```

### Paginated Results

Proxmox API doesn't have built-in pagination, but you can simulate it:

```python
async def get_resources_limited(limit: int = 100):
    """Get resources with manual limit."""
    async with ProxmoxClient(...) as client:
        all_resources = await client.cluster.resources.get()
        
        # Return limited results
        return all_resources[:limit]

asyncio.run(get_resources_limited(50))
```

---

## Custom HTTP Configuration

### SSL/TLS Configuration

```python
# SSL verification for production
async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",
    password="password",
    verify_ssl=True  # Always True in production
) as client:
    ...

# SSL disabled for development (not recommended)
async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",
    password="password",
    verify_ssl=False  # Only for development!
) as client:
    ...
```

### Timeout Configuration

```python
# Short timeout for quick responses
async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",
    password="password",
    timeout=10.0  # 10 seconds
) as client:
    ...

# Long timeout for slow operations
async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",
    password="password",
    timeout=120.0  # 2 minutes
) as client:
    ...
```

---

## Type Safety and Mypy

### Full Type Checking

Enable strict type checking in your code:

```bash
mypy --strict your_script.py
```

### Type-Annotated Functions

```python
from typing import Optional
from prmxctrl import ProxmoxClient
from prmxctrl.models.nodes import NodeStatusResponse

async def get_node_status(
    client: ProxmoxClient,
    node: str
) -> Optional[NodeStatusResponse]:
    """
    Get node status with full type hints.
    
    Args:
        client: ProxmoxClient instance
        node: Node name
        
    Returns:
        Node status response or None if error
    """
    try:
        return await client.nodes(node).status.get()
    except Exception:
        return None

async def typed_main() -> int:
    """Main function with proper type hints."""
    async with ProxmoxClient(...) as client:
        status: Optional[NodeStatusResponse] = await get_node_status(
            client,
            "pve1"
        )
        if status is None:
            return 1
        print(f"Node: {status.node}")
        return 0

exit_code: int = asyncio.run(typed_main())
```

### Import Models Explicitly

```python
# For maximum type safety, import models explicitly
from prmxctrl import ProxmoxClient
from prmxctrl.models.cluster import ClusterGETResponse
from prmxctrl.models.nodes import (
    NodeStatusResponse,
    QemuVMResponse,
    LXCContainerResponse
)

async def fully_typed():
    async with ProxmoxClient(...) as client:
        cluster_status: ClusterGETResponse = await client.cluster.status.get()
        node_status: NodeStatusResponse = await client.nodes("pve1").status.get()
        vms: list[QemuVMResponse] = await client.nodes("pve1").qemu.list()
        containers: list[LXCContainerResponse] = await client.nodes("pve1").lxc.list()
```

---

## Production Deployment

### Structured Logging

```python
import logging
import logging.handlers
import asyncio
from prmxctrl import ProxmoxClient
from prmxctrl.base.exceptions import ProxmoxAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.handlers.RotatingFileHandler(
            'proxmox.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def production_operation():
    """Example production operation with logging."""
    try:
        logger.info("Starting cluster status check")
        async with ProxmoxClient(...) as client:
            status = await client.cluster.status.get()
            logger.info(f"Cluster status: {status.cluster}")
            
    except ProxmoxAPIError as e:
        logger.error(f"API error: {e.status_code}", extra={'details': e.details})
    except Exception as e:
        logger.exception("Unexpected error")

asyncio.run(production_operation())
```

### Health Checks

```python
async def health_check() -> bool:
    """Check Proxmox API health."""
    try:
        async with ProxmoxClient(...) as client:
            # Try to get version - lightweight, fast
            version = await client.version.get()
            logger.info("Health check passed")
            return True
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

# Periodic health check
async def periodic_health_check():
    while True:
        is_healthy = await health_check()
        if not is_healthy:
            logger.critical("Proxmox API is down!")
            # Take action: notify, failover, etc.
        
        await asyncio.sleep(30)  # Check every 30 seconds

asyncio.run(periodic_health_check())
```

### Graceful Shutdown

```python
import signal
import asyncio

async def main_with_shutdown():
    """Main application with graceful shutdown."""
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    async def shutdown():
        logger.info("Shutting down...")
        # Cancel pending tasks
        tasks = [t for t in asyncio.all_tasks() if not t.done()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    
    loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(shutdown()))
    
    try:
        async with ProxmoxClient(...) as client:
            while True:
                status = await client.cluster.status.get()
                logger.info(f"Cluster status: {status.cluster}")
                await asyncio.sleep(60)
    except asyncio.CancelledError:
        logger.info("Cancelled")
    finally:
        logger.info("Shutdown complete")

asyncio.run(main_with_shutdown())
```

### Rate Limiting

```python
from asyncio import Semaphore
from datetime import datetime, timedelta

class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = []
        self.semaphore = Semaphore(max_requests)
    
    async def acquire(self):
        """Wait for rate limit availability."""
        now = datetime.now()
        # Remove old requests outside window
        self.requests = [
            r for r in self.requests
            if now - r < timedelta(seconds=self.window)
        ]
        
        if len(self.requests) >= self.max_requests:
            # Wait for oldest request to exit window
            oldest = min(self.requests)
            wait_time = (oldest + timedelta(seconds=self.window) - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.requests.append(datetime.now())

limiter = RateLimiter(max_requests=10, window_seconds=60)

async def rate_limited_operation():
    """Rate-limited API calls."""
    async with ProxmoxClient(...) as client:
        await limiter.acquire()
        result = await client.cluster.status.get()
        return result
```

---

## Performance Best Practices Summary

1. **Use async/await patterns** - Enable concurrent operations
2. **Use context managers** - Proper resource cleanup
3. **Batch operations** - Multiple tasks in parallel
4. **Minimize API calls** - Use resources endpoint for filtering
5. **Implement caching** - Cache frequently accessed data
6. **Add timeouts** - Prevent hanging operations
7. **Handle errors gracefully** - Retry with backoff
8. **Log important events** - For monitoring and debugging
9. **Monitor health** - Regular health checks
10. **Use type hints** - Enable mypy strict checking

---

**See Also**: [Examples](./06_EXAMPLES.md) | [Error Handling](./07_ERROR_HANDLING.md) | [Core Concepts](./03_CORE_CONCEPTS.md)
