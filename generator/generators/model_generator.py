"""
Model generation utilities for Proxmox API schema.

This module generates Pydantic v2 models from parsed schema endpoints,
creating type-safe request and response models.
"""

from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass
from collections import defaultdict
import re
from pathlib import Path
import jinja2

from ..parse_schema import Endpoint, Method, Parameter
from .type_mapper import TypeMapper


@dataclass
class ModelField:
    """Represents a field in a Pydantic model."""

    name: str
    type_annotation: str
    field_kwargs: Dict[str, str]
    description: Optional[str] = None


@dataclass
class PydanticModel:
    """Represents a complete Pydantic model."""

    name: str
    fields: List[ModelField]
    docstring: Optional[str] = None
    base_class: str = "BaseModel"


@dataclass
class ModelFile:
    """Represents a complete Python file with multiple models."""

    filename: str
    models: List[PydanticModel]
    imports: List[str]


class ModelGenerator:
    """
    Generates Pydantic v2 models from parsed Proxmox API schema.

    Creates request models for method parameters and response models
    for return types, with proper type annotations and validation.
    """

    def __init__(self):
        self.type_mapper = TypeMapper()
        self.generated_models: Dict[str, PydanticModel] = {}
        self.model_counter = defaultdict(int)

    def generate_models(self, endpoints: List[Endpoint]) -> List[ModelFile]:
        """
        Generate Pydantic models for all endpoints.

        Args:
            endpoints: List of parsed Endpoint objects

        Returns:
            List of ModelFile objects containing the generated models
        """
        # Collect all models by module
        models_by_module: Dict[str, List[PydanticModel]] = defaultdict(list)

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

    def write_models(self, model_files: List[ModelFile], output_dir: Path):
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

    def _write_init_file(self, output_dir: Path, model_files: List[ModelFile]):
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
    ) -> Optional[PydanticModel]:
        """Generate a request model for method parameters."""
        if not method.parameters:
            return None

        # Generate model name
        model_name = self._generate_model_name(endpoint, method_name, "Request")

        fields = []
        types_used = set()

        for param in method.parameters:
            # Map parameter type
            param_spec = {
                "type": param.type,
                "format": param.format,
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

            # Create field
            field = ModelField(
                name=self._sanitize_field_name(param.name),
                type_annotation=type_annotation,
                field_kwargs=field_kwargs,
                description=param.description,
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
    ) -> Optional[PydanticModel]:
        """Generate a response model for method returns."""
        if not method.returns or method.returns.type == "null":
            return None

        # Generate model name
        model_name = self._generate_model_name(endpoint, method_name, "Response")

        # For now, create a simple response model
        # TODO: Handle complex response schemas
        if method.returns.type == "object":
            type_annotation = "Dict[str, Any]"
        elif method.returns.type == "array":
            # Check if items are specified
            if hasattr(method.returns, "items") and method.returns.items:
                item_type, _ = self.type_mapper.map_parameter_type(method.returns.items, "item")
                type_annotation = f"List[{item_type}]"
            else:
                type_annotation = "List[Any]"
        else:
            # Primitive type
            type_annotation, _ = self.type_mapper.map_parameter_type(
                {"type": method.returns.type}, "response"
            )

        # Create a simple response model with a single 'data' field
        field = ModelField(
            name="data",
            type_annotation=type_annotation,
            field_kwargs={"description": repr(f"Response data for {method_name.upper()}")},
        )

        model = PydanticModel(
            name=model_name,
            fields=[field],
            docstring=f"Response model for {endpoint.path} {method_name.upper()}",
        )

        # Store for potential reuse
        self.generated_models[model_name] = model

        return model

    def _generate_model_name(self, endpoint: Endpoint, method_name: str, suffix: str) -> str:
        """Generate a unique model name."""
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

        # Ensure uniqueness
        counter = self.model_counter[model_name]
        self.model_counter[model_name] += 1

        if counter > 0:
            model_name = f"{model_name}{counter}"

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

    def _create_model_file(self, module_name: str, models: List[PydanticModel]) -> ModelFile:
        """Create a ModelFile from a list of models."""
        # Collect all types used across models
        all_types = set()
        for model in models:
            for field in model.fields:
                all_types.add(field.type_annotation)

        # Generate imports
        imports = self.type_mapper.get_required_imports(list(all_types))

        # Add base Pydantic import
        imports.insert(0, "from pydantic import BaseModel, Field")

        # Create filename
        filename = f"{module_name}.py"

        return ModelFile(filename=filename, models=models, imports=imports)
