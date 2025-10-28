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
from generator.generators.model_generator import ModelGenerator


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
    generator.write_models(model_files, models_dir)

    print("Model generation complete!")


if __name__ == "__main__":
    generate_models()
