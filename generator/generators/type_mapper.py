"""
Type mapping utilities for Proxmox API schema to Python/Pydantic types.

This module handles the conversion of Proxmox API parameter specifications
to appropriate Python types and Pydantic field definitions.
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
import re


class ProxmoxType(Enum):
    """Proxmox API parameter types."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NULL = "null"


class PythonType(Enum):
    """Python type representations."""

    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    DICT = "Dict[str, Any]"
    LIST = "List[Any]"
    NONE = "None"


class TypeMapper:
    """
    Maps Proxmox API parameter specifications to Python/Pydantic types.

    Handles type conversion, constraints, and Pydantic Field generation.
    """

    # Proxmox custom formats and their Python equivalents
    FORMAT_MAPPINGS = {
        # Node-related formats
        "pve-node": "ProxmoxNode",
        "pve-node-list": "List[ProxmoxNode]",
        # VM/Container ID formats
        "pve-vmid": "ProxmoxVMID",
        "pve-vmid-list": "List[ProxmoxVMID]",
        # Storage formats
        "pve-storage-id": "str",  # Storage ID/name
        "pve-storage-id-list": "List[str]",
        # Replication formats
        "pve-replication-job-id": "str",
        "pve-replication-job-id-list": "List[str]",
        # Config ID formats
        "pve-configid-list": "str",  # Comma-separated list
        # Time formats
        "pve-timezone": "str",
        "pve-calendar-event": "str",
        # Network formats
        "pve-iface": "str",  # Network interface name
        "ipv4": "str",
        "ipv6": "str",
        "ip": "str",  # IPv4 or IPv6
        "cidr": "str",  # CIDR notation
        "mac-addr": "str",
        # Authentication formats
        "pve-userid": "str",  # User ID with realm
        "pve-realm": "str",
        # Generic formats
        "email": "str",
        "uri": "str",
        "uuid": "str",
        "hostname": "str",
    }

    @classmethod
    def map_parameter_type(
        cls, param_spec: Dict[str, Any], param_name: str = ""
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Map a Proxmox parameter specification to Python type and Pydantic Field kwargs.

        Args:
            param_spec: Parameter specification from schema
            param_name: Parameter name for better error messages

        Returns:
            Tuple of (python_type_string, field_kwargs_dict)
        """
        param_type = param_spec.get("type", "string")
        is_optional = param_spec.get("optional", False)
        default_value = param_spec.get("default")

        # Handle array types
        if param_type == "array":
            return cls._map_array_type(param_spec, param_name, is_optional, default_value)

        # Handle object types
        elif param_type == "object":
            return cls._map_object_type(param_spec, param_name, is_optional, default_value)

        # Handle primitive types
        else:
            return cls._map_primitive_type(param_spec, param_name, is_optional, default_value)

    @classmethod
    def _map_primitive_type(
        cls, param_spec: Dict[str, Any], param_name: str, is_optional: bool, default_value: Any
    ) -> Tuple[str, Dict[str, Any]]:
        """Map primitive parameter types."""
        param_type = param_spec.get("type", "string")
        param_format = param_spec.get("format")

        # Base type mapping
        if param_type == "string":
            python_type = cls._map_string_type(param_spec)
        elif param_type == "integer":
            python_type = "int"
        elif param_type == "number":
            python_type = "float"
        elif param_type == "boolean":
            python_type = "bool"
        elif param_type == "null":
            python_type = "None"
        else:
            # Unknown type, default to string
            python_type = "str"

        # Apply format-specific mapping
        if param_format and param_format in cls.FORMAT_MAPPINGS:
            python_type = cls.FORMAT_MAPPINGS[param_format]

        # Handle optional types
        if is_optional:
            python_type = f"Optional[{python_type}]"

        # Build Pydantic Field kwargs
        field_kwargs = cls._build_field_kwargs(param_spec, default_value)

        return python_type, field_kwargs

    @classmethod
    def _map_string_type(cls, param_spec: Dict[str, Any]) -> str:
        """Map string type with format considerations."""
        param_format = param_spec.get("format")

        # Handle enum values
        if "enum" in param_spec:
            enum_values = param_spec["enum"]
            if len(enum_values) <= 10:  # Use Literal for small enums
                from typing import Literal

                # Create a union of literal values
                literals = [f'"{v}"' for v in enum_values]
                return f"Literal[{', '.join(literals)}]"
            else:
                # For large enums, use str with validation
                return "str"

        # Handle format-specific types
        if param_format:
            if param_format in cls.FORMAT_MAPPINGS:
                return cls.FORMAT_MAPPINGS[param_format]
            elif param_format == "password":
                return "Password"
            elif param_format == "token":
                return "AuthToken"

        return "str"

    @classmethod
    def _map_array_type(
        cls, param_spec: Dict[str, Any], param_name: str, is_optional: bool, default_value: Any
    ) -> Tuple[str, Dict[str, Any]]:
        """Map array parameter types."""
        items_spec = param_spec.get("items", {})
        if not items_spec:
            # Generic array
            python_type = "List[Any]"
        else:
            # Typed array
            item_type, _ = cls.map_parameter_type(items_spec, f"{param_name}_item")
            python_type = f"List[{item_type}]"

        if is_optional:
            python_type = f"Optional[{python_type}]"

        field_kwargs = cls._build_field_kwargs(param_spec, default_value)

        return python_type, field_kwargs

    @classmethod
    def _map_object_type(
        cls, param_spec: Dict[str, Any], param_name: str, is_optional: bool, default_value: Any
    ) -> Tuple[str, Dict[str, Any]]:
        """Map object parameter types."""
        # For now, treat objects as generic dictionaries
        # TODO: Generate nested models for complex objects
        python_type = "Dict[str, Any]"

        if is_optional:
            python_type = f"Optional[{python_type}]"

        field_kwargs = cls._build_field_kwargs(param_spec, default_value)

        return python_type, field_kwargs

    @classmethod
    def _build_field_kwargs(cls, param_spec: Dict[str, Any], default_value: Any) -> Dict[str, Any]:
        """Build Pydantic Field kwargs from parameter constraints."""
        field_kwargs = {}

        # Description
        if "description" in param_spec:
            field_kwargs["description"] = param_spec["description"]

        # Default value
        if "default" in param_spec:
            field_kwargs["default"] = param_spec["default"]

        # Numeric constraints
        if "minimum" in param_spec:
            field_kwargs["ge"] = param_spec["minimum"]
        if "maximum" in param_spec:
            field_kwargs["le"] = param_spec["maximum"]
        if "exclusiveMinimum" in param_spec:
            field_kwargs["gt"] = param_spec["exclusiveMinimum"]
        if "exclusiveMaximum" in param_spec:
            field_kwargs["lt"] = param_spec["exclusiveMaximum"]

        # String constraints
        if "minLength" in param_spec:
            field_kwargs["min_length"] = param_spec["minLength"]
        if "maxLength" in param_spec:
            field_kwargs["max_length"] = param_spec["maxLength"]

        # Pattern validation
        if "pattern" in param_spec:
            field_kwargs["pattern"] = param_spec["pattern"]

        # Enum validation (for large enums)
        if "enum" in param_spec and len(param_spec["enum"]) > 10:
            field_kwargs["enum"] = param_spec["enum"]

        return field_kwargs

    @classmethod
    def get_required_imports(cls, types_used: List[str]) -> List[str]:
        """
        Get required import statements for the given types.

        Args:
            types_used: List of Python type strings used in the model

        Returns:
            List of import statements
        """
        imports = set()

        # Standard typing imports
        typing_imports = set()
        pydantic_imports = set()

        for type_str in types_used:
            # Check for Optional
            if "Optional[" in type_str:
                typing_imports.add("Optional")

            # Check for List
            if "List[" in type_str:
                typing_imports.add("List")

            # Check for Dict
            if "Dict[" in type_str:
                typing_imports.add("Dict")

            # Check for Literal
            if "Literal[" in type_str:
                typing_imports.add("Literal")

            # Check for Pydantic types
            if "Field(" in type_str:
                pydantic_imports.add("Field")

            # Check for custom types
            if "ProxmoxNode" in type_str:
                imports.add("from ..types import ProxmoxNode")
            if "ProxmoxVMID" in type_str:
                imports.add("from ..types import ProxmoxVMID")
            if "Password" in type_str:
                imports.add("from ..types import Password")
            if "AuthToken" in type_str:
                imports.add("from ..types import AuthToken")

        # Add typing imports
        if typing_imports:
            imports.add(f"from typing import {', '.join(sorted(typing_imports))}")

        # Add Pydantic imports
        if pydantic_imports:
            imports.add(f"from pydantic import {', '.join(sorted(pydantic_imports))}")

        return sorted(imports)
