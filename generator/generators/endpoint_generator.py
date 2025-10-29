"""
Endpoint generation utilities for Proxmox API schema.

This module generates hierarchical endpoint classes from parsed schema endpoints,
creating type-safe method calls that mirror the Proxmox API structure.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jinja2

from ..parse_schema import Endpoint, Method


@dataclass
class EndpointClass:
    """Represents a complete endpoint class."""

    name: str
    base_class: str = "EndpointBase"
    docstring: str | None = None
    properties: list[dict[str, Any]] = field(default_factory=list)
    methods: list[dict[str, Any]] = field(default_factory=list)
    call_method: dict[str, Any] | None = None
    methods: list[dict[str, Any]] = field(default_factory=list)
    call_method: dict[str, Any] | None = None


@dataclass
class EndpointFile:
    """Represents a complete Python file with one or more endpoint classes."""

    file_path: str  # Relative path like "access.py" or "nodes/_item.py"
    classes: list[EndpointClass]
    imports: str


class EndpointGenerator:
    """
    Generates hierarchical endpoint classes from parsed Proxmox API schema.

    Creates endpoint classes that mirror the API structure with proper method
    signatures, type hints, and hierarchical navigation.
    """

    def __init__(self):
        self.generated_classes: set[str] = set()
        self.class_counter: dict[str, int] = {}  # Will be initialized in _collect_all_endpoints
        self.endpoint_files: dict[str, EndpointFile] = {}
        self.endpoint_class_names: dict[str, str] = {}  # Map endpoint path to class name
        self.model_name_map: dict[str, str] = {}  # Map base model names to actual names

    def generate_endpoints(
        self, endpoints: list[Endpoint], model_name_map: dict[str, str]
    ) -> list[EndpointFile]:
        """
        Generate endpoint classes for all endpoints.

        Args:
            endpoints: List of parsed Endpoint objects
            model_name_map: Mapping from base model names to actual generated names

        Returns:
            List of EndpointFile objects containing the generated classes
        """
        self.model_name_map = model_name_map  # Store for use in method generation

        # First pass: collect all endpoints and generate class names
        self._collect_all_endpoints(endpoints)

        # Second pass: generate actual classes and files
        self.endpoint_files = {}

        for endpoint in endpoints:
            self._process_endpoint_recursive(endpoint)

        # Third pass: create root endpoint classes for each top-level group
        self._create_root_endpoint_classes(endpoints)

        # Convert to list
        return list(self.endpoint_files.values())

    def _collect_all_endpoints(self, endpoints: list[Endpoint]):
        """First pass: collect all endpoints and pre-generate class names."""
        # First, collect all base names that need class names
        all_base_names = set()

        def collect_base_names(endpoint: Endpoint):
            if endpoint.methods or endpoint.children:
                base_name = self._get_base_name(endpoint)
                all_base_names.add(base_name)
            for child in endpoint.children:
                collect_base_names(child)

        for endpoint in endpoints:
            collect_base_names(endpoint)

        # Sort base names for deterministic ordering
        sorted_base_names = sorted(all_base_names)

        # Pre-assign counters for each base name
        self.class_counter = {}
        for base_name in sorted_base_names:
            self.class_counter[base_name] = 0

        # Now generate class names deterministically
        for endpoint in endpoints:
            self._collect_endpoint_recursive(endpoint)

    def _collect_endpoint_recursive(self, endpoint: Endpoint):
        """Recursively collect endpoint and generate its class name."""
        if endpoint.methods or endpoint.children:
            # Generate class name deterministically
            class_name = self._generate_class_name(endpoint)
            self.endpoint_class_names[endpoint.path] = class_name

        # Process children
        for child in endpoint.children:
            self._collect_endpoint_recursive(child)

    def _process_endpoint_recursive(self, endpoint: Endpoint, parent_path: str = ""):
        """Process endpoint and its children recursively."""
        # Generate class for this endpoint
        endpoint_class = self._generate_endpoint_class(endpoint)

        # Check if this is a root endpoint (only one path part, like "/nodes")
        path_parts = [p for p in endpoint.path.strip("/").split("/") if p]
        is_root_endpoint = len(path_parts) == 1

        if (endpoint_class or endpoint.children) and not is_root_endpoint:
            # Determine file path for this endpoint
            file_path = self._get_file_path(endpoint)

            # Create or get endpoint file
            if file_path not in self.endpoint_files:
                self.endpoint_files[file_path] = EndpointFile(
                    file_path=file_path,
                    classes=[],
                    imports="",
                )

            # Add class if it exists
            if endpoint_class:
                self.endpoint_files[file_path].classes.append(endpoint_class)

        # Process children recursively
        for child in endpoint.children:
            self._process_endpoint_recursive(child, endpoint.path)

    def generate_endpoint_file(self, endpoint: Endpoint, children: list[Endpoint]) -> str:
        """
        Generate endpoint code for a single endpoint file.

        Args:
            endpoint: The main endpoint for this file
            children: Child endpoints

        Returns:
            Generated Python code as string
        """
        # Generate classes for this endpoint
        classes = []

        # Generate main endpoint class
        if endpoint.methods or children:
            main_class = self._generate_endpoint_class(endpoint)
            if main_class:
                classes.append(main_class)

        # Generate additional classes if needed (like item classes)
        # This is simplified - in practice, the full generator handles this

        if not classes:
            return f'"""Generated endpoints for {endpoint.path} - no classes needed"""\n'

        # Collect imports
        imports = self._collect_imports(classes)

        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template("endpoint.py.jinja")

        # Render template
        content = template.render(
            classes=classes,
            imports=imports,
        )

        return content

    def write_endpoints(self, endpoint_files: list[EndpointFile], output_dir: Path):
        """
        Write generated endpoint files to disk.

        Args:
            endpoint_files: List of EndpointFile objects to write
            output_dir: Base output directory (e.g., prmxctrl/endpoints)
        """
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template("endpoint.py.jinja")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Track which directories need __init__.py
        directories_created = set()

        # Write each endpoint file
        for endpoint_file in endpoint_files:
            # Create directory structure if needed
            file_path = output_dir / endpoint_file.file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            directories_created.add(file_path.parent)

            # Update imports for all files in this directory
            endpoint_file.imports = self._collect_imports(endpoint_file.classes)

            # Render template
            content = template.render(
                classes=endpoint_file.classes,
                imports=endpoint_file.imports,
            )

            # Write file
            file_path.write_text(content)

        # Generate __init__.py files for all directories
        for directory in sorted(directories_created):
            self._write_init_file(directory)

    def _write_init_file(self, directory: Path):
        """Write __init__.py file for a directory."""
        init_file = directory / "__init__.py"

        # Collect all Python files in this directory (not subdirectories)
        python_files = []
        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                python_files.append(item)

        # Generate imports
        imports = []
        all_exports = []

        for py_file in sorted(python_files):
            module_name = py_file.stem

            # Check if this is a root module (like cluster.py for cluster/ directory)
            if py_file.name == f"{directory.name}.py":
                # This is the root file, import the main class
                root_class_name = directory.name.replace("-", "_").capitalize() + "Endpoints"
                imports.append(f"from .{module_name} import {root_class_name}")
                all_exports.append(root_class_name)
            else:
                # Import the module
                imports.append(f"from . import {module_name}")
                all_exports.append(module_name)

        # Create __init__.py content
        content = '''"""
