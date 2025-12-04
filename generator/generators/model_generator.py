"""
Model generation utilities for Proxmox API schema.

This module generates Pydantic v2 models from parsed schema endpoints,
creating type-safe request and response models.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import jinja2

from ..parse_schema import Endpoint, Method
from .type_mapper import TypeMapper


@dataclass
class ModelField:
    """Represents a field in a Pydantic model."""

    name: str
    type_annotation: str
    field_kwargs: dict[str, str]
    description: str | None = None
    original_name: str | None = (
        None  # Original API parameter name (may differ from Python field name)
    )


@dataclass
class PydanticModel:
    """Represents a complete Pydantic model."""

    name: str
    fields: list[ModelField]
    docstring: str | None = None
    base_class: str = "BaseModel"


@dataclass
class ModelFile:
    """Represents a complete Python file with multiple models."""

    filename: str
    models: list[PydanticModel]
    imports: list[str]


class ModelGenerator:
    """
    Generates Pydantic v2 models from parsed Proxmox API schema.

    Creates request models for method parameters and response models
    for return types, with proper type annotations and validation.
    """

    def __init__(self):
        self.type_mapper = TypeMapper()
        self.generated_models: dict[str, PydanticModel] = {}
        self.model_counter = defaultdict(int)

    def generate_models(self, endpoints: list[Endpoint]) -> list[ModelFile]:
        """
        Generate Pydantic models for all endpoints.

        Args:
            endpoints: List of parsed Endpoint objects

        Returns:
            List of ModelFile objects containing the generated models
        """
        # Collect all models by module
        models_by_module: dict[str, list[PydanticModel]] = defaultdict(list)

        def process_endpoint(endpoint: Endpoint):
            """Process a single endpoint and its methods."""
            module_name = self._get_module_name(endpoint)

            # Generate models for each method
            for method_name, method in endpoint.methods.items():
                # Request model
                if method.parameters:
                    request_model = self._generate_request_model(endpoint, method_name, method)
                    if request_model:
                        models_by_module[module_name].append(request_model)

                # Response model
                if method.returns and method.returns.type != "null":
                    response_model = self._generate_response_model(endpoint, method_name, method)
                    if response_model:
                        models_by_module[module_name].append(response_model)

            # Process children
            for child in endpoint.children:
                process_endpoint(child)

        # Process all endpoints
        for endpoint in endpoints:
            process_endpoint(endpoint)

        # Convert to ModelFile objects
        model_files = []
        for module_name, models in models_by_module.items():
            if models:  # Only create files with models
                model_file = self._create_model_file(module_name, models)
                model_files.append(model_file)

        return model_files

    def _create_model_file(self, module_name: str, models: list[PydanticModel]) -> ModelFile:
        """Create a ModelFile from a list of models."""
        # Collect all imports needed
        imports = self._collect_imports(models)

        # Create filename
        filename = f"{module_name}.py"

        return ModelFile(filename=filename, models=models, imports=imports)

    def _collect_imports(self, models: list[PydanticModel]) -> list[str]:
        """Collect all imports needed for the model file."""
        imports = set()
        typing_imports = set()

        # Base Pydantic imports
        imports.add("from pydantic import BaseModel, Field, ConfigDict")

        # Check what typing imports are needed
        for model in models:
            for field in model.fields:
                type_str = field.type_annotation
                if "Optional[" in type_str:
                    typing_imports.add("Optional")
                if "Literal[" in type_str:
                    typing_imports.add("Literal")
                # Always include Any since it's commonly used
                if "Any" in type_str:
                    typing_imports.add("Any")
                # If field type contains custom types, add imports
                if "Proxmox" in type_str:
                    imports.add("from ..base.types import ProxmoxNode, ProxmoxVMID")

        # Add typing imports if any are needed
        if typing_imports:
            imports.add(f"from typing import {', '.join(sorted(typing_imports))}")

        return sorted(imports)

    def generate_models_file_with_names(
        self, endpoints: list[Endpoint], module_name: str
    ) -> tuple[str, dict]:
        """
        Generate model code for a specific module and return model name mapping.

        Args:
            endpoints: List of endpoints for this module
            module_name: Name of the module

        Returns:
            Tuple of (generated Python code as string, dict mapping base names to actual names)
        """
        # Generate models for this module
        models = []
        model_name_map = {}

        for endpoint in endpoints:
            # Generate models for each method
            for method_name, method in endpoint.methods.items():
                # Request model
                if method.parameters:
                    request_model = self._generate_request_model(endpoint, method_name, method)
                    if request_model:
                        models.append(request_model)
                        # Map base name to actual name
                        base_name = self._generate_base_model_name(endpoint, method_name, "Request")
                        model_name_map[base_name] = request_model.name

                # Response model
                if method.returns and method.returns.type != "null":
                    response_model = self._generate_response_model(endpoint, method_name, method)
                    if response_model:
                        models.append(response_model)
                        # Map base name to actual name
                        base_name = self._generate_base_model_name(
                            endpoint, method_name, "Response"
                        )
                        model_name_map[base_name] = response_model.name

        if not models:
            return f'"""Generated models for {module_name} - no models needed"""\n', {}

        # Collect imports
        imports = self._collect_imports(models)

        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template("model.py.jinja")

        # Render template
        content = template.render(
            module_name=module_name,
            imports=imports,
            models=models,
        )

        return content, model_name_map

    def write_models(self, model_files: list[ModelFile], output_dir: Path):
        """
        Write generated model files to disk.

        Args:
            model_files: List of ModelFile objects to write
            output_dir: Base output directory (e.g., prmxctrl/models)
        """
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template("model.py.jinja")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Collect all model names for __init__.py
        all_models = []

        # Write each model file
        for model_file in model_files:
            # Render template
            content = template.render(
                module_name=model_file.filename.replace(".py", ""),
                imports=model_file.imports,
                models=model_file.models,
            )

            # Write file
            output_path = output_dir / model_file.filename
            output_path.write_text(content)

        # Generate __init__.py
        self._write_init_file(output_dir, model_files)

    def _write_init_file(self, output_dir: Path, model_files: list[ModelFile]):
        """Generate models/__init__.py with all exports."""
        init_content = '''"""
