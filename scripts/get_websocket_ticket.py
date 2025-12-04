#!/usr/bin/env python3
"""
Get a fresh WebSocket VNC ticket from Proxmox API.

Usage:
    python get_websocket_ticket.py
"""

import os
import requests
import json
from pathlib import Path
import dotenv

dotenv.load_dotenv()

# Configuration
WEBSOCKET_VNC_HOST = os.getenv("PROXMOX_HOST", "192.168.1.224:8006")
WEBSOCKET_VNC_NODE = os.getenv("PROXMOX_NODE", "pve")
WEBSOCKET_VNC_VMID = os.getenv("PROXMOX_VMID", "100")
WEBSOCKET_VNC_TOKEN = os.getenv("PROXMOX_API_TOKEN")

if not WEBSOCKET_VNC_TOKEN:
    print("Error: PROXMOX_API_TOKEN not set in .env file")
    print("Expected format: test@pam!test=91eb1dff-12ba-4c53-9528-1a4d18883c98")
    exit(1)

# Construct API endpoint
url = (
    f"{WEBSOCKET_VNC_HOST}/api2/json/nodes/{WEBSOCKET_VNC_NODE}/qemu/{WEBSOCKET_VNC_VMID}/vncproxy"
)

headers = {
    "Authorization": f"PVEAPIToken={WEBSOCKET_VNC_TOKEN}",
    "Content-Type": "application/json",
}

payload = {
    "generate-password": 0,
    "websocket": 1,
}

print(f"Requesting WebSocket VNC ticket from Proxmox...")
print(f"Endpoint: {url}")

try:
    # Disable SSL verification for self-signed certificates
    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code == 200:
        data = response.json()
        ticket = data.get("data", {}).get("ticket")
        port = data.get("data", {}).get("port")

        if ticket:
            print("\n✓ Successfully retrieved WebSocket ticket!")
            print(f"\nUpdate your .env file with:")
            print(f"WEBSOCKET_VNC_TICKET={ticket}")
            print(f"\nTicket details:")
            print(f"  Ticket: {ticket[:50]}...")
            print(f"  Port: {port}")
            print(f"  Expires in: ~30 seconds")

            # Also update .env file automatically
            env_file = Path(".env")
            if env_file.exists():
                content = env_file.read_text()
                # Replace or add the ticket
                if "WEBSOCKET_VNC_TICKET=" in content:
                    import re

                    content = re.sub(
                        r"WEBSOCKET_VNC_TICKET=.*",
                        f"WEBSOCKET_VNC_TICKET={ticket}",
                        content,
                    )
                else:
                    content += f"\nWEBSOCKET_VNC_TICKET={ticket}\n"

                env_file.write_text(content)
                print(f"\n✓ Updated .env file automatically")

        else:
            print(f"\n✗ Error: No ticket in response")
            print(f"Response: {data}")
    else:
        print(f"\n✗ Error: HTTP {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTroubleshooting:")
    print("  1. Check PROXMOX_API_TOKEN is correct in .env")
    print("  2. Verify Proxmox server is accessible")
    print("  3. Ensure VM exists (WEBSOCKET_VNC_NODE and WEBSOCKET_VNC_VMID are correct)")
