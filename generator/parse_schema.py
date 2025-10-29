"""Schema parsing utilities for prmxctrl SDK generation.

This module handles parsing the raw Proxmox API schema into structured
Python objects with proper type annotations.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Parameter:
    """API parameter definition with validation constraints."""

    name: str
    type: str
    description: str | None = None
    optional: bool = False
    default: Any | None = None
    format: str | None = None
    minimum: int | None = None
    maximum: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[Any] | None = None
    properties: dict[str, Any] | None = None  # For nested objects


@dataclass
class Response:
    """API response definition."""

    type: str
    description: str | None = None
    properties: dict[str, Any] | None = None
    items: dict[str, Any] | None = None  # For array responses


@dataclass
class Method:
    """HTTP method definition with parameters and response."""

    method: Literal["GET", "POST", "PUT", "DELETE"]
    name: str
    description: str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    returns: Response | None = None
    protected: bool = False
    proxyto: str | None = None
    permissions: dict[str, Any] | None = None


@dataclass
class Endpoint:
    """API endpoint definition with hierarchical structure."""

    path: str
    text: str  # URL segment name
    leaf: bool  # True if terminal node
    methods: dict[str, Method] = field(default_factory=dict)
    children: list["Endpoint"] = field(default_factory=list)

    # Parsed metadata
    path_params: list[str] = field(default_factory=list)  # e.g., ['node', 'vmid']
    python_path: str = ""  # e.g., "nodes.qemu.item"
    class_name: str = ""  # e.g., "NodesQemuItemEndpoints"


class SchemaParser:
    """Parse raw schema into structured format."""

    def parse(self, raw_schema: list[dict[str, Any]]) -> list[Endpoint]:
        """Parse schema recursively into Endpoint objects.

        Args:
            raw_schema: Raw schema list from JSON parsing.

        Returns:
            List of parsed Endpoint objects.
        """
        return [self._parse_node(node, parent_path="") for node in raw_schema]

    def _parse_node(self, node: dict[str, Any], parent_path: str) -> Endpoint:
        """Parse single schema node into Endpoint object.

        Args:
            node: Raw schema node dictionary.
            parent_path: Parent path for building full paths.

        Returns:
            Parsed Endpoint object.
        """
        path = node["path"]
        text = node["text"]

        endpoint = Endpoint(path=path, text=text, leaf=node.get("leaf", 0) == 1)

        # Extract path parameters: /nodes/{node}/qemu/{vmid}
        endpoint.path_params = re.findall(r"\{(\w+)\}", path)

        # Parse methods (GET, POST, PUT, DELETE)
        if "info" in node:
            for method_name, method_info in node["info"].items():
                endpoint.methods[method_name] = self._parse_method(method_name, method_info)

        # Parse children recursively
        if "children" in node:
            endpoint.children = [self._parse_node(child, path) for child in node["children"]]

        # Generate Python naming
        endpoint.python_path = self._generate_python_path(path)
        endpoint.class_name = self._generate_class_name(path)

        return endpoint

    def _parse_method(self, method_name: str, method_info: dict[str, Any]) -> Method:
        """Parse method definition.

        Args:
            method_name: HTTP method name (GET, POST, etc.).
            method_info: Raw method information.

        Returns:
            Parsed Method object.
        """
        method = Method(
            method=method_name,
            name=method_info.get("name", ""),
            description=method_info.get("description"),
            protected=method_info.get("protected", 0) == 1,
        )

        # Parse parameters
        if "parameters" in method_info:
            params_info = method_info["parameters"]
            if "properties" in params_info:
                method.parameters = [
                    self._parse_parameter(name, prop)
                    for name, prop in params_info["properties"].items()
                ]

        # Parse response
        if "returns" in method_info:
            method.returns = self._parse_response(method_info["returns"])

        # Additional method properties
        method.proxyto = method_info.get("proxyto")
        method.permissions = method_info.get("permissions")

        return method

    def _parse_parameter(self, name: str, prop: dict[str, Any]) -> Parameter:
        """Parse parameter definition.

        Args:
            name: Parameter name.
            prop: Parameter properties.

        Returns:
            Parsed Parameter object.
        """
        return Parameter(
            name=name,
            type=prop.get("type", "string"),
            description=prop.get("description"),
            optional=prop.get("optional", 0) == 1,
            default=prop.get("default"),
            format=prop.get("format"),
            minimum=prop.get("minimum"),
            maximum=prop.get("maximum"),
            max_length=prop.get("maxLength"),
            pattern=prop.get("pattern"),
            enum=prop.get("enum"),
            properties=prop.get("properties"),  # Nested properties
        )

    def _parse_response(self, response_info: dict[str, Any]) -> Response:
        """Parse response definition.

        Args:
            response_info: Raw response information.

        Returns:
            Parsed Response object.
        """
        return Response(
            type=response_info.get("type", "object"),
            description=response_info.get("description"),
            properties=response_info.get("properties"),
            items=response_info.get("items"),
        )

    def _generate_python_path(self, api_path: str) -> str:
        """Convert API path to Python attribute path.

        Examples:
        /nodes/{node}/qemu/{vmid}/config → nodes.item.qemu.item.config

        Args:
            api_path: API path string.

        Returns:
            Python attribute path.
        """
        parts = api_path.strip("/").split("/")
        python_parts = []

        for part in parts:
            if "{" in part:
                param = part.strip("{}")
                python_parts.append("item")
            else:
                python_parts.append(part)

        return ".".join(python_parts)

    def _generate_class_name(self, api_path: str) -> str:
        """Generate class name from API path.

        Examples:
        /nodes/{node}/qemu/{vmid} → NodesQemuItemEndpoints

        Args:
            api_path: API path string.

        Returns:
            Generated class name.
        """
        parts = api_path.strip("/").split("/")
        name_parts = []

        for part in parts:
            if "{" in part:
                name_parts.append("Item")
            else:
                name_parts.append(part.capitalize())

        return "".join(name_parts) + "Endpoints"
