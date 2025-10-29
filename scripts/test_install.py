#!/usr/bin/env python3
"""
Test script to verify prmxctrl package installation and basic functionality.
"""

import asyncio
import sys

from prmxctrl import ProxmoxClient


async def test_basic_import():
    """Test that we can import and instantiate the client."""
    print("✓ Successfully imported ProxmoxClient")

    # Test client instantiation (without connecting)
    try:
        client = ProxmoxClient(host="https://dummy-host:8006", user="test@pve", password="dummy")
        print("✓ Successfully created ProxmoxClient instance")
    except Exception as e:
        print(f"✗ Failed to create client: {e}")
        return False

    # Test that client has expected attributes
    expected_attrs = ["cluster", "nodes", "access", "pools", "storage", "version"]
    for attr in expected_attrs:
        if hasattr(client, attr):
            print(f"✓ Client has {attr} attribute")
        else:
            print(f"✗ Client missing {attr} attribute")
            return False

    # Test hierarchical access
    try:
        nodes_endpoint = client.nodes
        print("✓ Can access client.nodes")
    except Exception as e:
        print(f"✗ Failed to access client.nodes: {e}")
        return False

    return True


async def test_models():
    """Test that models can be imported."""
    try:
        from prmxctrl.models import (
            AccessGETResponse,
            ClusterGETResponse,
            NodesGETResponse,
            PoolsGETResponse,
            StorageGETResponse,
            VersionGETResponse,
        )

        print("✓ Successfully imported all main models")
        return True
    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        return False


async def main():
    """Run all tests."""
    print("Testing prmxctrl package installation...")
    print("=" * 50)

    tests = [
        ("Basic import and client creation", test_basic_import),
        ("Model imports", test_models),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            if await test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")

    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Package is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
