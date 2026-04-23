# Error Handling

Comprehensive guide to handling errors and exceptions in prmxctrl.

## Exception Hierarchy

The SDK defines the following exception types:

```
Exception (Python base)
├── ProxmoxError (Base for all SDK exceptions)
│   ├── ProxmoxAuthError (Authentication failures)
│   ├── ProxmoxAPIError (API errors)
│   ├── ProxmoxConnectionError (Network errors)
│   ├── ProxmoxValidationError (Input validation)
│   └── ProxmoxTimeoutError (Operation timeouts)
```

## Common Exceptions

### ProxmoxAuthError

Raised when authentication fails.

**Causes:**
- Invalid username or password
- API token expired or invalid
- User account disabled
- Insufficient permissions

**Handling:**

```python
from prmxctrl import ProxmoxClient
from prmxctrl.base.exceptions import ProxmoxAuthError

async def connect_safe():
    try:
        async with ProxmoxClient(
            host="https://proxmox.example.com:8006",
            user="root@pam",
            password="wrong_password"
        ) as client:
            status = await client.cluster.status.get()
    except ProxmoxAuthError as e:
        print(f"Authentication failed: {e}")
        print("Check your credentials and try again")

asyncio.run(connect_safe())
```

### ProxmoxAPIError

Raised when the API returns an error response.

