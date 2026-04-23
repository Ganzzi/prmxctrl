# Authentication

Comprehensive guide to authenticating with the Proxmox VE API using prmxctrl.

## Authentication Methods

The SDK supports two primary authentication methods:

### 1. Password Authentication (Ticket-Based)

Uses username, password, and realm to obtain a session ticket from Proxmox.

**Pros:**
- Simple setup
- Works with existing user credentials
- No additional configuration needed

**Cons:**
- Less secure (stores password in memory)
- Token-based auth is preferred for production

**Implementation:**

```python
from prmxctrl import ProxmoxClient

# Synchronous context manager pattern
async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",  # Format: username@realm
    password="your_password",
    verify_ssl=True
) as client:
    result = await client.cluster.status.get()
```

**Parameters:**
- `host` (str): Proxmox server URL with scheme and port
- `user` (str): Username in format `username@realm`
- `password` (str): User's password
- `verify_ssl` (bool): Verify SSL certificates (default: True)
- `timeout` (float): Request timeout in seconds (default: 30.0)

### 2. API Token Authentication (Recommended)

Uses API tokens for secure, programmatic access. Tokens can be scoped and revoked without changing user passwords.

**Pros:**
- More secure (token-based, no password storage)
- Can be scoped to specific permissions
- Can be easily revoked
- Recommended for production use

**Cons:**
- Requires creating a token in Proxmox UI
- Additional setup step

**Implementation:**

```python
from prmxctrl import ProxmoxClient

async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",  # Still required for token auth
    token_name="my-api-token",
    token_value="12345678-1234-1234-1234-123456789abc",
    verify_ssl=True
) as client:
    result = await client.cluster.status.get()
```

**Parameters:**
- `host` (str): Proxmox server URL with scheme and port
- `user` (str): Username in format `username@realm` (still required)
- `token_name` (str): API token name/ID
- `token_value` (str): API token secret/value
- `verify_ssl` (bool): Verify SSL certificates (default: True)
- `timeout` (float): Request timeout in seconds (default: 30.0)

## Creating API Tokens

### Step 1: Access Proxmox Web Interface

1. Go to `https://your-proxmox-host:8006`
2. Login with your user credentials
3. Navigate to **User Management** → **API Tokens**

### Step 2: Create New Token

1. Click **Add**
2. Fill in the form:
   - **User**: Select your user (e.g., `root@pam`)
   - **Token ID**: Give it a meaningful name (e.g., `my-api-token`)
   - **Expire**: Set expiration date or leave empty for no expiration
3. Click **Add**

### Step 3: Copy Token Value

⚠️ **Important**: The token value is only shown once! Copy it immediately.

```
Proxmox-API-Token=root@pam!my-api-token=12345678-1234-1234-1234-123456789abc
```

- **Token Name** (before `=`): `root@pam!my-api-token`
- **Token Secret** (after `=`): `12345678-1234-1234-1234-123456789abc`

### Step 4: Use in Code

```python
from prmxctrl import ProxmoxClient

async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",
    token_name="my-api-token",
    token_value="12345678-1234-1234-1234-123456789abc"
) as client:
    # Now you can use the client
    ...
```

## Realm Types

Proxmox supports different realms for user authentication:

### Standard Realms

| Realm | Description | Example User |
|-------|-------------|--------------|
| `pam` | Linux PAM authentication | `root@pam` |
| `pve` | Proxmox VE realm (default) | `user@pve` |
| `ldap` | LDAP directory | `user@ldap-realm` |
| `openid` | OpenID Connect | `user@openid-realm` |

**Determine your realm:**

```python
# Check which realms are configured
async with ProxmoxClient(...) as client:
    domains = await client.access.domains.list()
    for domain in domains:
        print(f"Domain: {domain.realm} ({domain.type})")
```

## Security Best Practices

### 1. Environment Variables

Never hardcode credentials in source code:

```python
import os
from dotenv import load_dotenv

load_dotenv()

async with ProxmoxClient(
    host=os.getenv("PROXMOX_HOST"),
    user=os.getenv("PROXMOX_USER"),
    token_name=os.getenv("PROXMOX_TOKEN_ID"),
    token_value=os.getenv("PROXMOX_TOKEN_SECRET")
) as client:
    ...
```

