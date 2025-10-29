"""
Type mapping utilities for Proxmox API schema to Python/Pydantic types.

This module handles the conversion of Proxmox API parameter specifications
to appropriate Python types and Pydantic field definitions.
"""

from enum import Enum
from typing import Any


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
    DICT = "dict[str, Any]"
    LIST = "list[Any]"
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
        "pve-node-list": "list[ProxmoxNode]",
        # VM/Container ID formats
        "pve-vmid": "ProxmoxVMID",
        "pve-vmid-list": "list[ProxmoxVMID]",
        # Storage formats
        "pve-storage-id": "str",  # Storage ID/name
        "pve-storage-id-list": "list[str]",
        # Replication formats
        "pve-replication-job-id": "str",
        "pve-replication-job-id-list": "list[str]",
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
        cls, param_spec: dict[str, Any], param_name: str = ""
    ) -> tuple[str, dict[str, Any]]:
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
        cls, param_spec: dict[str, Any], param_name: str, is_optional: bool, default_value: Any
    ) -> tuple[str, dict[str, Any]]:
        """Map primitive parameter types."""
        param_type = param_spec.get("type", "string")
        param_format = param_spec.get("format")

        # Base type mapping - make more permissive for Proxmox API compatibility
        if param_type == "string":
            python_type = cls._map_string_type(param_spec, default_value)
        elif param_type == "integer":
            # Integers in Proxmox often accept strings like "unlimited"
            python_type = "int | str"
        elif param_type == "number":
            # Numbers in Proxmox can sometimes have string defaults
            python_type = "float | str"
        elif param_type == "boolean":
            # Booleans in Proxmox accept true/false, 1/0, yes/no
            python_type = "bool | int | str"
        elif param_type == "null":
            python_type = "None"
        else:
            # Unknown type, default to string
            python_type = "str"

        # Apply format-specific mapping
        if param_format and isinstance(param_format, str) and param_format in cls.FORMAT_MAPPINGS:
            python_type = cls.FORMAT_MAPPINGS[param_format]

        # Adjust type based on default value compatibility
        python_type = cls._adjust_type_for_default(python_type, default_value)

        # Handle optional types
        if is_optional:
            python_type = f"{python_type} | None"

        # Build Pydantic Field kwargs
        field_kwargs = cls._build_field_kwargs(param_spec, default_value, param_type)

        return python_type, field_kwargs

    @classmethod
    def _adjust_type_for_default(cls, python_type: str, default_value: Any) -> str:
        """
        Adjust the Python type to be compatible with the default value.

        For Proxmox API compatibility, we make types more permissive by default,
        but this method handles any remaining edge cases.
        """
        if default_value is None:
            return python_type

        # For most cases, our permissive base types should handle the defaults
        # This method is kept for future edge cases
        return python_type

    @classmethod
    def _map_string_type(cls, param_spec: dict[str, Any], default_value: Any = None) -> str:
        """Map string type with format considerations."""
        param_format = param_spec.get("format")

        # Handle enum values
        if "enum" in param_spec and param_spec["enum"] is not None:
            enum_values = param_spec["enum"]
            if len(enum_values) <= 10:  # Use Literal for small enums

                # Include default value in enum if it's not already there
                all_values = set(enum_values)
                if default_value is not None and default_value not in all_values:
                    all_values.add(default_value)

                # Create a union of literal values
                literals = [f'"{v}"' for v in sorted(all_values)]
                return f"Literal[{', '.join(literals)}]"
            else:
                # For large enums, use str with validation
                return "str"

        # Handle format-specific types
        if param_format and isinstance(param_format, str):
            if param_format in cls.FORMAT_MAPPINGS:
                return cls.FORMAT_MAPPINGS[param_format]
            elif param_format == "password":
                return "Password"
            elif param_format == "token":
                return "AuthToken"

        return "str"

    @classmethod
    def _map_array_type(
        cls, param_spec: dict[str, Any], param_name: str, is_optional: bool, default_value: Any
    ) -> tuple[str, dict[str, Any]]:
        """Map array parameter types."""
        items_spec = param_spec.get("items", {})
        if not items_spec:
            # Generic array
            python_type = "list[Any]"
        else:
            # Typed array
            item_type, _ = cls.map_parameter_type(items_spec, f"{param_name}_item")
            python_type = f"list[{item_type}]"

        if is_optional:
            python_type = f"{python_type} | None"

        field_kwargs = cls._build_field_kwargs(param_spec, default_value, "array")

        return python_type, field_kwargs

    @classmethod
    def _map_object_type(
        cls, param_spec: dict[str, Any], param_name: str, is_optional: bool, default_value: Any
    ) -> tuple[str, dict[str, Any]]:
        """Map object parameter types."""
        # For now, treat objects as generic dictionaries
        # TODO: Generate nested models for complex objects
        python_type = "dict[str, Any]"

        if is_optional:
            python_type = f"{python_type} | None"

        field_kwargs = cls._build_field_kwargs(param_spec, default_value, "object")

        return python_type, field_kwargs

    @classmethod
    def _build_field_kwargs(
        cls, param_spec: dict[str, Any], default_value: Any, param_type: str = "string"
    ) -> dict[str, Any]:
        """Build Pydantic Field kwargs from parameter constraints."""
        field_kwargs = {}

        # Description
        if "description" in param_spec:
            field_kwargs["description"] = param_spec["description"]

        # Default value
        if default_value is not None:
            field_kwargs["default"] = default_value

        # Numeric constraints (only for numeric types)
        if param_type in ("integer", "number"):
            if "minimum" in param_spec and param_spec["minimum"] is not None:
                try:
                    field_kwargs["ge"] = (
                        int(param_spec["minimum"])
                        if param_type == "integer"
                        else float(param_spec["minimum"])
                    )
                except (ValueError, TypeError):
                    field_kwargs["ge"] = param_spec["minimum"]
            if "maximum" in param_spec and param_spec["maximum"] is not None:
                try:
                    field_kwargs["le"] = (
                        int(param_spec["maximum"])
                        if param_type == "integer"
                        else float(param_spec["maximum"])
                    )
                except (ValueError, TypeError):
                    field_kwargs["le"] = param_spec["maximum"]
            if "exclusiveMinimum" in param_spec and param_spec["exclusiveMinimum"] is not None:
                try:
                    field_kwargs["gt"] = (
                        int(param_spec["exclusiveMinimum"])
                        if param_type == "integer"
                        else float(param_spec["exclusiveMinimum"])
                    )
                except (ValueError, TypeError):
                    field_kwargs["gt"] = param_spec["exclusiveMinimum"]
            if "exclusiveMaximum" in param_spec and param_spec["exclusiveMaximum"] is not None:
                try:
                    field_kwargs["lt"] = (
                        int(param_spec["exclusiveMaximum"])
                        if param_type == "integer"
                        else float(param_spec["exclusiveMaximum"])
                    )
                except (ValueError, TypeError):
                    field_kwargs["lt"] = param_spec["exclusiveMaximum"]

        # String constraints (only for string types)
        if param_type == "string":
            if "minLength" in param_spec and param_spec["minLength"] is not None:
                try:
                    field_kwargs["min_length"] = int(param_spec["minLength"])
                except (ValueError, TypeError):
                    field_kwargs["min_length"] = param_spec["minLength"]
            if "maxLength" in param_spec and param_spec["maxLength"] is not None:
                try:
                    field_kwargs["max_length"] = int(param_spec["maxLength"])
                except (ValueError, TypeError):
                    field_kwargs["max_length"] = param_spec["maxLength"]

            # Pattern validation - temporarily disabled due to regex compilation issues
            # if "pattern" in param_spec and param_spec["pattern"] is not None:
            #     pattern = param_spec["pattern"]
            #     # Convert regex patterns to Python-compatible format
            #     if pattern:
            #         # Fix case-insensitive flag syntax: (?^i:...) -> (?i:...)
            #         pattern = re.sub(r"\(\?\^i:", "(?i:", pattern)
            #         # Skip extremely large patterns that would exceed regex compilation limits
            #         if len(pattern) > 10000:  # Arbitrary limit to prevent compilation issues
            #             # Skip this pattern constraint
            #             pass
            #         else:
            #             field_kwargs["pattern"] = pattern

        # Enum validation (for large enums) - disabled as Pydantic Field doesn't support enum parameter
        # Large enums are handled by returning "str" type without validation
        # if "enum" in param_spec and param_spec["enum"] is not None and len(param_spec["enum"]) > 10:
        #     field_kwargs["enum"] = param_spec["enum"]

        return field_kwargs

    @classmethod
    def get_required_imports(cls, types_used: list[str]) -> list[str]:
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
            # Check for List (legacy - should not happen with new code)
            if "List[" in type_str:
                typing_imports.add("List")

            # Check for Dict (not needed for built-in dict)
            # if "dict[" in type_str:
            #     typing_imports.add("Dict")

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
