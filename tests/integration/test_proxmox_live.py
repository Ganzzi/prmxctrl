"""
Live integration tests for prmxctrl SDK against real Proxmox API.

Tests exercise VM lifecycle, cluster monitoring, and VNC proxy endpoints.
Skip with structured evidence when PROXMOX_* env vars are not set.

Environment variables required:
- PROXMOX_HOST — Proxmox API URL (e.g., "https://192.168.1.100:8006")
- PROXMOX_USER — Proxmox API user (e.g., "root@pam")
- PROXMOX_TOKEN_NAME — API token name
- PROXMOX_TOKEN_VALUE — API token secret

Optional:
- TEST_PROXMOX_NODE — Node name for test VM (default: "pve")
- TEST_VM_ID — VM ID for test VM (default: "100")
"""

import os
import pytest


# ---------------------------------------------------------------------------
# Required environment check
# ---------------------------------------------------------------------------


REQUIRED_ENV = ["PROXMOX_HOST", "PROXMOX_USER", "PROXMOX_TOKEN_NAME", "PROXMOX_TOKEN_VALUE"]


def _build_skip_message(missing_vars):
    """Build structured skip message listing missing env vars."""
    lines = ["BUILT_NOT_VERIFIED: Missing environment variables:"]
    for var in missing_vars:
        lines.append(f"  - {var}")
    lines.append("")
    lines.append("Set these variables to enable live Proxmox integration tests:")
    lines.append('  export PROXMOX_HOST="https://your-proxmox:8006"')
    lines.append('  export PROXMOX_USER="root@pam"')
    lines.append('  export PROXMOX_TOKEN_NAME="your-token-name"')
    lines.append('  export PROXMOX_TOKEN_VALUE="your-token-value"')
    return "\n".join(lines)


@pytest.fixture(autouse=True)
def require_proxmox():
    """Skip test if required Proxmox environment variables are not set."""
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        pytest.skip(_build_skip_message(missing))


@pytest.fixture
async def proxmox_client():
    """Create a ProxmoxClient instance from environment variables."""
    from prmxctrl import ProxmoxClient

    client = ProxmoxClient(
        host=os.getenv("PROXMOX_HOST"),
        user=os.getenv("PROXMOX_USER"),
        token_name=os.getenv("PROXMOX_TOKEN_NAME"),
        token_value=os.getenv("PROXMOX_TOKEN_VALUE"),
        verify_ssl=os.getenv("PROXMOX_VERIFY_SSL", "false").lower() == "true",
    )
    yield client
    # No explicit cleanup needed — client uses httpx which handles connection cleanup


# ---------------------------------------------------------------------------
# Cluster monitoring tests
# ---------------------------------------------------------------------------


class TestProxmoxLiveCluster:
    """Live cluster monitoring tests."""

    @pytest.mark.asyncio
    async def test_get_version(self, proxmox_client):
        """Get Proxmox API version."""
        result = await proxmox_client.version.get()
        assert result is not None
        assert "version" in result

    @pytest.mark.asyncio
    async def test_list_nodes(self, proxmox_client):
        """List all nodes in the cluster."""
        nodes = await proxmox_client.nodes.nodes()
        assert isinstance(nodes, list)
        # At least one node should exist
        assert len(nodes) >= 1

    @pytest.mark.asyncio
    async def test_get_node_status(self, proxmox_client):
        """Get status of a specific node."""
        node = os.getenv("TEST_PROXMOX_NODE", "pve")
        result = await proxmox_client.nodes(node).status.status()
        assert result is not None
        assert "uptime" in result or "status" in result


# ---------------------------------------------------------------------------
# VM lifecycle tests (non-destructive)
# ---------------------------------------------------------------------------


class TestProxmoxLiveVMLifecycle:
    """Live VM lifecycle tests — read-only operations."""

    @pytest.mark.asyncio
    async def test_get_vm_status(self, proxmox_client):
        """Get current status of a test VM."""
        node = os.getenv("TEST_PROXMOX_NODE", "pve")
        vmid = int(os.getenv("TEST_VM_ID", "100"))

        status = await proxmox_client.nodes(node).qemu(vmid).status.current.get()
        assert status is not None
        assert "status" in status
        # Status should be one of: running, stopped
        assert status["status"] in ["running", "stopped"]

    @pytest.mark.asyncio
    async def test_get_vm_config(self, proxmox_client):
        """Get configuration of a test VM."""
        node = os.getenv("TEST_PROXMOX_NODE", "pve")
        vmid = int(os.getenv("TEST_VM_ID", "100"))

        config = await proxmox_client.nodes(node).qemu(vmid).config.vm_config()
        assert config is not None
        # Config should have basic fields
        assert "cores" in config or "memory" in config or "name" in config

    @pytest.mark.asyncio
    async def test_list_vms(self, proxmox_client):
        """List all VMs on a node."""
        node = os.getenv("TEST_PROXMOX_NODE", "pve")

        vms = await proxmox_client.nodes(node).qemu.qemu()
        assert isinstance(vms, list)


# ---------------------------------------------------------------------------
# VNC proxy tests
# ---------------------------------------------------------------------------


class TestProxmoxLiveVNCProxy:
    """Live VNC proxy ticket generation tests."""

    @pytest.mark.asyncio
    async def test_get_vnc_proxy_ticket(self, proxmox_client):
        """Get VNC proxy ticket for a test VM."""
        node = os.getenv("TEST_PROXMOX_NODE", "pve")
        vmid = int(os.getenv("TEST_VM_ID", "100"))

        # Get VNC proxy ticket
        ticket_response = await proxmox_client.nodes(node).qemu(vmid).vncproxy.vncproxy(
            params={"websocket": 1}
        )
        assert ticket_response is not None
        assert "ticket" in ticket_response
        assert "port" in ticket_response