Auto-generated endpoint module.

This module contains hierarchical endpoint classes for Proxmox VE API access.
DO NOT EDIT MANUALLY
"""

'''

        if imports:
            content += "\n".join(imports) + "\n\n"

            if all_exports:
                content += "__all__ = [\n"
                for export in all_exports:
                    content += f'    "{export}",\n'
                content += "]\n"

        # Write the file
        init_file.write_text(content)

    def _get_file_path(self, endpoint: Endpoint) -> str:
        """
        Determine the file path for an endpoint using Option B (nested) structure.

        Creates valid Python module names by replacing {param} with param_item.

        Examples:
            /access -> access.py
            /access/users -> access/users.py
            /nodes -> nodes.py
            /nodes/{node} -> nodes/node_item/_item.py
            /nodes/{node}/qemu -> nodes/node_item/qemu.py
            /nodes/{node}/qemu/{vmid} -> nodes/node_item/qemu/vmid_item/_item.py
        """
        path_parts = [p for p in endpoint.path.strip("/").split("/") if p]

        if not path_parts:
            return "common.py"

        # Convert path parts to valid Python identifiers
        # Replace {param} with param_item for valid directory names
        converted_parts = []
        for p in path_parts:
            if p.startswith("{") and p.endswith("}"):
                # {node} -> node_item
                param_name = p.strip("{}")
                # Avoid Python keywords
                if param_name in {
                    "False",
                    "None",
                    "True",
                    "and",
                    "as",
                    "assert",
                    "async",
                    "await",
                    "break",
                    "class",
                    "continue",
                    "def",
                    "del",
                    "elif",
                    "else",
                    "except",
                    "finally",
                    "for",
                    "from",
                    "global",
                    "if",
                    "import",
                    "in",
                    "is",
                    "lambda",
                    "nonlocal",
                    "not",
                    "or",
                    "pass",
                    "raise",
                    "return",
                    "try",
                    "while",
                    "with",
                    "yield",
                }:
                    param_name += "_"
                converted_parts.append(f"{param_name}_item")
            else:
                # Regular parts: replace hyphens with underscores and avoid keywords
                part_name = p.replace("-", "_")
                if part_name in {
                    "False",
                    "None",
                    "True",
                    "and",
                    "as",
                    "assert",
                    "async",
                    "await",
                    "break",
                    "class",
                    "continue",
                    "def",
                    "del",
                    "elif",
                    "else",
                    "except",
                    "finally",
                    "for",
                    "from",
                    "global",
                    "if",
                    "import",
                    "in",
                    "is",
                    "lambda",
                    "nonlocal",
                    "not",
                    "or",
                    "pass",
                    "raise",
                    "return",
                    "try",
                    "while",
                    "with",
                    "yield",
                }:
                    part_name += "_"
                converted_parts.append(part_name)

        # Check if this endpoint has path parameters
        if endpoint.path_params:
            # Item accessor: use _item.py in the appropriate directory
            result_parts = converted_parts + ["_item"]
            filename = "/".join(result_parts) + ".py"
        else:
            # Regular endpoint: use path as module
            filename = "/".join(converted_parts) + ".py"

        return filename

    def _calculate_relative_import(self, from_path: str, to_path: str) -> str:
        """
        Calculate relative import path from one file to another.

        Examples:
            from: access.py, to: access/users.py -> .access.users
            from: nodes/node_item/_item.py, to: nodes/node_item/qemu/_item.py -> .qemu._item
            from: nodes/node_item/qemu/_item.py, to: nodes/node_item/qemu/config/_item.py -> .config._item
        """
        from_parts = from_path.replace(".py", "").split("/")
        to_parts = to_path.replace(".py", "").split("/")

        # Directory path for the from file (excluding the filename)
        from_dir_parts = from_parts[:-1] if from_parts else []
        to_file_parts = to_parts

        # Find common prefix between directory paths
        common_len = 0
        for i, (from_dir, to_file) in enumerate(zip(from_dir_parts, to_file_parts)):
            if from_dir == to_file:
                common_len = i + 1
            else:
                break

        # Calculate relative path
        up_levels = len(from_dir_parts) - common_len
        down_parts = to_file_parts[common_len:]

        # Always include at least one "." for relative imports
        relative_parts = ["."] * (up_levels + 1) + down_parts
        return ".".join(relative_parts)

    def _generate_endpoint_class(self, endpoint: Endpoint) -> EndpointClass | None:
        """Generate an endpoint class for a single endpoint."""
        if not endpoint.methods and not endpoint.children:
            return None

        # Get class name from pre-generated names
        class_name = self.endpoint_class_names.get(endpoint.path)
        if not class_name:
            class_name = self._generate_class_name(endpoint)
            self.endpoint_class_names[endpoint.path] = class_name

        # Create class
        endpoint_class = EndpointClass(
            name=class_name,
            docstring=f"Endpoint class for {endpoint.path}",
        )

        # Generate properties for direct non-parametrized children
        for child in endpoint.children:
            # Only add properties for non-parametrized children (text doesn't contain {param})
            if "{" not in child.text and "}" not in child.text:
                prop_info = self._generate_property(endpoint, child)
                endpoint_class.properties.append(prop_info)

        # Collect forbidden names (property names)
        forbidden_names = {prop["name"] for prop in endpoint_class.properties}

        # Generate methods
        for method_name, method in endpoint.methods.items():
            method_info = self._generate_method(
                endpoint, method_name, method, forbidden_names=forbidden_names
            )
            if method_info:
                endpoint_class.methods.append(method_info)

        # Generate __call__ method if endpoint has children with path parameters
        # Only for collection endpoints (endpoints without path parameters in their text)
        if "{" not in endpoint.text and "}" not in endpoint.text:
            parametrized_children = [
                child for child in endpoint.children if "{" in child.text or "}" in child.text
            ]
            if parametrized_children:
                endpoint_class.call_method = self._generate_call_method(parametrized_children[0])

        return endpoint_class

    def _generate_method(
        self,
        endpoint: Endpoint,
        method_name: str,
        method: Method,
        forbidden_names: set[str] | None = None,
    ) -> dict[str, Any] | None:
        """Generate a method for an HTTP operation."""
        forbidden_names = forbidden_names or set()

        # Map HTTP method to Python method name
        python_method_name = self._get_method_name(method)

        # Avoid conflicts with property names
        if python_method_name in forbidden_names:
            if method.method == "GET":
                python_method_name = "get"
            else:
                python_method_name += "_"

        # Determine parameter model
        param_model = None
        if method.parameters:
            base_name = self._generate_base_model_name(endpoint, method_name, "Request")
            param_model = self.model_name_map.get(base_name)

        # Determine response model
        response_model = None
        if method.returns and method.returns.type != "null":
            base_name = self._generate_base_model_name(endpoint, method_name, "Response")
            response_model = self.model_name_map.get(base_name)

        # Generate return statement
        if method_name == "GET":
            if param_model:
                return_statement = "return await self._get(params=params.model_dump(exclude_none=True) if params else None)"
            else:
                return_statement = "return await self._get()"
        elif method_name == "POST":
            if param_model:
                return_statement = "return await self._post(data=params.model_dump(exclude_none=True) if params else None)"
            else:
                return_statement = "return await self._post()"
        elif method_name == "PUT":
            if param_model:
                return_statement = "return await self._put(data=params.model_dump(exclude_none=True) if params else None)"
            else:
                return_statement = "return await self._put()"
        elif method_name == "DELETE":
            return_statement = "return await self._delete()"
        else:
            return_statement = "# Unknown HTTP method"

        return {
            "name": python_method_name,
            "http_method": method_name,
            "param_model": param_model,
            "response_model": response_model,
            "description": method.description or f"{method_name.upper()} operation",
            "return_statement": return_statement,
        }

    def _generate_method_dict(
        self,
        endpoint: Endpoint,
        method_name: str,
        method: Method,
        forbidden_names: set[str] | None = None,
    ) -> dict[str, Any] | None:
        """Generate method dict for a single method (used by root classes)."""
        forbidden_names = forbidden_names or set()

        # method_name is already the HTTP method like "GET"
        python_method_name = self._get_method_name(method)

        # Avoid conflicts with property names
        if python_method_name in forbidden_names:
            if method.method == "GET":
                python_method_name = "get"
            else:
                python_method_name += "_"

        # Determine parameter model
        param_model = None
        if method.parameters:
            base_name = self._generate_base_model_name(endpoint, method_name, "Request")
            param_model = self.model_name_map.get(base_name)

        # Determine response model
        response_model = None
        if method.returns and method.returns.type != "null":
            base_name = self._generate_base_model_name(endpoint, method_name, "Response")
            response_model = self.model_name_map.get(base_name)

        # Generate return statement
        if method_name == "GET":
            if param_model:
                return_statement = "return await self._get(params=params.model_dump(exclude_none=True) if params else None)"
            else:
                return_statement = "return await self._get()"
        elif method_name == "POST":
            if param_model:
                return_statement = "return await self._post(data=params.model_dump(exclude_none=True) if params else None)"
            else:
                return_statement = "return await self._post()"
        elif method_name == "PUT":
            if param_model:
                return_statement = "return await self._put(data=params.model_dump(exclude_none=True) if params else None)"
            else:
                return_statement = "return await self._put()"
        elif method_name == "DELETE":
            return_statement = "return await self._delete()"
        else:
            return_statement = "# Unknown HTTP method"

        return {
            "name": python_method_name,
            "http_method": method_name,
            "param_model": param_model,
            "response_model": response_model,
            "description": method.description or f"{method_name.upper()} operation",
            "return_statement": return_statement,
        }

    def _generate_property(
        self, current_endpoint: Endpoint, child_endpoint: Endpoint
    ) -> dict[str, Any]:
        """Generate a property for accessing child endpoints."""
        prop_name = child_endpoint.text.replace("-", "_")

        # Avoid Python keywords
        if prop_name in {
            "False",
            "None",
            "True",
            "and",
            "as",
            "assert",
            "async",
            "await",
            "break",
            "class",
            "continue",
            "def",
            "del",
            "elif",
            "else",
            "except",
            "finally",
            "for",
            "from",
            "global",
            "if",
            "import",
            "in",
            "is",
            "lambda",
            "nonlocal",
            "not",
            "or",
            "pass",
            "raise",
            "return",
            "try",
            "while",
            "with",
            "yield",
        }:
            prop_name += "_"

        # Get class name, generating it if not already cached
        if child_endpoint.path in self.endpoint_class_names:
            class_name = self.endpoint_class_names[child_endpoint.path]
        else:
            class_name = self._generate_class_name(child_endpoint)
            self.endpoint_class_names[child_endpoint.path] = class_name

        # Determine import path for the child class
        current_file_path = self._get_file_path(current_endpoint)
        child_file_path = self._get_file_path(child_endpoint)

        # Calculate relative import path
        import_path = self._calculate_relative_import(current_file_path, child_file_path)

        # Special handling for _item files
        if current_file_path.endswith("/_item.py"):
            import_path = f".{prop_name}._item"

        return {
            "name": prop_name,
            "class": class_name,
            "path": child_endpoint.text,
            "module": (
                child_file_path.rsplit("/", 1)[-1].replace(".py", "")
                if "/" in child_file_path
                else child_file_path.replace(".py", "")
            ),
            "import_path": import_path,
        }

    def _generate_call_method(self, child_endpoint: Endpoint) -> dict[str, Any]:
        """Generate __call__ method for parameterized access."""
        # Find the parameter that matches the endpoint text (e.g., {vmid} -> vmid)
        param_name = None
        if child_endpoint.path_params:
            # Try to match the parameter with the endpoint text
            text_param = child_endpoint.text.strip("{}")
            if text_param in child_endpoint.path_params:
                param_name = text_param
            else:
                # Fallback to first parameter
                param_name = child_endpoint.path_params[0]

        if not param_name:
            param_name = "id"  # Default fallback

        # Avoid Python keywords
        if param_name in {
            "False",
            "None",
            "True",
            "and",
            "as",
            "assert",
            "async",
            "await",
            "break",
            "class",
            "continue",
            "def",
            "del",
            "elif",
            "else",
            "except",
            "finally",
            "for",
            "from",
            "global",
            "if",
            "import",
            "in",
            "is",
            "lambda",
            "nonlocal",
            "not",
            "or",
            "pass",
            "raise",
            "return",
            "try",
            "while",
            "with",
            "yield",
        }:
            param_name += "_"

        item_class_name = self.endpoint_class_names.get(child_endpoint.path)
        if not item_class_name:
            item_class_name = self._generate_class_name(child_endpoint)
            self.endpoint_class_names[child_endpoint.path] = item_class_name

        # Determine import path for the child class
        # For parametrized children, the item is in {param_name}_item/_item.py
        import_path = f".{param_name}_item._item"

        # Determine parameter type
        param_type = "str"  # Default
        if (
            "id" in param_name.lower()
            or "vmid" in param_name.lower()
            or "port" in param_name.lower()
        ):
            param_type = "int"

        return {
            "param_name": param_name,
            "param_type": param_type,
            "item_class": item_class_name,
            "import_path": import_path,
        }

    def _get_method_name(self, method: Method) -> str:
        """Convert HTTP method to Python method name."""
        http_method = method.method

        if http_method == "GET":
            # If returns array, call it list(), otherwise get()
            if method.returns and method.returns.type == "array":
                return "list"
            return "get"
        elif http_method == "POST":
            # Use method name or default to create
            method_name = method.name or "create"
        elif http_method == "PUT":
            method_name = method.name or "update"
        elif http_method == "DELETE":
            return "delete"
        else:
            # Fallback
            method_name = method.name or http_method.lower()

        # Sanitize method name to be valid Python identifier
        if method_name:
            method_name = method_name.replace("-", "_")

            # Ensure it's not a Python keyword
            python_keywords = {
                "and",
                "as",
                "assert",
                "async",
                "await",
                "break",
                "class",
                "continue",
                "def",
                "del",
                "elif",
                "else",
                "except",
                "False",
                "finally",
                "for",
                "from",
                "global",
                "if",
                "import",
                "in",
                "is",
                "lambda",
                "None",
                "nonlocal",
                "not",
                "or",
                "pass",
                "raise",
                "return",
                "True",
                "try",
                "while",
                "with",
                "yield",
            }

            if method_name in python_keywords:
                method_name = f"{method_name}_"

        return method_name if method_name else "execute"

    def _get_base_name(self, endpoint: Endpoint) -> str:
        """Get the base name for class name generation."""
        # Use endpoint path to create meaningful name
        path_parts = [p for p in endpoint.path.split("/") if p and not p.startswith("{")]

        if path_parts:
            # Capitalize each part, converting hyphens to underscores first
            name_parts = [part.replace("-", "_").title() for part in path_parts]
            base_name = "".join(name_parts)
        else:
            base_name = "Api"

        # Add suffix
        return f"{base_name}Endpoints"

    def _generate_class_name(self, endpoint: Endpoint) -> str:
        """Generate class name from endpoint using deterministic counters."""
        base_name = self._get_base_name(endpoint)

        # Initialize counter if not exists (for testing or standalone usage)
        if base_name not in self.class_counter:
            self.class_counter[base_name] = 0

        # Get the next available number for this base name
        counter = self.class_counter[base_name]
        self.class_counter[base_name] += 1

        if counter == 0:
            class_name = base_name
        else:
            class_name = f"{base_name}{counter}"

        # Mark as used (for backward compatibility)
        self.generated_classes.add(class_name)

        return class_name

    def _generate_model_name(self, endpoint: Endpoint, method_name: str, suffix: str) -> str:
        """Generate model name for request/response models."""
        # Use endpoint path components to create a meaningful name
        path_parts = [p for p in endpoint.path.split("/") if p and not p.startswith("{")]

        if path_parts:
            # Use the last meaningful path component
            base_name = path_parts[-1].replace("-", "_").title()
        else:
            base_name = "Api"

        # Add method and suffix
        method_part = method_name.upper()
        model_name = f"{base_name}{method_part}{suffix}"

        return model_name

    def _collect_imports(self, classes: list[EndpointClass]) -> str:
        """Collect all imports needed for the endpoint file."""
        imports = []

        # Base import
        imports.append("from prmxctrl.base.endpoint_base import EndpointBase")
        imports.append("from typing import Optional")

        # Collect model imports (endpoint class imports are now done inline)
        model_imports = set()

        for endpoint_class in classes:
            # No longer collect imports for __call__ method - they use inline imports

            for method in endpoint_class.methods:
                if method["param_model"]:
                    model_imports.add(method["param_model"])
                if method["response_model"]:
                    model_imports.add(method["response_model"])

        # Group model imports
        if model_imports:
            imports.append("from prmxctrl.models import (")

            for model_name in sorted(model_imports):
                imports.append(f"    {model_name},")

            imports.append(")")

        return "\n".join(imports)

    def _write_init_file(self, directory: Path):
        """Write __init__.py file for a directory."""
        init_file = directory / "__init__.py"

        # Collect all Python files in this directory (not subdirectories)
        python_files = []
        for item in directory.iterdir():
            if item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
                python_files.append(item)

        # Generate imports
        imports = []
        all_exports = []

        for py_file in sorted(python_files):
            module_name = py_file.stem

            # Check if this is a root module (like cluster.py for cluster/ directory)
            if py_file.name == f"{directory.name}.py":
                # This is the root file, import the main class
                root_class_name = directory.name.replace("-", "_").capitalize() + "Endpoints"
                imports.append(f"from .{module_name} import {root_class_name}")
                all_exports.append(root_class_name)
            else:
                # Import the module
                imports.append(f"from . import {module_name}")
                all_exports.append(module_name)

        # Create __init__.py content
        content = '''"""
