"""
Client generation utilities for Proxmox API SDK.

This module generates the main ProxmoxClient class that provides
access to all API endpoints through hierarchical navigation.
"""

from dataclasses import dataclass

import jinja2

from ..parse_schema import Endpoint


@dataclass
class ClientFile:
    """Represents the generated client file."""

    filename: str
    content: str


class ClientGenerator:
    """
    Generates the main ProxmoxClient class.

    Creates a client class that inherits from HTTPClient and provides
    properties for accessing all root API endpoints.
    """

    def __init__(self):
        pass

    def generate(self, endpoints: list[Endpoint]) -> str:
        """
        Generate the main ProxmoxClient class code.

        Args:
            endpoints: List of parsed root endpoints

        Returns:
            Generated client code as string
        """
        # Collect root endpoint names
        root_endpoints = self._collect_root_endpoints(endpoints)

        # Generate client code using template
        return self._generate_client_code(root_endpoints)

    def generate_client(self, endpoints: list[Endpoint]) -> ClientFile:
        """
        Generate the main ProxmoxClient class.

        Args:
            endpoints: List of parsed root endpoints

        Returns:
            ClientFile containing the generated client code
        """
        # Collect root endpoint names
        root_endpoints = self._collect_root_endpoints(endpoints)

        # Generate client code using template
        template_content = self._generate_client_code(root_endpoints)

        return ClientFile(filename="client.py", content=template_content)

    def _collect_root_endpoints(self, endpoints: list[Endpoint]) -> list[dict[str, str]]:
        """Collect information about root endpoints."""
        root_endpoints = []

        for endpoint in endpoints:
            # Get the root path component
            path_parts = endpoint.path.strip("/").split("/")
            if path_parts and path_parts[0]:
                root_name = path_parts[0]
                module_name = root_name.replace("-", "_")
                class_name = self._generate_root_class_name(root_name)

                root_endpoints.append(
                    {
                        "name": root_name.replace("-", "_"),
                        "class_name": class_name,
                        "module": module_name,
                    }
                )

        return root_endpoints

    def _generate_root_class_name(self, root_name: str) -> str:
        """Generate class name for root endpoint."""
        # Convert hyphens to underscores, capitalize and add suffix
        return root_name.replace("-", "_").capitalize() + "Endpoints"

    def _generate_client_code(self, root_endpoints: list[dict[str, str]]) -> str:
        """Generate the complete client code."""
        # Template for the client
        template = '''"""
Generated Proxmox VE API Client.

This module contains the main ProxmoxClient class for accessing
the Proxmox VE API through type-safe, hierarchical endpoints.
DO NOT EDIT MANUALLY
"""

from typing import Optional
from prmxctrl.base.http_client import HTTPClient

{% for endpoint in root_endpoints %}
from prmxctrl.endpoints.{{ endpoint.module }} import {{ endpoint.class_name }}
{% endfor %}


class ProxmoxClient(HTTPClient):
    """
    Main client for accessing the Proxmox VE API.

    This class provides hierarchical access to all Proxmox API endpoints
    with full type safety and async support.

    Example:
        async with ProxmoxClient(
            host="https://proxmox.example.com:8006",
            user="root@pam",
            password="secret"
        ) as client:
            # Access cluster endpoints
            status = await client.cluster.status.get()

            # Access node-specific endpoints
            nodes = await client.nodes.list()
            node_info = await client.nodes("pve1").status.get()

            # Access VM endpoints
            vm_config = await client.nodes("pve1").qemu(100).config.get()
    """

    def __init__(
        self,
        host: str,
        user: Optional[str] = None,
        password: Optional[str] = None,
        token_name: Optional[str] = None,
        token_value: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: float = 30.0,
    ):
        """
        Initialize the Proxmox API client.

        Args:
            host: Proxmox host URL (e.g., "https://proxmox:8006")
            user: Username for authentication (required for password auth)
            password: Password for authentication (required for password auth)
            token_name: API token name (required for token auth)
            token_value: API token value (required for token auth)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
        """
        super().__init__(
            host=host,
            user=user,
            password=password,
            token_name=token_name,
            token_value=token_value,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

{% for endpoint in root_endpoints %}
    @property
    def {{ endpoint.name }}(self) -> {{ endpoint.class_name }}:
        """Access {{ endpoint.name }} API endpoints."""
        return {{ endpoint.class_name }}(self, "/{{ endpoint.name }}")

{% endfor %}
'''

        # Set up Jinja2 environment
        env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
        template_obj = env.from_string(template)

        # Render template
        return template_obj.render(root_endpoints=root_endpoints)
