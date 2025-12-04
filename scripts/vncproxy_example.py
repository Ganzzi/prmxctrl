#!/usr/bin/env python3
"""
Script to call the vncproxy endpoint using prmxctrl.

This script demonstrates:
- Loading credentials from environment variables (.env file)
- Supporting both password and API token authentication
- Calling the vncproxy endpoint
- Printing the VNC proxy response data

Usage:
    python scripts/vncproxy_example.py

Environment Variables:
    See .env.example for required variables
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from prmxctrl import ProxmoxClient
from prmxctrl.models.nodes import Nodes_Node_Qemu_Vmid_VncproxyPOSTRequest


def load_env_file() -> None:
    """Load environment variables from .env file."""
    env_file = project_root / ".env"
    if not env_file.exists():
        print(f"❌ Error: .env file not found at {env_file}")
        print("   Please copy .env.example to .env and fill in your credentials")
        sys.exit(1)

    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    except ImportError:
        print("⚠️  python-dotenv not installed, loading environment variables manually...")
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()


def get_env_vars() -> dict[str, str]:
    """Get required environment variables."""
    required_vars = [
        "PROXMOX_HOST",
        "PROXMOX_USERNAME",
        "PROXMOX_REALM",
        "PROXMOX_NODE",
        "PROXMOX_VMID",
    ]

    env_vars = {}
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            env_vars[var] = value
        else:
            missing_vars.append(var)

    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file and ensure all variables are set.")
        sys.exit(1)

    # Optional auth variables
    env_vars["PROXMOX_PASSWORD"] = os.getenv("PROXMOX_PASSWORD", "")
    env_vars["PROXMOX_TOKEN_ID"] = os.getenv("PROXMOX_TOKEN_ID", "")
    env_vars["PROXMOX_TOKEN_SECRET"] = os.getenv("PROXMOX_TOKEN_SECRET", "")

    return env_vars


async def call_vncproxy(
    host: str,
    user: str,
    password: str = "",
    token_id: str = "",
    token_secret: str = "",
    node: str = "pve1",
    vmid: str = "100",
) -> None:
    """
    Call the vncproxy endpoint using the generated endpoint class.

    Args:
        host: Proxmox host URL
        user: Username in format username@realm
        password: User password (for password auth)
        token_id: API token ID (for token auth)
        token_secret: API token secret (for token auth)
        node: Node name
        vmid: Virtual machine ID
    """
    print(f"\n🔌 Calling VNC Proxy endpoint...")
    print(f"   Host: {host}")
    print(f"   User: {user}")
    print(f"   Node: {node}")
    print(f"   VMID: {vmid}")

    # Initialize client based on auth method
    if token_id and token_secret:
        print(f"   Auth: API Token ({token_id})")
        client = ProxmoxClient(
            host=host,
            user=user,
            token_name=token_id,
            token_value=token_secret,
            verify_ssl=False,
        )
    elif password:
        print(f"   Auth: Password")
        client = ProxmoxClient(
            host=host,
            user=user,
            password=password,
            verify_ssl=False,
        )
    else:
        print("❌ Error: No authentication method provided")
        print("   Provide either password OR token_id + token_secret")
        sys.exit(1)

    try:
        await client._setup_client()

        # Call the vncproxy endpoint
        res = await (
            client.nodes(node)
            .qemu(vmid)
            .vncproxy.vncproxy(
                params=Nodes_Node_Qemu_Vmid_VncproxyPOSTRequest(
                    node=node,
                    vmid=vmid,
                    websocket=1,
                )
            )
        )

        print("\n✅ VNC Proxy endpoint called successfully!")
        print("\n📊 Response Data:")
        print(f"cert: {res['cert']}  # SSL certificate for the VNC connection")
        print(f"upid: {res['upid']}  # Unique Process ID for the VNC proxy task")
        print(f"user: {res['user']}  # Authenticated user identifier")
        print(f"port: {res['port']}  # VNC server port number")
        print(f"ticket: {res['ticket']}  # VNC authentication ticket")

    except Exception as e:
        print(f"\n❌ Error calling VNC Proxy endpoint: {e}")
        sys.exit(1)
    finally:
        await client._cleanup_client()


async def main() -> None:
    """Main function."""
    print("🎬 VNC Proxy Endpoint Call using prmxctrl")
    print("=" * 50)

    # Load environment variables
    load_env_file()

    # Get environment variables
    env_vars = get_env_vars()

    host = env_vars["PROXMOX_HOST"]
    username = env_vars["PROXMOX_USERNAME"]
    realm = env_vars["PROXMOX_REALM"]
    password = env_vars["PROXMOX_PASSWORD"]
    token_id = env_vars["PROXMOX_TOKEN_ID"]
    token_secret = env_vars["PROXMOX_TOKEN_SECRET"]
    node = env_vars["PROXMOX_NODE"]
    vmid = env_vars["PROXMOX_VMID"]

    user = f"{username}@{realm}"

    print(f"\n📋 Configuration loaded:")
    print(f"   Host: {host}")
    print(f"   User: {user}")
    print(f"   Node: {node}")
    print(f"   VMID: {vmid}")

    # Call the vncproxy endpoint
    await call_vncproxy(
        host=host,
        user=user,
        password=password,
        token_id=token_id,
        token_secret=token_secret,
        node=node,
        vmid=vmid,
    )

    print("\n" + "=" * 50)
    print("✅ Script completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
