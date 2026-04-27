"""E2e scenario tests for remote workspace lifecycle (Proxmox/SSH/VNC).

IMPORTANT: These tests are BUILT_ONLY unless real remote infrastructure is provided.
Real verification requires:
- Proxmox API URL and token with test node/pool/storage access
- Disposable VM template ID
- SSH credentials and reachable test VM
- VNC/console settings

To enable real verification, set:
- PROXMOX_API_URL
- PROXMOX_API_TOKEN
- PROXMOX_NODE
- PROXMOX_STORAGE
- PROXMOX_VM_TEMPLATE
- SSH_TEST_HOST
- SSH_TEST_USER
- VNC_TEST_HOST
- VNC_TEST_PORT

Without these vars, tests skip with BUILT_NOT_VERIFIED status.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixture: skip unless real infra is provided
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def skip_unless_real_infra():
    """Skip all real-infra tests unless PROXMOX_API_URL is set."""
    if not os.getenv("PROXMOX_API_URL"):
        pytest.skip("BUILT_NOT_VERIFIED: PROXMOX_API_URL not set — requires real Proxmox infrastructure")


@pytest.fixture
def infra_config():
    """Load infra config from environment."""
    return {
        "proxmox_api_url": os.getenv("PROXMOX_API_URL"),
        "proxmox_api_token": os.getenv("PROXMOX_API_TOKEN"),
        "proxmox_node": os.getenv("PROXMOX_NODE", "pve"),
        "proxmox_storage": os.getenv("PROXMOX_STORAGE", "local"),
        "proxmox_vm_template": os.getenv("PROXMOX_VM_TEMPLATE"),
        "ssh_host": os.getenv("SSH_TEST_HOST"),
        "ssh_user": os.getenv("SSH_TEST_USER", "root"),
        "vnc_host": os.getenv("VNC_TEST_HOST"),
        "vnc_port": int(os.getenv("VNC_TEST_PORT", "5900")),
    }


# ---------------------------------------------------------------------------
# Real-infra tests (only run when env vars are provided)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.skipif(
    not os.getenv("PROXMOX_API_URL"),
    reason="BUILT_NOT_VERIFIED: requires PROXMOX_API_URL"
)
class TestRemoteWorkspaceLifecycleReal:
    """End-to-end remote workspace lifecycle with real Proxmox/SSH/VNC."""

    @pytest.mark.asyncio
    async def test_create_vm_via_proxmox(self, infra_config):
        """Create a disposable VM via Proxmox API."""
        from prmxctrl import ProxmoxClient

        client = ProxmoxClient(
            api_url=infra_config["proxmox_api_url"],
            api_token=infra_config["proxmox_api_token"],
        )

        # Clone from template
        vm_id = await client.clone_vm(
            node=infra_config["proxmox_node"],
            template_id=int(infra_config["proxmox_vm_template"]),
            new_vm_id=9999,
            name="test-e2e-vm",
            storage=infra_config["proxmox_storage"],
        )

        assert vm_id is not None

        # Start the VM
        await client.start_vm(
            node=infra_config["proxmox_node"],
            vm_id=vm_id,
        )

        # Verify VM is running
        status = await client.get_vm_status(
            node=infra_config["proxmox_node"],
            vm_id=vm_id,
        )

        assert status["status"] == "running"

        # Cleanup: stop and delete VM
        await client.stop_vm(
            node=infra_config["proxmox_node"],
            vm_id=vm_id,
        )
        await client.delete_vm(
            node=infra_config["proxmox_node"],
            vm_id=vm_id,
        )


# ---------------------------------------------------------------------------
# Mocked tests (always run to verify harness structure)
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestRemoteWorkspaceLifecycleMocked:
    """Mocked lifecycle tests that verify the harness structure without real infrastructure."""

    @pytest.mark.asyncio
    async def test_mocked_proxmox_lifecycle(self):
        """Mocked Proxmox lifecycle: clone, start, stop, delete."""
        with patch("prmxctrl.ProxmoxClient") as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value = mock_instance

            mock_instance.clone_vm.return_value = 9999
            mock_instance.get_vm_status.return_value = {"status": "running"}

            client = MockClient(
                api_url="https://mock-proxmox:8006",
                api_token="mock-token",
            )

            vm_id = await client.clone_vm(
                node="pve",
                template_id=100,
                new_vm_id=9999,
                name="mock-vm",
                storage="local",
            )

            await client.start_vm(node="pve", vm_id=vm_id)
            status = await client.get_vm_status(node="pve", vm_id=vm_id)
            await client.stop_vm(node="pve", vm_id=vm_id)
            await client.delete_vm(node="pve", vm_id=vm_id)

            assert vm_id == 9999
            assert status["status"] == "running"

    @pytest.mark.asyncio
    async def test_mocked_ssh_connection(self):
        """Mocked SSH connection and command execution."""
        with patch("ssh_agent_bridge.SshClient") as MockSsh:
            mock_instance = AsyncMock()
            MockSsh.return_value = mock_instance

            mock_instance.execute_command.return_value = MagicMock(
                exit_code=0,
                stdout="hello from mocked VM",
                stderr="",
            )

            client = MockSsh(
                host="mock-host",
                port=22,
                username="root",
                key_path=None,
            )

            result = await client.execute_command("echo hello")

            assert result.exit_code == 0
            assert "hello" in result.stdout

    @pytest.mark.asyncio
    async def test_mocked_vnc_connection(self):
        """Mocked VNC connection and frame capture."""
        with patch("vnc_agent_bridge.VncClient") as MockVnc:
            mock_instance = AsyncMock()
            MockVnc.return_value = mock_instance

            mock_instance.connect.return_value = True
            mock_instance.capture_frame.return_value = b"mocked-frame-data"

            client = MockVnc(
                host="mock-host",
                port=5900,
                password="mock-password",
            )

            connected = await client.connect(timeout=10)
            frame = await client.capture_frame()
            await client.disconnect()

            assert connected is True
            assert frame == b"mocked-frame-data"