Auto-generated endpoint module.

This module contains hierarchical endpoint classes for Proxmox VE API access.
DO NOT EDIT MANUALLY
"""

'''

        if imports:
            content += "\n".join(imports) + "\n\n"

            if all_exports:
                content += "__all__ = [\n"
                for export in all_exports:
                    content += f'    "{export}",\n'
                content += "]\n"

        # Write the file
        init_file.write_text(content)

    def _create_root_endpoint_classes(self, endpoints: list[Endpoint]):
        """Create root endpoint classes that aggregate child endpoints."""

        # Group endpoints by root path
        root_groups = defaultdict(list)

        for endpoint in endpoints:
            path_parts = endpoint.path.strip("/").split("/")
            if path_parts and path_parts[0]:
                root_name = path_parts[0]
                root_groups[root_name].append(endpoint)

        # Create root class for each group
        for root_name, group_endpoints in root_groups.items():
            self._create_root_class_for_group(root_name, group_endpoints)

    def _create_root_class_for_group(self, root_name: str, endpoints: list[Endpoint]):
        """Create a root endpoint class for a group of endpoints."""
        # Generate root class name (e.g., "ClusterEndpoints")
        root_class_name = root_name.replace("-", "_").capitalize() + "Endpoints"

        # Create root endpoint class
        root_class = EndpointClass(
            name=root_class_name,
            docstring=f"Root endpoint class for {root_name} API endpoints.",
            properties=[],
            methods=[],
        )

        # Find the root endpoint and check if it has parametrized children
        root_endpoint = None
        for ep in endpoints:
            if ep.path == f"/{root_name}":
                root_endpoint = ep
                break

        # Add __call__ method if the root endpoint has parametrized children
        if root_endpoint and any(child.path_params for child in root_endpoint.children):
            # Find the first parametrized child
            parametrized_child = next(
                (child for child in root_endpoint.children if child.path_params), None
            )
            if parametrized_child:
                root_class.call_method = self._generate_call_method(parametrized_child)

        # Add properties for each child endpoint
        for endpoint in endpoints:
            if endpoint.path == f"/{root_name}":
                # Skip root endpoint for now, add methods later
                pass
            else:
                # Child endpoint - add as property
                child_class_name = self.endpoint_class_names.get(endpoint.path)
                if child_class_name:
                    # Get the property name from the endpoint path
                    path_parts = endpoint.path.strip("/").split("/")
                    if len(path_parts) > 1:
                        prop_name = path_parts[1]  # Second part after root
                        if "{" in prop_name:
                            prop_name = "_item"  # Dynamic path parameter
                        else:
                            prop_name = prop_name.replace("-", "_")

                        root_class.properties.append(
                            {
                                "name": prop_name,
                                "type": child_class_name,
                                "description": f"Access {endpoint.path} endpoints",
                            }
                        )

        # Collect forbidden names (property names)
        forbidden_names = {prop["name"] for prop in root_class.properties}

        # Add methods for root endpoint
        for endpoint in endpoints:
            if endpoint.path == f"/{root_name}":
                if endpoint.methods:
                    for method_name, method in endpoint.methods.items():
                        method_dict = self._generate_method_dict(
                            endpoint, method_name, method, forbidden_names=forbidden_names
                        )
                        if method_dict:
                            root_class.methods.append(method_dict)

        # Create file for root class
        file_path = f"{root_name}/__init__.py"
        if file_path not in self.endpoint_files:
            self.endpoint_files[file_path] = EndpointFile(
                file_path=file_path,
                classes=[],
                imports="",
            )

        # Add root class to file
        self.endpoint_files[file_path].classes.insert(0, root_class)  # Insert at beginning

    def _generate_base_model_name(self, endpoint: Endpoint, method_name: str, suffix: str) -> str:
        """Generate the base model name without counter."""
        # Use endpoint path to create a unique name
        path = (
            endpoint.path.replace("/", "_")
            .replace("{", "")
            .replace("}", "")
            .replace("-", "_")
            .title()
        )
        if path.startswith("_"):
            path = path[1:]

        # Add method and suffix
        method_part = method_name.upper()
        model_name = f"{path}{method_part}{suffix}"

        return model_name

    def _extract_class_names_from_file(self, content: str) -> list[str]:
        """Extract class names from Python file content."""

        class_names = []
        # Match class definitions
        class_pattern = r"^class\s+(\w+)\s*\("
        for line in content.split("\n"):
            match = re.match(class_pattern, line.strip())
            if match:
                class_names.append(match.group(1))
        return class_names