**Common Status Codes:**
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (auth failed)
- `403` - Forbidden (permission denied)
- `404` - Not Found (resource doesn't exist)
- `500` - Server Error (API error)

**Handling:**

```python
from prmxctrl.base.exceptions import ProxmoxAPIError

async def safe_api_call():
    try:
        async with ProxmoxClient(...) as client:
            # Try to get a non-existent node
            status = await client.nodes("invalid-node").status.get()
    except ProxmoxAPIError as e:
        print(f"API Error: {e.status_code}")
        print(f"Message: {e.message}")
        print(f"Details: {e.details}")
        
        if e.status_code == 404:
            print("Resource not found")
        elif e.status_code == 403:
            print("Permission denied")
        elif e.status_code == 400:
            print("Invalid parameters")

asyncio.run(safe_api_call())
```

**Accessing Error Information:**

```python
try:
    await client.nodes("pve1").qemu(100).delete()
except ProxmoxAPIError as e:
    # Error attributes
    e.status_code  # HTTP status code
    e.message      # Error message
    e.details      # Detailed error information
    str(e)         # Full error string
```

### ProxmoxConnectionError

Raised when connection to the server fails.

**Causes:**
- Host is unreachable
- Server is down
- Network connectivity issues
- Wrong hostname/port

**Handling:**

```python
from prmxctrl.base.exceptions import ProxmoxConnectionError

async def connect_with_retry():
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            async with ProxmoxClient(
                host="https://proxmox.example.com:8006",
                user="root@pam",
                password="password"
            ) as client:
                status = await client.cluster.status.get()
                return status
        except ProxmoxConnectionError as e:
            print(f"Connection failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                print("Max retries exceeded")
                raise

asyncio.run(connect_with_retry())
```

### ProxmoxValidationError

Raised when input validation fails.

**Causes:**
- Invalid parameter types
- Constraint violations (min/max, pattern)
- Missing required parameters
- Invalid enum values

**Handling:**

```python
from pydantic import ValidationError

async def safe_vm_creation():
    async with ProxmoxClient(...) as client:
        try:
            # Invalid vmid (must be >= 100)
            result = await client.nodes("pve1").qemu.create(
                vmid=-1,  # Invalid!
                name="my-vm"
            )
        except ValidationError as e:
            print("Validation failed:")
            for error in e.errors():
                field = error['loc'][0]
                msg = error['msg']
                print(f"  {field}: {msg}")

asyncio.run(safe_vm_creation())
```

### ProxmoxTimeoutError

Raised when an operation times out.

**Causes:**
- Server is slow to respond
- Network latency
- Timeout parameter is too short

**Handling:**

```python
import asyncio
from prmxctrl.base.exceptions import ProxmoxTimeoutError

async def call_with_timeout():
    try:
        async with ProxmoxClient(
            host="https://proxmox.example.com:8006",
            user="root@pam",
            password="password",
            timeout=5.0  # 5 seconds
        ) as client:
            status = await client.cluster.status.get()
    except ProxmoxTimeoutError:
        print("Request timed out")
        print("Try increasing the timeout or check server performance")

asyncio.run(call_with_timeout())
```

## General Exception Handling

### Basic Try-Except

```python
async def basic_error_handling():
    try:
        async with ProxmoxClient(...) as client:
            result = await client.cluster.status.get()
    except Exception as e:
        print(f"Error: {e}")
```

### Handling Multiple Exception Types

```python
from prmxctrl.base.exceptions import (
    ProxmoxAuthError,
    ProxmoxAPIError,
    ProxmoxConnectionError
)

async def multi_exception_handling():
    try:
        async with ProxmoxClient(...) as client:
            status = await client.cluster.status.get()
            
    except ProxmoxAuthError as e:
        print("Authentication failed")
        # Handle authentication error
        
    except ProxmoxConnectionError as e:
        print("Cannot connect to server")
        # Handle connection error
        
    except ProxmoxAPIError as e:
        print(f"API error: {e.status_code}")
        # Handle API error
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Handle any other error

asyncio.run(multi_exception_handling())
```

### Using Context Managers for Cleanup

```python
async def with_cleanup():
    client = ProxmoxClient(...)
    try:
        await client._setup_client()
        
        status = await client.cluster.status.get()
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await client._cleanup_client()

asyncio.run(with_cleanup())
```

## Status Code Handling

Different HTTP status codes indicate different issues:

```python
from prmxctrl.base.exceptions import ProxmoxAPIError

async def handle_status_codes():
    try:
        async with ProxmoxClient(...) as client:
            # Some operation
            ...
    except ProxmoxAPIError as e:
        if e.status_code == 400:
            print("Bad Request - Check your parameters")
            # Handle bad parameters
            
        elif e.status_code == 401:
            print("Unauthorized - Check credentials")
            # Handle auth failure
            
        elif e.status_code == 403:
            print("Forbidden - Check permissions")
            # Handle permission error
            
        elif e.status_code == 404:
            print("Not Found - Resource doesn't exist")
            # Handle missing resource
            
        elif e.status_code == 500:
            print("Server Error - Try again later")
            # Handle server error
            
        else:
            print(f"Unexpected status: {e.status_code}")

asyncio.run(handle_status_codes())
```

## Retry Patterns

### Simple Retry with Exponential Backoff

```python
import asyncio
from prmxctrl.base.exceptions import ProxmoxAPIError

async def operation_with_retry():
    max_retries = 3
    base_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            async with ProxmoxClient(...) as client:
                return await client.cluster.status.get()
                
        except ProxmoxAPIError as e:
            if e.status_code >= 500:
                # Server error - retry with backoff
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Server error, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    print("Max retries exceeded")
                    raise
            else:
                # Client error - don't retry
                raise

asyncio.run(operation_with_retry())
```

### Retry with Custom Logic

```python
async def operation_with_custom_retry():
    retryable_codes = {408, 429, 500, 502, 503, 504}  # Timeout, rate limit, server errors
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            async with ProxmoxClient(...) as client:
                return await client.cluster.resources.get()
                
        except ProxmoxAPIError as e:
            if e.status_code in retryable_codes and attempt < max_retries - 1:
                delay = 2 ** attempt
                print(f"Error {e.status_code}, retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                raise

asyncio.run(operation_with_custom_retry())
```

## Timeout Handling

### Set Operation Timeout

```python
import asyncio

async def operation_with_timeout():
    try:
        async with ProxmoxClient(
            host="https://proxmox.example.com:8006",
            user="root@pam",
            password="password",
            timeout=30.0  # 30 seconds
        ) as client:
            # This operation will timeout after 30 seconds
            status = await client.cluster.status.get()
            
    except asyncio.TimeoutError:
        print("Operation timed out")

asyncio.run(operation_with_timeout())
```

### Timeout with asyncio.wait_for

```python
async def operation_with_wait_for():
    try:
        async with ProxmoxClient(...) as client:
            # Timeout after 5 seconds
            status = await asyncio.wait_for(
                client.cluster.status.get(),
                timeout=5.0
            )
    except asyncio.TimeoutError:
        print("Operation timed out")

asyncio.run(operation_with_wait_for())
```

## Validation Errors

### Catching Pydantic Validation Errors

```python
from pydantic import ValidationError

async def catch_validation_errors():
    try:
        async with ProxmoxClient(...) as client:
            await client.nodes("pve1").qemu.create(
                vmid=999999999,  # Too large
                name="my-vm!"    # Invalid characters
            )
    except ValidationError as e:
        print("Validation errors:")
        for error in e.errors():
            print(f"  {error['loc']}: {error['msg']}")

asyncio.run(catch_validation_errors())
```

### Pre-validate Data

```python
from pydantic import BaseModel, ValidationError

class VMConfig(BaseModel):
    vmid: int  # Must be int
    name: str  # Must be str
    memory: int  # Must be int

async def validate_before_create():
    try:
        # Validate before sending to API
        config = VMConfig(
            vmid=100,
            name="my-vm",
            memory=2048
        )
        
        async with ProxmoxClient(...) as client:
            await client.nodes("pve1").qemu.create(**config.model_dump())
            
    except ValidationError as e:
        print("Configuration invalid:", e)

asyncio.run(validate_before_create())
```

## Logging Errors

### Using Python Logging

```python
import logging
from prmxctrl.base.exceptions import ProxmoxAPIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def operation_with_logging():
    try:
        async with ProxmoxClient(...) as client:
            logger.info("Fetching cluster status...")
            status = await client.cluster.status.get()
            logger.info(f"Cluster status: {status}")
            
    except ProxmoxAPIError as e:
        logger.error(
            f"API error: {e.status_code}",
            extra={
                'message': e.message,
                'details': e.details
            }
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")

asyncio.run(operation_with_logging())
```

## Best Practices

### 1. Always Use Context Manager

```python
# ✅ Good - automatic cleanup and exception safety
async with ProxmoxClient(...) as client:
    result = await client.cluster.status.get()

# ❌ Bad - potential resource leak
client = ProxmoxClient(...)
result = await client.cluster.status.get()
```

### 2. Catch Specific Exceptions

```python
# ✅ Good - handle specific exceptions
try:
    ...
except ProxmoxAuthError:
    print("Auth failed")
except ProxmoxAPIError:
    print("API error")

# ❌ Bad - catches everything including bugs
try:
    ...
except Exception:
    pass
```

### 3. Log Errors for Debugging

```python
# ✅ Good - log errors
logger.error("Operation failed", exc_info=True)

# ❌ Bad - silent failures
try:
    ...
except Exception:
    pass
```

### 4. Implement Retry Logic

```python
# ✅ Good - retry on transient errors
for attempt in range(max_retries):
    try:
        return await operation()
    except ProxmoxConnectionError:
        await asyncio.sleep(2 ** attempt)

# ❌ Bad - fail immediately
await operation()
```

### 5. Provide User Feedback

```python
# ✅ Good - clear error messages
print("Failed to connect: Check host and credentials")

# ❌ Bad - cryptic errors
print(str(e))
```

## Common Error Scenarios

### "Connection refused"

```python
# The Proxmox server is not running or unreachable
# Solution: Check server status and network connectivity

async def check_connection():
    try:
        async with ProxmoxClient(host="https://proxmox:8006", ...) as client:
            await client.version.get()
            print("✓ Connected")
    except ProxmoxConnectionError:
        print("✗ Cannot connect to Proxmox")
        print("  Check: host address, port, firewall, server status")
```

### "Invalid credentials"

```python
# Username, password, or token is incorrect
# Solution: Verify credentials

# Check correct format: username@realm
user = f"root@pam"  # Correct format

async with ProxmoxClient(
    user=user,  # Must be username@realm
    password="correct_password"
) as client:
    ...
```

### "Permission denied"

```python
# User doesn't have permission for this operation
# Solution: Check user roles and ACLs

try:
    await client.access.users.create(...)
except ProxmoxAPIError as e:
    if e.status_code == 403:
        print("User doesn't have permission to create users")
        print("Admin role required")
```

### "Operation timed out"

```python
# Server took too long to respond
# Solution: Increase timeout or check server performance

async with ProxmoxClient(
    timeout=60.0  # Increase from default 30 seconds
) as client:
    result = await client.cluster.backup.create(...)
```

---

**See Also**: [Getting Started](./01-getting-started.md) | [API Reference](./04-api-reference.md) | [Examples](./06-examples.md) | [Advanced Usage](./08-advanced-usage.md)
