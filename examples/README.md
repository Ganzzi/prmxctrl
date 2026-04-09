# Examples

This directory contains usage examples for the prmxctrl SDK.

## Quick Start Example

```python
import asyncio
from prmxctrl import ProxmoxClient

async def main():
    async with ProxmoxClient(
        host="https://your-proxmox-host:8006",
        user="your-username@pve",
        token_name="your-token-name",
        token_value="your-token-secret"
    ) as client:
        # Get cluster status
        status = await client.cluster.status.get()
        print(f"Cluster status: {status}")

        # List all nodes
        nodes = await client.nodes.get()
        for node in nodes:
            print(f"Node: {node.node}")

asyncio.run(main())
```

## More Examples

See the `scripts/` directory for additional examples:
- `scripts/test_proxmox_connection.py` - Test connection to Proxmox
- `scripts/vncproxy_example.py` - VNC proxy usage
- `scripts/get_websocket_ticket.py` - WebSocket ticket handling
