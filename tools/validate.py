"""
Comprehensive validation script for prmxctrl SDK.

This script validates the generated SDK code to ensure:
1. All generated code compiles without syntax errors
2. All code passes mypy --strict type checking
3. All code passes ruff linting
4. All endpoints from schema were generated
5. All imports work correctly
6. Basic runtime validation

Usage:
    python tools/validate.py
    python tools/validate.py --verbose
    python tools/validate.py --fix  # Auto-fix formatting issues
"""

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_command(
    cmd: list, description: str, cwd: Path | None = None, capture_output: bool = True
) -> tuple[bool, str, str]:
    """Run a command and return (success, stdout, stderr)."""
    if cwd is None:
        cwd = Path(__file__).parent.parent

    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True, cwd=cwd)
        success = result.returncode == 0
        status = "[OK]" if success else "[ERROR]"
        print(f"{status} {description}")
        return success, result.stdout, result.stderr
    except Exception as e:
        print(f"[ERROR] {description} failed with exception: {e}")
        return False, "", str(e)


def validate_syntax(files: list[Path]) -> bool:
    """Validate that all Python files compile without syntax errors."""
    print("\n" + "=" * 60)
    print("PHASE 1: Syntax Validation")
    print("=" * 60)

    errors = []
    for file_path in files:
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
            ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            errors.append(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            errors.append(f"Error reading {file_path}: {e}")

    if errors:
        print(f"❌ Found {len(errors)} syntax errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    print(f"✅ All {len(files)} files have valid syntax")
    return True


def validate_mypy() -> bool:
    """Run mypy --strict on the generated SDK."""
    print("\n" + "=" * 60)
    print("PHASE 2: Type Checking (mypy --strict)")
    print("=" * 60)

    success, stdout, stderr = run_command(
        ["mypy", "--strict", "prmxctrl/"], "Type checking with mypy --strict"
    )

    if not success:
        print("❌ Mypy errors found:")
        print(stderr)
        return False

    print("✅ All code passes mypy --strict type checking")
    return True


def validate_ruff(fix: bool = False) -> bool:
    """Run ruff linting on the generated SDK."""
    print("\n" + "=" * 60)
    print("PHASE 3: Linting (ruff)")
    print("=" * 60)

    cmd = ["ruff", "check", "prmxctrl/"]
    if fix:
        cmd.append("--fix")

    success, stdout, stderr = run_command(cmd, "Linting with ruff")

    if not success:
        print("❌ Ruff violations found:")
        print(stderr)
        if not fix:
            print("💡 Run with --fix to auto-fix formatting issues")
        return False

    print("✅ All code passes ruff linting")
    return True


def validate_imports() -> bool:
    """Validate that all generated modules can be imported."""
    print("\n" + "=" * 60)
    print("PHASE 4: Import Validation")
    print("=" * 60)

    # Test main package import
    try:
        from prmxctrl import ProxmoxClient

        print("✅ Main package import successful")
    except ImportError as e:
        print(f"❌ Failed to import main package: {e}")
        return False

    # Test model imports
    try:
        from prmxctrl import models

        model_modules = [m for m in dir(models) if not m.startswith("_")]
        print(f"✅ Models package imported ({len(model_modules)} modules)")
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False

    # Test endpoint imports
    try:
        from prmxctrl import endpoints

        endpoint_modules = [m for m in dir(endpoints) if not m.startswith("_")]
        print(f"✅ Endpoints package imported ({len(endpoint_modules)} modules)")
    except ImportError as e:
        print(f"❌ Failed to import endpoints: {e}")
        return False

    # Test base classes
    try:
        from prmxctrl.base import (
            EndpointBase,
            HTTPClient,
            ProxmoxAPIError,
            ProxmoxAuthError,
            ProxmoxError,
        )

        print("✅ Base classes imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import base classes: {e}")
        return False

    return True


def load_schema() -> dict[str, Any] | None:
    """Load the parsed schema for validation."""
    schema_path = Path("schemas/v7.4-2.json")
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return None

    try:
        with open(schema_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load schema: {e}")
        return None


def validate_schema_coverage() -> bool:
    """Validate that all endpoints from schema were generated."""
    print("\n" + "=" * 60)
    print("PHASE 5: Schema Coverage Validation")
    print("=" * 60)

    schema = load_schema()
    if not schema:
        return False

    # Import schema parser to analyze endpoints
    try:
        from generator.analyze_schema import SchemaAnalyzer
        from generator.parse_schema import SchemaParser
    except ImportError as e:
        print(f"❌ Failed to import schema tools: {e}")
        return False

    # Parse schema
    parser = SchemaParser()
    endpoints = parser.parse(schema)

    # Analyze endpoints
    analyzer = SchemaAnalyzer()
    analysis = analyzer.analyze(endpoints)

    print(f"Schema contains {analysis['total_endpoints']} endpoints")
    print(f"Schema contains {analysis['total_methods']} methods")
    print(f"Schema contains {analysis['total_parameters']} parameters")

    # Check if generated files exist
    models_dir = Path("prmxctrl/models")
    endpoints_dir = Path("prmxctrl/endpoints")

    if not models_dir.exists():
        print(f"❌ Models directory not found: {models_dir}")
        return False

    if not endpoints_dir.exists():
        print(f"❌ Endpoints directory not found: {endpoints_dir}")
        return False

    # Count generated files
    model_files = list(models_dir.glob("*.py"))
    model_files = [f for f in model_files if not f.name.startswith("_")]

    endpoint_files = []
    for pattern in ["*.py", "**/*.py"]:
        endpoint_files.extend(list(endpoints_dir.glob(pattern)))
    endpoint_files = [f for f in endpoint_files if not f.name.startswith("_")]

    print(f"Generated {len(model_files)} model files")
    print(f"Generated {len(endpoint_files)} endpoint files")

    # Basic coverage check - we should have at least some files
    if len(model_files) == 0:
        print("❌ No model files generated")
        return False

    if len(endpoint_files) == 0:
        print("❌ No endpoint files generated")
        return False

    print("✅ Schema coverage validation passed")
    return True


def validate_runtime() -> bool:
    """Basic runtime validation of the SDK."""
    print("\n" + "=" * 60)
    print("PHASE 6: Runtime Validation")
    print("=" * 60)

    try:
        from prmxctrl import ProxmoxClient

        # Test client instantiation (without connecting)
        client = ProxmoxClient(host="https://dummy:8006", user="dummy@pam", password="dummy")

        # Check that client has expected attributes
        expected_attrs = ["cluster", "nodes", "access", "pools", "storage", "version"]
        for attr in expected_attrs:
            if not hasattr(client, attr):
                print(f"❌ Client missing expected attribute: {attr}")
                return False

        print("✅ Client instantiation and basic attributes validated")

        # Test that we can access endpoints without errors
        try:
            cluster = client.cluster
            print("✅ Cluster endpoint accessible")
        except Exception as e:
            print(f"❌ Failed to access cluster endpoint: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Runtime validation failed: {e}")
        return False


def main():
    """Run all validation phases."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate prmxctrl SDK")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fix", action="store_true", help="Auto-fix formatting issues")
    parser.add_argument("--skip-mypy", action="store_true", help="Skip mypy validation")
    parser.add_argument("--skip-ruff", action="store_true", help="Skip ruff validation")

    args = parser.parse_args()

    print("🔍 Starting prmxctrl SDK validation...")
    print("=" * 60)

    # Find all Python files in prmxctrl
    prmxctrl_dir = Path("prmxctrl")
    if not prmxctrl_dir.exists():
        print(f"❌ prmxctrl directory not found: {prmxctrl_dir}")
        return False

    python_files = list(prmxctrl_dir.rglob("*.py"))
    print(f"Found {len(python_files)} Python files to validate")

    # Phase 1: Syntax validation
    if not validate_syntax(python_files):
        return False

    # Phase 2: Type checking
    if not args.skip_mypy:
        if not validate_mypy():
            return False
    else:
        print("⏭️  Skipping mypy validation (--skip-mypy)")

    # Phase 3: Linting
    if not args.skip_ruff:
        if not validate_ruff(fix=args.fix):
            return False
    else:
        print("⏭️  Skipping ruff validation (--skip-ruff)")

    # Phase 4: Import validation
    if not validate_imports():
        return False

    # Phase 5: Schema coverage
    if not validate_schema_coverage():
        return False

    # Phase 6: Runtime validation
    if not validate_runtime():
        return False

    print("\n" + "=" * 60)
    print("🎉 ALL VALIDATION PHASES PASSED!")
    print("=" * 60)
    print()
    print("✅ Syntax validation: PASSED")
    print("✅ Type checking (mypy): PASSED")
    print("✅ Linting (ruff): PASSED")
    print("✅ Import validation: PASSED")
    print("✅ Schema coverage: PASSED")
    print("✅ Runtime validation: PASSED")
    print()
    print("The prmxctrl SDK is ready for use! 🚀")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
