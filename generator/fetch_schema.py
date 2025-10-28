"""Schema fetching and parsing utilities for prmxctrl SDK generation.

This module handles fetching the Proxmox API schema from remote GitHub
and parsing it into structured Python objects.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


class SchemaFetcher:
    """Fetch and parse Proxmox API schema from local or remote sources."""

    # Proxmox v7.4-2 schema commit
    COMMIT = "f42edd7afd805a27fd7a0b027d67ca7adeedc2c6"
    URL = f"https://raw.githubusercontent.com/proxmox/pve-docs/{COMMIT}/api-viewer/apidata.js"

    def __init__(self):
        """Initialize the schema fetcher for remote-only fetching."""
        pass

    async def fetch_remote(self) -> str:
        """Fetch apidata.js from GitHub.

        Returns:
            Raw JavaScript content as string.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(self.URL)
            response.raise_for_status()
            return response.text

    def extract_schema_json(self, js_content: str) -> str:
        """Extract JSON from JavaScript apiSchema definition.

        Args:
            js_content: Raw JavaScript content.

        Returns:
            JSON string containing the schema array.

        Raises:
            ValueError: If apiSchema definition cannot be found or parsed.
        """
        # Remove comments (both // and /* */ style)
        # js_content = re.sub(r"//.*?$", "", js_content, flags=re.MULTILINE)
        # js_content = re.sub(r"/\*.*?\*/", "", js_content, flags=re.DOTALL)

        # Find apiSchema definition - use a more robust approach
        # Look for the pattern: const apiSchema = [ ... ];
        start_match = re.search(r"const\s+apiSchema\s*=\s*\[", js_content)
        if not start_match:
            raise ValueError("Could not find apiSchema definition start")

        start_pos = start_match.end() - 1  # Position of the opening [

        # Find the matching closing ] by counting brackets
        bracket_count = 1  # We start after the opening [
        in_string = False
        escape_next = False
        pos = start_pos + 1

        while pos < len(js_content):
            char = js_content[pos]

            if escape_next:
                escape_next = False
            elif char == "\\":
                escape_next = True
            elif not in_string and char == '"':
                in_string = True
            elif in_string and char == '"':
                in_string = False
            elif not in_string:
                if char == "[":
                    bracket_count += 1
                elif char == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        # Found the matching closing bracket
                        end_pos = pos
                        json_str = js_content[start_pos : end_pos + 1]
                        return json_str

            pos += 1

        raise ValueError("Could not find matching closing bracket for apiSchema")

    def parse_json(self, json_str: str) -> List[Dict[str, Any]]:
        """Parse JSON string to Python objects.

        Args:
            json_str: Valid JSON string.

        Returns:
            Parsed schema as list of dictionaries.

        Raises:
            json.JSONDecodeError: If JSON parsing fails.
        """
        return json.loads(json_str)

    def validate_schema(self, schema: List[Dict[str, Any]]) -> None:
        """Basic validation of parsed schema structure.

        Args:
            schema: Parsed schema list.

        Raises:
            ValueError: If schema structure is invalid.
        """
        if not isinstance(schema, list):
            raise ValueError("Schema must be a list")

        if not schema:
            raise ValueError("Schema cannot be empty")

        # Check that first item has expected structure
        first_item = schema[0]
        required_keys = {"path", "text"}
        if not all(key in first_item for key in required_keys):
            raise ValueError(f"Schema items must have required keys: {required_keys}")

    async def fetch_and_parse(
        self, cache_file: Optional[str] = None, use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Complete pipeline: fetch, parse, validate, and cache schema.

        Args:
            cache_file: Path to cache file. If None, uses schemas/v7.4-2.json.
            use_cache: Whether to use cached file if it exists.

        Returns:
            Parsed and validated schema.

        Raises:
            ValueError: If schema parsing or validation fails.
            httpx.HTTPError: If remote fetch fails.
        """
        if cache_file is None:
            # Default cache location
            project_root = Path(__file__).parent.parent
            cache_file = str(project_root / "schemas" / "v7.4-2.json")

        # Try to load from cache first
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_schema = json.load(f)
                # Validate cached schema
                self.validate_schema(cached_schema)
                return cached_schema
            except (json.JSONDecodeError, ValueError):
                # Cache is corrupted, fetch fresh
                pass

        # Fetch from remote (primary source)
        js_content = await self.fetch_remote()

        # Extract and parse JSON
        json_str = self.extract_schema_json(js_content)
        schema = self.parse_json(json_str)

        # Validate structure
        self.validate_schema(schema)

        # Cache the result
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

        return schema

    def fetch_and_parse_local(self, local_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load and parse schema from local apidata.js file.

        Args:
            local_file: Path to local apidata.js file. If None, uses docs/ref/apidata.js.

        Returns:
            Parsed and validated schema.

        Raises:
            ValueError: If schema parsing or validation fails.
            FileNotFoundError: If local file doesn't exist.
        """
        if local_file is None:
            # Default local location
            project_root = Path(__file__).parent.parent
            local_file = str(project_root / "docs" / "ref" / "apidata.js")

        if not os.path.exists(local_file):
            raise FileNotFoundError(f"Local schema file not found: {local_file}")

        # Read local file
        with open(local_file, "r", encoding="utf-8") as f:
            js_content = f.read()

        # Extract and parse JSON
        json_str = self.extract_schema_json(js_content)
        schema = self.parse_json(json_str)

        # Validate structure
        self.validate_schema(schema)

        return schema
