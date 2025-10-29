#!/usr/bin/env python3
"""
Proxmox API Test Script

This script loads environment variables from .env file and tests
the connection to a Proxmox server using the prmxctrl SDK.

Usage:
    python scripts/test_proxmox_connection.py

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


def load_env_file():
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

        # Manual loading of .env file
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()


def get_env_vars():
    """Get required environment variables."""
    required_vars = [
        "PROXMOX_HOST",
        "PROXMOX_USERNAME",
        "PROXMOX_PASSWORD",
        "PROXMOX_REALM",
        "PROXMOX_TOKEN_ID",
        "PROXMOX_TOKEN_SECRET",
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

    return env_vars


async def test_password_auth(host: str, username: str, password: str, realm: str):
    """Test password authentication."""
    print(f"\n🔐 Testing password authentication...")
    print(f"   Host: {host}")
    print(f"   User: {username}@{realm}")

    try:
        client = ProxmoxClient(
            host=host,
            user=f"{username}@{realm}",
            password=password,
            verify_ssl=False,  # Disable SSL verification for self-signed certificates
        )
        await client._setup_client()

        # Test basic API call - get version
        print("   Making API call to /version...")
        version_info = await client.version.get()
        print("   ✅ Authentication successful!")
        print(f"   Version info: {version_info}")
        return True

    except Exception as e:
        print(f"   ❌ Password authentication failed: {e}")
        return False


async def test_token_auth(host: str, username: str, realm: str, token_id: str, token_secret: str):
    """Test API token authentication."""
    print(f"\n🔑 Testing API token authentication...")
    print(f"   Host: {host}")
    print(f"   Token: {token_id} for {username}@{realm}")

    try:
        async with ProxmoxClient(
            host=host,
            user=f"{username}@{realm}",
            token_name=token_id,
            token_value=token_secret,
            verify_ssl=False,  # Disable SSL verification for self-signed certificates
        ) as client:
            # Test basic API call - get version
            print("   Making API call to /version...")
            version_info = await client.version.get()
            print("   ✅ Token authentication successful!")
            print(f"   Proxmox Version: {version_info.get('version', 'Unknown')}")
            return True

    except Exception as e:
        print(f"   ❌ Token authentication failed: {e}")
        return False


async def test_node_info(
    host: str, username: str, realm: str, token_id: str, token_secret: str, node: str
):
    """Test getting node information."""
    print(f"\n🖥️  Testing node information retrieval...")
    print(f"   Node: {node}")

    try:
        async with ProxmoxClient(
            host=host,
            user=f"{username}@{realm}",
            token_name=token_id,
            token_value=token_secret,
            verify_ssl=False,  # Disable SSL verification for self-signed certificates
        ) as client:
            # Get node status
            node_status = await client.nodes(node).status.get()
            print("   ✅ Node status retrieved successfully!")
            print(f"   Node: {node_status.get('name', 'Unknown')}")
            print(f"   CPU Usage: {node_status.get('cpu', 0) * 100:.1f}%")
            print(f"   Memory Usage: {node_status.get('memory', {}).get('usage', 0) * 100:.1f}%")
            return True

    except Exception as e:
        print(f"   ❌ Node info retrieval failed: {e}")
        return False


async def test_vmid_info(
    host: str, username: str, realm: str, token_id: str, token_secret: str, node: str, vmid: str
):
    """Test getting VM information."""
    print(f"\n🖥️  Testing VM information retrieval...")
    print(f"   Node: {node}, VMID: {vmid}")

    try:
        async with ProxmoxClient(
            host=host,
            user=f"{username}@{realm}",
            token_name=token_id,
            token_value=token_secret,
            verify_ssl=False,  # Disable SSL verification for self-signed certificates
        ) as client:
            # Get VM status
            vm_status = await client.nodes(node).qemu(vmid).status.current.get()
            print("   ✅ VM status retrieved successfully!")
            print(f"   VM Name: {vm_status.get('name', 'Unknown')}")
            print(f"   Status: {vm_status.get('status', 'Unknown')}")
            print(f"   CPU Usage: {vm_status.get('cpu', 0) * 100:.1f}%")
            print(f"   Memory Usage: {vm_status.get('memory', {}).get('usage', 0) * 100:.1f}%")
            return True

    except Exception as e:
        print(f"   ❌ VM info retrieval failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Proxmox API Connection Test")
    print("=" * 50)

    # Load environment variables
    load_env_file()

    # Get environment variables
    env_vars = get_env_vars()

    host = env_vars["PROXMOX_HOST"]
    username = env_vars["PROXMOX_USERNAME"]
    password = env_vars["PROXMOX_PASSWORD"]
    realm = env_vars["PROXMOX_REALM"]
    token_id = env_vars["PROXMOX_TOKEN_ID"]
    token_secret = env_vars["PROXMOX_TOKEN_SECRET"]
    node = env_vars["PROXMOX_NODE"]
    vmid = env_vars["PROXMOX_VMID"]

    print(f"📋 Configuration loaded:")
    print(f"   Host: {host}")
    print(f"   User: {username}@{realm}")
    print(f"   Token ID: {token_id}")
    print(f"   Node: {node}")
    print(f"   VMID: {vmid}")

    # Test authentication methods
    password_success = await test_password_auth(host, username, password, realm)
    token_success = await test_token_auth(host, username, realm, token_id, token_secret)

    if not password_success and not token_success:
        print("\n❌ All authentication methods failed. Please check your credentials.")
        sys.exit(1)

    # Use token auth for further tests (preferred method)
    if token_success:
        print("\n🔄 Using token authentication for further tests...")

        # Test node information
        await test_node_info(host, username, realm, token_id, token_secret, node)

        # Test VM information
        await test_vmid_info(host, username, realm, token_id, token_secret, node, vmid)

    print("\n" + "=" * 50)
    print("✅ Proxmox API connection test completed!")

    if password_success and token_success:
        print("🎉 Both password and token authentication work!")
    elif token_success:
        print("🎉 Token authentication works! (Password auth failed)")
    elif password_success:
        print("🎉 Password authentication works! (Token auth failed)")


if __name__ == "__main__":
    asyncio.run(main())
