"""
Model generation tool for prmxctrl SDK.

This script generates Pydantic v2 models from the parsed Proxmox API schema.
Run this to regenerate all models after schema updates.
"""

import sys
import os
from pathlib import Path
from typing import List
import json

# Add generator package to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.fetch_schema import SchemaFetcher
from generator.parse_schema import SchemaParser
from generator.generators import ModelGenerator, ModelFile


def generate_models():
    """Generate Pydantic models from schema."""
    print("Generating Pydantic models from Proxmox API schema...")

    # Fetch and parse schema
    print("Loading schema...")
    fetcher = SchemaFetcher()
    raw_schema = fetcher.fetch_and_parse_local()

    parser = SchemaParser()
    endpoints = parser.parse(raw_schema)

    print(f"Parsed {len(endpoints)} top-level endpoints")

    # Generate models
    print("Generating models...")
    generator = ModelGenerator()
    model_files = generator.generate_models(endpoints)

    print(f"Generated {len(model_files)} model files")

    # Write model files
    models_dir = Path(__file__).parent.parent / "prmxctrl" / "models"
    models_dir.mkdir(exist_ok=True)

    for model_file in model_files:
        file_path = models_dir / model_file.filename
        print(f"Writing {file_path}")

        # Render template
        content = render_model_template(model_file)

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Generate __init__.py
    generate_models_init(models_dir, model_files)

    print("Model generation complete!")


def render_model_template(model_file: ModelFile) -> str:
    """Render a model file using Jinja2 template."""
    try:
        from jinja2 import Template
    except ImportError:
        print("Error: jinja2 not installed. Install with: pip install jinja2")
        sys.exit(1)

    # Load template
    template_path = Path(__file__).parent.parent / "generator" / "templates" / "model.py.jinja"
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    template = Template(template_content)

    # Extract module name from filename
    module_name = model_file.filename.replace(".py", "")

    # Render template
    return template.render(
        module_name=module_name, imports=model_file.imports, models=model_file.models
    )


def generate_models_init(models_dir: Path, model_files: List[ModelFile]):
    """Generate __init__.py for models package."""
    init_content = '''"""
Auto-generated Pydantic models for Proxmox API.

This package contains type-safe models for all Proxmox API endpoints,
automatically generated from the API schema.
"""

'''

    # Collect all model names
    all_models = []
    for model_file in model_files:
        for model in model_file.models:
            all_models.append(model.name)

    # Add imports
    for model_file in model_files:
        module_name = model_file.filename.replace(".py", "")
        model_names = [model.name for model in model_file.models]
        if model_names:
            init_content += f"from .{module_name} import {', '.join(model_names)}\n"

    # Add __all__
    if all_models:
        init_content += "\n__all__ = [\n"
        for model in sorted(all_models):
            init_content += f'    "{model}",\n'
        init_content += "]\n"

    # Write __init__.py
    init_path = models_dir / "__init__.py"
    with open(init_path, "w", encoding="utf-8") as f:
        f.write(init_content)

    print(f"Generated {init_path}")


if __name__ == "__main__":
    generate_models()
