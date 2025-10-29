#!/usr/bin/env python3
"""
Simple script to call the vncproxy endpoint using prmxctrl.

Due to a generator bug, vncproxy is not directly accessible through
client.nodes("pve1").qemu(100).vncproxy(). This script shows the workaround.
"""

import asyncio

from prmxctrl import ProxmoxClient
from prmxctrl.models.nodes import (
    Nodes_Node_Qemu_Vmid_VncproxyPOSTRequest,
)


async def call_vncproxy():
    """
    Call the vncproxy endpoint using the generated endpoint class.
    """

    # Configuration - replace with your actual values
    PROXMOX_HOST = "https://your-proxmox-host:8006"
    USER = "root@pam"
    PASSWORD = "your-password"
    NODE = "pve1"
    VMID = 100

    client = ProxmoxClient(
        host=PROXMOX_HOST,
        user=USER,
        password=PASSWORD,
        verify_ssl=False,  # Set to True in production
    )

    res = (
        await client.nodes(NODE)
        .qemu(VMID)
        .vncproxy.vncproxy(
            params=Nodes_Node_Qemu_Vmid_VncproxyPOSTRequest(
                node=NODE,
                vmid=VMID,
                generate_password=0,
                websocket=1,
            )
        )
    )
    res.data


async def main():
    """
    Main function.
    """
    print("VNC Proxy Endpoint Call using prmxctrl")
    print("=" * 40)

    await call_vncproxy()


if __name__ == "__main__":
    asyncio.run(main())
