"""
Core perturbation logic for applying and managing prompt modifications.
"""

import json
import re
import shutil
from pathlib import Path
from typing import Any

import yaml

from .strategies import STRATEGIES


# ============================================================================
# BACKUP MANAGEMENT
# ============================================================================

class BackupManager:
    """Manages backup and restoration of perturbed files."""

    def __init__(self, backup_dir: Path = None):
        if backup_dir is None:
            # Default to .perturbation_backups in maia_fork root
            backup_dir = Path(__file__).parent.parent / ".perturbation_backups"

        self.backup_dir = backup_dir
        self.backup_dir.mkdir(exist_ok=True)
        self.manifest_file = self.backup_dir / "manifest.json"
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> dict:
        """Load backup manifest."""
        if self.manifest_file.exists():
            return json.loads(self.manifest_file.read_text())
        return {"backups": {}}

    def _save_manifest(self):
        """Save backup manifest."""
        self.manifest_file.write_text(
            json.dumps(self.manifest, indent=2)
        )

    def backup_file(self, file_path: Path) -> Path:
        """Create backup of file if not already backed up."""
        file_str = str(file_path.resolve())

        if file_str in self.manifest["backups"]:
            backup_path = Path(self.manifest["backups"][file_str])
            print(f"  ℹ️  Already backed up: {file_path.name}")
            return backup_path

        # Create new backup
        backup_name = f"{file_path.name}.{abs(hash(file_str)) % 10000}.bak"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(file_path, backup_path)

        self.manifest["backups"][file_str] = str(backup_path)
        self._save_manifest()

        print(f"  ✓ Backed up: {file_path.name} -> {backup_path.name}")
        return backup_path

    def restore_all(self) -> int:
        """Restore all backed up files."""
        count = 0
        for original, backup in self.manifest["backups"].items():
            original_path = Path(original)
            backup_path = Path(backup)

            if backup_path.exists():
                shutil.copy2(backup_path, original_path)
                print(f"  ✓ Restored: {original_path}")
                count += 1
            else:
                print(f"  ⚠️  Backup not found: {backup_path}")

        return count

    def clean_backups(self):
        """Remove all backups and manifest."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
            print(f"  ✓ Cleaned backup directory: {self.backup_dir}")


# ============================================================================
# PERTURBATION APPLICATION
# ============================================================================

def apply_single_perturbation(
    perturb: dict[str, Any],
    base_dir: Path,
    backup_mgr: BackupManager
) -> bool:
    """
    Apply a single perturbation to a file.

    Returns True if file was modified, False otherwise.
    """
    file_path = base_dir / perturb["file"]

    if not file_path.exists():
        print(f"  ✗ File not found: {file_path}")
        return False

    # Backup before modifying
    backup_mgr.backup_file(file_path)

    # Read original content
    text = file_path.read_text(encoding="utf-8")
    original = text

    # Apply perturbation based on type
    perturb_type = perturb.get("type", "exact")

    if perturb_type == "exact":
        # Simple exact string replacement
        find = perturb.get("find", "")
        replace = perturb.get("replace", "")
        text = text.replace(find, replace)

    elif perturb_type == "regex":
        # Regex-based replacement
        pattern = perturb.get("pattern", "")
        strategy = perturb.get("strategy")

        if strategy:
            # Apply strategy to each match
            if strategy not in STRATEGIES:
                print(f"  ✗ Unknown strategy: {strategy}")
                return False

            fn = STRATEGIES[strategy]

            def repl(m):
                return fn(m.group(0), **perturb)

            text = re.sub(pattern, repl, text)
        else:
            # Simple regex replacement
            replace = perturb.get("replace", "")
            text = re.sub(pattern, replace, text)

    elif perturb_type == "full":
        # Apply strategy to entire file
        strategy = perturb.get("strategy")
        if strategy not in STRATEGIES:
            print(f"  ✗ Unknown strategy: {strategy}")
            return False

        fn = STRATEGIES[strategy]
        text = fn(text, **perturb)

    else:
        print(f"  ✗ Unknown perturbation type: {perturb_type}")
        return False

    # Write if changed
    if text != original:
        file_path.write_text(text, encoding="utf-8")
        print(f"  ✅ Modified: {file_path}")
        return True
    else:
        print(f"  ℹ️  No changes: {file_path}")
        return False


def load_config(config_path: Path) -> dict[str, Any]:
    """Load perturbation config from JSON or YAML."""
    text = config_path.read_text(encoding="utf-8")

    if config_path.suffix in [".yaml", ".yml"]:
        return yaml.safe_load(text)
    else:
        return json.loads(text)


# ============================================================================
# PUBLIC API
# ============================================================================

def apply_perturbations(config_path: str | Path, base_dir: Path = None) -> int:
    """
    Apply perturbations from a config file.

    Args:
        config_path: Path to perturbation config (JSON or YAML)
        base_dir: Base directory for relative file paths (default: maia_fork root)

    Returns:
        Number of files successfully modified
    """
    config_path = Path(config_path)

    if base_dir is None:
        # Default to maia_fork root (parent of perturbations/)
        base_dir = Path(__file__).parent.parent

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    print(f"\n🔧 Loading perturbation config: {config_path.name}\n")
    config = load_config(config_path)

    perturbations = config.get("perturbations", [])

    if not perturbations:
        print("⚠️  No perturbations defined in config")
        return 0

    print(f"Found {len(perturbations)} perturbation(s) to apply\n")

    # Show description if present
    if "description" in config:
        print(f"Description: {config['description']}\n")

    backup_mgr = BackupManager()
    modified = 0

    for i, perturb in enumerate(perturbations, 1):
        file_name = perturb.get("file", "?")
        desc = perturb.get("description", "")

        print(f"[{i}/{len(perturbations)}] {file_name}")
        if desc:
            print(f"  → {desc}")

        if apply_single_perturbation(perturb, base_dir, backup_mgr):
            modified += 1

        print()  # Blank line between perturbations

    print(f"✓ Successfully modified {modified}/{len(perturbations)} file(s)\n")
    return modified


def restore_originals() -> int:
    """
    Restore all backed up files to their original state.

    Returns:
        Number of files restored
    """
    print("\n♻️  Restoring original files...\n")

    backup_mgr = BackupManager()
    count = backup_mgr.restore_all()

    print(f"\n✓ Restored {count} file(s)")
    print(f"ℹ️  Backups are still preserved in {backup_mgr.backup_dir}")
    print(f"   Run clean_backups() to remove them\n")

    return count


def clean_backups():
    """Remove all backup files and manifest."""
    print("\n🧹 Cleaning backup files...\n")

    backup_mgr = BackupManager()
    backup_mgr.clean_backups()

    print("\n✓ All backups removed\n")