Generated Pydantic models for Proxmox VE API.

This module contains all auto-generated Pydantic v2 models for request and response
validation across all API endpoints.
"""

'''

        all_models = []

        # Add imports for all models grouped by file
        for model_file in model_files:
            module_name = model_file.filename.replace(".py", "")
            model_names = [model.name for model in model_file.models]
            if model_names:
                init_content += f"from .{module_name} import {', '.join(model_names)}\n"
                all_models.extend(model_names)

        # Add __all__ export
        init_content += "\n__all__ = [\n"
        for model_name in sorted(all_models):
            init_content += f'    "{model_name}",\n'
        init_content += "]\n"

        # Write __init__.py
        init_path = output_dir / "__init__.py"
        init_path.write_text(init_content)

    def _generate_request_model(
        self, endpoint: Endpoint, method_name: str, method: Method
    ) -> PydanticModel | None:
        """Generate a request model for method parameters."""
        if not method.parameters:
            return None

        # Generate model name
        base_name = self._generate_base_model_name(endpoint, method_name, "Request")
        model_name = self._ensure_unique_name(base_name)

        fields = []
        types_used = set()

        for param in method.parameters:
            # Map parameter type
            param_spec = {
                "type": param.type,
                "format": param.format,
                "optional": param.optional,
                "default": param.default,
                "minimum": param.minimum,
                "maximum": param.maximum,
                "maxLength": param.max_length,
                "pattern": param.pattern,
                "enum": param.enum,
                "properties": param.properties,
            }
            type_annotation, field_kwargs = self.type_mapper.map_parameter_type(
                param_spec, param.name
            )

            # Track types used for imports
            types_used.add(type_annotation)

            # Add description to field_kwargs if present
            if param.description:
                field_kwargs["description"] = param.description

            # Add serialization_alias if field name differs from original (e.g., hyphens to underscores)
            sanitized_name = self._sanitize_field_name(param.name)
            if sanitized_name != param.name:
                # Add alias for serialization (when sending to API)
                field_kwargs["serialization_alias"] = param.name

            # Create field
            field = ModelField(
                name=sanitized_name,
                type_annotation=type_annotation,
                field_kwargs=field_kwargs,
                description=param.description,
                original_name=param.name if sanitized_name != param.name else None,
            )
            fields.append(field)

        if not fields:
            return None

        # Create model
        model = PydanticModel(
            name=model_name,
            fields=fields,
            docstring=f"Request model for {endpoint.path} {method_name.upper()}",
        )

        # Store for potential reuse
        self.generated_models[model_name] = model

        return model

    def _generate_response_model(
        self, endpoint: Endpoint, method_name: str, method: Method
    ) -> PydanticModel | None:
        """Generate a response model for method returns."""
        if not method.returns or method.returns.type == "null":
            return None

        # Generate model name
        base_name = self._generate_base_model_name(endpoint, method_name, "Response")
        model_name = self._ensure_unique_name(base_name)

        # For now, create a simple response model
        # TODO: Handle complex response schemas
        if method.returns.type == "object":
            type_annotation = "dict[str, Any]"
        elif method.returns.type == "array":
            # Check if items are specified
            if hasattr(method.returns, "items") and method.returns.items:
                item_type, _ = self.type_mapper.map_parameter_type(method.returns.items, "item")
                type_annotation = f"list[{item_type}]"
            else:
                type_annotation = "list[Any]"
        else:
            # Primitive type
            type_annotation, _ = self.type_mapper.map_parameter_type(
                {"type": method.returns.type}, "response"
            )

        # Create a simple response model with a single 'data' field
        field = ModelField(
            name="data",
            type_annotation=type_annotation,
            field_kwargs={"description": f"Response data for {method_name.upper()}"},
        )

        model = PydanticModel(
            name=model_name,
            fields=[field],
            docstring=f"Response model for {endpoint.path} {method_name.upper()}",
        )

        # Store for potential reuse
        self.generated_models[model_name] = model

        return model

    def _ensure_unique_name(self, base_name: str) -> str:
        """Ensure a model name is unique by adding counter if needed."""
        counter = self.model_counter[base_name]
        self.model_counter[base_name] += 1

        if counter > 0:
            return f"{base_name}{counter}"
        return base_name

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

    def _get_module_name(self, endpoint: Endpoint) -> str:
        """Get the module name for an endpoint."""
        path_parts = endpoint.path.strip("/").split("/")

        # Use the first path component as module name
        if path_parts and path_parts[0]:
            return path_parts[0]
        else:
            return "common"

    def _sanitize_field_name(self, name: str) -> str:
        """Sanitize field names to be valid Python identifiers."""
        # Replace invalid characters
        name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Ensure it doesn't start with a digit
        if name and name[0].isdigit():
            name = f"field_{name}"

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

        if name in python_keywords:
            name = f"{name}_"

        return name
