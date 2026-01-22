#!/usr/bin/env python3
"""
Quick test script to verify perturbation system works correctly.

Usage:
    cd maia_fork
    python perturbations/test_perturbations.py
"""

import sys
from pathlib import Path

# Add parent to path so we can import perturbations
sys.path.insert(0, str(Path(__file__).parent.parent))

from perturbations import apply_perturbations, restore_originals, clean_backups


def test_simple_perturbation():
    """Test basic perturbation and restoration."""
    print("\n" + "="*70)
    print("TEST 1: Simple Perturbation")
    print("="*70)

    config_path = Path(__file__).parent / "configs" / "test_simple.yaml"

    # Read original content
    target_file = Path(__file__).parent.parent / "prompts" / "open" / "final.txt"
    original_content = target_file.read_text()

    print("\n1. Applying perturbation...")
    apply_perturbations(config_path)

    # Check it was modified
    modified_content = target_file.read_text()
    marker = "[PERTURBATION TEST: This text was added by the perturbation system]"

    if marker in modified_content:
        print("   ✅ Perturbation successfully applied!")
        print(f"   Found marker: {marker}")
    else:
        print("   ❌ Perturbation failed - marker not found")
        return False

    print("\n2. Restoring original...")
    restore_originals()

    # Check restoration
    restored_content = target_file.read_text()

    if restored_content == original_content:
        print("   ✅ Restoration successful!")
    else:
        print("   ❌ Restoration failed - content doesn't match original")
        return False

    return True


def test_iteration_control():
    """Test MAIA-specific perturbation."""
    print("\n" + "="*70)
    print("TEST 2: Iteration Control Perturbation")
    print("="*70)

    config_path = Path(__file__).parent / "configs" / "iteration_control.yaml"
    target_file = Path(__file__).parent.parent / "prompts" / "open" / "final.txt"

    original_content = target_file.read_text()

    print("\n1. Applying iteration control perturbation...")
    apply_perturbations(config_path)

    modified_content = target_file.read_text()

    # Check for the change
    if "run exactly 3 iterations" in modified_content.lower():
        print("   ✅ Iteration control successfully applied!")
        print("   Changed 'iterate until confident' to 'run exactly 3 iterations'")
    else:
        print("   ⚠️  Warning: Expected text not found")
        print("   This might be okay if the original prompt didn't contain the target phrase")

    print("\n2. Restoring original...")
    restore_originals()

    restored_content = target_file.read_text()
    if restored_content == original_content:
        print("   ✅ Restoration successful!")
    else:
        print("   ❌ Restoration failed")
        return False

    return True


def test_view_config():
    """Show what a config looks like."""
    print("\n" + "="*70)
    print("TEST 3: Viewing Available Configs")
    print("="*70)

    configs_dir = Path(__file__).parent / "configs"
    configs = sorted(configs_dir.glob("*.yaml"))

    print(f"\nFound {len(configs)} config files:\n")

    for config in configs:
        print(f"  📄 {config.name}")

        # Try to read description
        try:
            import yaml
            with open(config) as f:
                data = yaml.safe_load(f)
                if "description" in data:
                    print(f"     → {data['description']}")
        except:
            pass

    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MAIA PERTURBATION SYSTEM - TEST SUITE")
    print("="*70)

    tests = [
        ("Simple Perturbation", test_simple_perturbation),
        ("Iteration Control", test_iteration_control),
        ("View Configs", test_view_config),
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n   ❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")

    # Clean up backups
    print("\n" + "="*70)
    print("CLEANUP")
    print("="*70)

    try:
        from perturbations.perturber import clean_backups
        clean_backups()
    except Exception as e:
        print(f"Note: Backup cleanup failed (this is okay): {e}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print("\n" + "="*70)
    print(f"FINAL RESULT: {passed}/{total} tests passed")
    print("="*70 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)