#!/usr/bin/env python3
"""Sync version numbers across foundation packages (core, i18n, legesher)."""

import argparse
import re
import sys
from pathlib import Path


def get_root_version() -> str:
    """Get version from root pyproject.toml."""
    root_toml = Path("pyproject.toml")
    if not root_toml.exists():
        raise FileNotFoundError("Root pyproject.toml not found. Run from repository root.")

    content = root_toml.read_text()
    match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in root pyproject.toml")
    return match.group(1)


def get_current_version(file_path: Path) -> str | None:
    """Get current version from a file."""
    if not file_path.exists():
        return None

    content = file_path.read_text()

    if file_path.name == "pyproject.toml":
        match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    elif file_path.name == "__init__.py":
        match = re.search(r'^__version__ = "([^"]+)"', content, re.MULTILINE)
    else:
        return None

    return match.group(1) if match else None


def update_version_in_file(file_path: Path, version: str, dry_run: bool = False) -> bool:
    """Update version in a file. Returns True if file was modified."""
    if not file_path.exists():
        print(f"⚠️  Skipping {file_path} (not found)")
        return False

    content = file_path.read_text()
    original_content = content

    if file_path.name == "pyproject.toml":
        # Update version = "x.y.z"
        content = re.sub(
            r'^version = "[^"]+"',
            f'version = "{version}"',
            content,
            flags=re.MULTILINE
        )
    elif file_path.name == "__init__.py":
        # Update __version__ = "x.y.z"
        content = re.sub(
            r'^__version__ = "[^"]+"',
            f'__version__ = "{version}"',
            content,
            flags=re.MULTILINE
        )

    if content != original_content:
        if dry_run:
            current_version = get_current_version(file_path)
            print(f"🔍 Would update {file_path} from {current_version} to {version}")
        else:
            file_path.write_text(content)
            print(f"✅ Updated {file_path} to {version}")
        return True
    else:
        print(f"ℹ️  {file_path} already at {version}")
        return False


def check_versions() -> bool:
    """Check if all foundation packages are in sync. Returns True if synced."""
    try:
        root_version = get_root_version()
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}")
        return False

    print(f"📦 Root version: {root_version}")
    print("Checking foundation package versions...")

    foundation_packages = ["core", "i18n", "legesher"]
    all_synced = True
    mismatched = []

    for pkg in foundation_packages:
        # Check pyproject.toml
        toml_file = Path(f"libs/{pkg}/pyproject.toml")
        toml_version = get_current_version(toml_file)

        # Check __init__.py
        init_candidates = [
            Path(f"libs/{pkg}/legesher_{pkg}/__init__.py"),
            Path(f"libs/{pkg}/legesher/__init__.py"),
        ]

        init_version = None
        for init_file in init_candidates:
            if init_file.exists() and "__version__" in init_file.read_text():
                init_version = get_current_version(init_file)
                break

        if toml_version != root_version:
            print(f"❌ {toml_file}: {toml_version} (expected {root_version})")
            all_synced = False
            mismatched.append(f"{pkg}/pyproject.toml")
        else:
            print(f"✅ {toml_file}: {toml_version}")

        if init_version and init_version != root_version:
            print(f"❌ {pkg}/__init__.py: {init_version} (expected {root_version})")
            all_synced = False
            mismatched.append(f"{pkg}/__init__.py")
        elif init_version:
            print(f"✅ {pkg}/__init__.py: {init_version}")

    if all_synced:
        print(f"\n✅ All foundation packages are synced to {root_version}")
    else:
        print(f"\n❌ Version mismatch detected in: {', '.join(mismatched)}")
        print(f"   Run './scripts/sync-foundation-versions.py' to sync to {root_version}")

    return all_synced


def main():
    """Sync foundation package versions to root version."""
    parser = argparse.ArgumentParser(
        description="Sync version numbers across foundation packages (core, i18n, legesher)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if versions are in sync (useful in CI)"
    )

    args = parser.parse_args()

    # Check mode
    if args.check:
        synced = check_versions()
        sys.exit(0 if synced else 1)

    # Sync mode
    try:
        version = get_root_version()
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified\n")

    print(f"📦 Root version: {version}")
    print("Syncing foundation packages (core, i18n, legesher)...")

    foundation_packages = ["core", "i18n", "legesher"]
    modified = False

    for pkg in foundation_packages:
        # Update pyproject.toml
        toml_file = Path(f"libs/{pkg}/pyproject.toml")
        if update_version_in_file(toml_file, version, dry_run=args.dry_run):
            modified = True

        # Update __init__.py
        # Try both naming conventions
        init_candidates = [
            Path(f"libs/{pkg}/legesher_{pkg}/__init__.py"),
            Path(f"libs/{pkg}/legesher/__init__.py"),
        ]

        for init_file in init_candidates:
            if init_file.exists() and "__version__" in init_file.read_text():
                if update_version_in_file(init_file, version, dry_run=args.dry_run):
                    modified = True
                break

    if modified:
        if args.dry_run:
            print(f"\n🔍 Dry run complete. Run without --dry-run to apply changes.")
        else:
            print(f"\n🎉 Foundation packages synced to {version}")
            print("Don't forget to commit these changes!")
    else:
        print(f"\n✅ All foundation packages already at {version}")


if __name__ == "__main__":
    main()