**`.env` file:**
```
PROXMOX_HOST=https://proxmox.example.com:8006
PROXMOX_USER=root@pam
PROXMOX_TOKEN_ID=my-api-token
PROXMOX_TOKEN_SECRET=12345678-1234-1234-1234-123456789abc
```

### 2. Token Scoping

Create tokens with minimal required permissions:

1. In Proxmox UI, go to **Access Control** → **Roles**
2. Create a custom role with only needed permissions
3. Create API token and assign this role
4. This limits damage if token is compromised

### 3. Token Rotation

Regularly rotate API tokens:

1. Create a new token
2. Update your application to use the new token
3. Delete the old token in Proxmox UI

### 4. HTTPS Only

Always use HTTPS (secure connection):

```python
# ✅ Good
client = ProxmoxClient(
    host="https://proxmox.example.com:8006",
    ...
)

# ❌ Bad (insecure)
client = ProxmoxClient(
    host="http://proxmox.example.com:8006",  # No encryption!
    ...
)
```

### 5. SSL Certificate Verification

In production, always verify SSL certificates:

```python
# ✅ Production
async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",
    password="password",
    verify_ssl=True  # Default
) as client:
    ...

# ⚠️ Development/Testing only
async with ProxmoxClient(
    host="https://proxmox.example.com:8006",
    user="root@pam",
    password="password",
    verify_ssl=False  # Don't do this in production!
) as client:
    ...
```

### 6. Session Management

The SDK automatically handles session management:

- **Ticket-based auth**: Tokens are automatically obtained and refreshed
- **Token auth**: Tokens are sent with each request

```python
# Session is automatically managed within the context
async with ProxmoxClient(...) as client:
    # Session automatically created
    await client.cluster.status.get()
    # Session automatically cleaned up
```

## Troubleshooting Authentication

### "Invalid credentials" or "401 Unauthorized"

**Check:**
1. Username and realm are correct (`username@realm`)
2. Password is correct (for password auth)
3. Token ID and secret are correct (for token auth)
4. Token hasn't expired
5. Host URL includes scheme and port (`https://....:8006`)

```python
# Debug: Print what you're sending
print(f"Host: {host}")
print(f"User: {user}")
# Don't print password or token!
```

### "SSL: CERTIFICATE_VERIFY_FAILED"

**Option 1: Update CA certificates**
```bash
pip install --upgrade certifi
```

**Option 2: Disable verification (development only)**
```python
async with ProxmoxClient(
    ...,
    verify_ssl=False
) as client:
    ...
```

**Option 3: Provide custom CA certificate**
```python
# For httpx, custom CA is configured in http_client.py
# This would require modifying the SDK
```

### "Connection refused" or "Cannot connect"

**Check:**
1. Proxmox is running and accessible
2. Firewall allows access to port 8006
3. URL format is correct (`https://host:8006`)
4. No typos in hostname

```bash
# Test connection
curl https://your-proxmox-host:8006/api2/json/version -k
```

### Token has expired

Create a new token:

```python
async with ProxmoxClient(
    ...,
    token_name="new-token",
    token_value="new-token-secret"
) as client:
    ...
```

## Complete Example with Error Handling

```python
import asyncio
import os
from dotenv import load_dotenv
from prmxctrl import ProxmoxClient
from prmxctrl.base.exceptions import ProxmoxAuthError, ProxmoxAPIError

async def main():
    load_dotenv()
    
    try:
        async with ProxmoxClient(
            host=os.getenv("PROXMOX_HOST"),
            user=os.getenv("PROXMOX_USER"),
            token_name=os.getenv("PROXMOX_TOKEN_ID"),
            token_value=os.getenv("PROXMOX_TOKEN_SECRET"),
            verify_ssl=True
        ) as client:
            # Get cluster status
            status = await client.cluster.status.get()
            print(f"✓ Connected to Proxmox cluster")
            
    except ProxmoxAuthError as e:
        print(f"✗ Authentication failed: {e}")
        print(f"  Check your credentials and try again")
        
    except ProxmoxAPIError as e:
        print(f"✗ API error: {e.status_code} - {e.message}")
        
    except ConnectionError:
        print(f"✗ Cannot connect to Proxmox server")
        print(f"  Check host URL and network connectivity")

if __name__ == "__main__":
    asyncio.run(main())
```

---

**See Also**: [Getting Started](./01-getting-started.md) | [Error Handling](./07-error-handling.md) | [Advanced Usage](./08-advanced-usage.md)
