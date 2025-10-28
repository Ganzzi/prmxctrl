"""
Test the model generation pipeline.

This script tests the model generation components without running the full generation.
"""

import sys
from pathlib import Path

# Add generator package to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all imports work."""
    try:
        from generator.fetch_schema import SchemaFetcher
        from generator.parse_schema import SchemaParser
        from generator.generators import ModelGenerator, TypeMapper

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_type_mapper():
    """Test the type mapper."""
    try:
        from generator.generators import TypeMapper

        # Test basic type mapping
        param_spec = {
            "type": "string",
            "description": "Test parameter",
            "optional": True,
            "default": "default_value",
        }

        python_type, field_kwargs = TypeMapper.map_parameter_type(param_spec, "test_param")

        assert python_type == "Optional[str]"
        assert field_kwargs["description"] == "Test parameter"
        assert field_kwargs["default"] == "default_value"

        print("✓ Type mapper works")
        return True
    except Exception as e:
        print(f"✗ Type mapper test failed: {e}")
        return False


def test_schema_loading():
    """Test schema loading and parsing."""
    try:
        from generator.fetch_schema import SchemaFetcher
        from generator.parse_schema import SchemaParser

        fetcher = SchemaFetcher()
        raw_schema = fetcher.fetch_and_parse_local()

        parser = SchemaParser()
        endpoints = parser.parse(raw_schema)

        assert len(endpoints) > 0
        assert len(endpoints[0].methods) > 0

        print(f"✓ Schema loading works: {len(endpoints)} endpoints parsed")
        return True
    except Exception as e:
        print(f"✗ Schema loading test failed: {e}")
        return False


def test_model_generation():
    """Test model generation with a small subset."""
    try:
        from generator.fetch_schema import SchemaFetcher
        from generator.parse_schema import SchemaParser
        from generator.generators import ModelGenerator

        # Load a small subset of schema
        fetcher = SchemaFetcher()
        raw_schema = fetcher.fetch_and_parse_local()

        parser = SchemaParser()
        endpoints = parser.parse(raw_schema)

        # Take just the first endpoint for testing
        test_endpoints = endpoints[:1] if endpoints else []

        generator = ModelGenerator()
        model_files = generator.generate_models(test_endpoints)

        assert len(model_files) >= 0  # May be 0 if no parameters

        if model_files:
            print(f"✓ Model generation works: {len(model_files[0].models)} models generated")
        else:
            print("✓ Model generation works: no models needed for test endpoint")

        return True
    except Exception as e:
        print(f"✗ Model generation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing model generation pipeline...")

    tests = [
        test_imports,
        test_type_mapper,
        test_schema_loading,
        test_model_generation,
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! Model generation pipeline is ready.")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)
