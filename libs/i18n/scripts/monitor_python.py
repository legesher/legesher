#!/usr/bin/env python3
"""
Monitor Python releases for new versions.

Checks GitHub CPython repository for new major releases and compares
with currently supported versions in version-index.yml.

Exit codes:
    0: Success (may or may not have found new version)
    1: Error (network, parsing, file not found, etc.)

Output:
    - New version found: Prints "3.14" to stdout
    - No new version: Prints empty string to stdout
    - Errors: Prints to stderr
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import yaml
from packaging.version import Version, InvalidVersion


# GitHub API endpoint for CPython tags
# Note: CPython uses tags, not releases, so we query tags and filter for X.Y.0 versions
GITHUB_API_URL = "https://api.github.com/repos/python/cpython/tags"

# User agent for GitHub API
USER_AGENT = "Legesher-Python-Monitor/1.0"

# Timeout for HTTP requests (seconds) - configurable via environment variable
REQUEST_TIMEOUT = int(os.getenv("LEGESHER_GITHUB_TIMEOUT", "10"))

# Retry configuration for rate limiting
MAX_RETRIES = int(os.getenv("LEGESHER_GITHUB_MAX_RETRIES", "3"))
RETRY_DELAY = 2  # Initial delay in seconds

# Pattern for major releases (vX.Y.0 where X >= 3)
# Updated to support Python 10+ with pattern: ([3-9]|\d{2,})\.\d+
MAJOR_RELEASE_PATTERN = re.compile(r"^v?(([3-9]|\d{2,})\.\d+)\.0$")


def log_verbose(message: str, verbose: bool = False) -> None:
    """Print message to stderr if verbose mode is enabled."""
    if verbose:
        print(f"[INFO] {message}", file=sys.stderr)


def log_error(message: str) -> None:
    """Print error message to stderr."""
    print(f"[ERROR] {message}", file=sys.stderr)


def validate_version_string(version_str: str) -> bool:
    """
    Validate version string format.

    Args:
        version_str: Version string to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        Version(version_str)
        return True
    except InvalidVersion:
        return False


def get_latest_github_release_with_retry(
    verbose: bool = False, max_retries: int = MAX_RETRIES
) -> str | None:
    """
    Query GitHub API with retry logic for rate limiting.

    Args:
        verbose: Enable verbose logging
        max_retries: Maximum number of retry attempts

    Returns:
        Version string (e.g., "3.14.0") or None if error
    """
    for attempt in range(max_retries):
        try:
            return _fetch_github_releases(verbose)
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # Rate limit - retry with exponential backoff
                if attempt < max_retries - 1:
                    delay = RETRY_DELAY * (2**attempt)  # Exponential backoff
                    log_verbose(
                        f"Rate limited (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay}s...",
                        verbose,
                    )
                    time.sleep(delay)
                else:
                    log_error(
                        f"GitHub API rate limit exceeded after {max_retries} attempts"
                    )
                    return None
            else:
                log_error(f"GitHub API HTTP error: {e.code} - {e.reason}")
                return None

    return None


def _fetch_github_releases(verbose: bool = False) -> str | None:
    """
    Internal function to fetch releases from GitHub (no retry logic).

    Args:
        verbose: Enable verbose logging

    Returns:
        Version string or None if error
    """
    log_verbose(f"Querying GitHub API: {GITHUB_API_URL}", verbose)

    # Create request with User-Agent header
    request = urllib.request.Request(
        f"{GITHUB_API_URL}?per_page=50", headers={"User-Agent": USER_AGENT}
    )

    # Make the request
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        tags = json.loads(response.read().decode())

    if not isinstance(tags, list):
        log_error("Unexpected response format from GitHub API")
        return None

    log_verbose(f"Retrieved {len(tags)} tags from GitHub", verbose)

    # Find the latest major release (v3.X.0)
    latest_version = None
    latest_version_obj = None

    for tag in tags:
        tag_name = tag.get("name", "")

        # Check if it's a major release (v3.X.0)
        match = MAJOR_RELEASE_PATTERN.match(tag_name)
        if not match:
            continue

        # Extract version from capture group 1 (the full version number)
        version_str = match.group(1) + ".0"  # Add .0 back for validation

        # Validate version string
        if not validate_version_string(version_str):
            log_verbose(f"Skipping invalid version: {version_str}", verbose)
            continue

        try:
            version_obj = Version(version_str)

            # Track the latest version found
            if latest_version_obj is None or version_obj > latest_version_obj:
                latest_version = version_str
                latest_version_obj = version_obj
                log_verbose(f"Found major release: {version_str}", verbose)

        except InvalidVersion:
            log_verbose(f"Skipping invalid version: {version_str}", verbose)
            continue

    if latest_version is None:
        log_verbose("No major releases found in recent tags", verbose)
        return None

    log_verbose(f"Latest major release: {latest_version}", verbose)
    return latest_version


def get_latest_github_release(verbose: bool = False) -> str | None:
    """
    Query GitHub API for latest CPython release with retry logic.

    Args:
        verbose: Enable verbose logging

    Returns:
        Version string (e.g., "3.14.0") or None if error
    """
    try:
        return get_latest_github_release_with_retry(verbose)
    except urllib.error.URLError as e:
        log_error(f"Network error querying GitHub: {e.reason}")
        return None
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse GitHub API response: {e}")
        return None
    except Exception as e:
        log_error(f"Unexpected error querying GitHub: {e}")
        return None


def get_version_index_path() -> Path:
    """
    Get the path to version-index.yml.

    Returns:
        Path object pointing to version-index.yml
    """
    # Script is in libs/i18n/scripts/, version-index.yml is in libs/i18n/language-packs/python/
    script_dir = Path(__file__).parent
    version_index = (
        script_dir.parent / "language-packs" / "python" / "version-index.yml"
    )
    return version_index


def get_our_latest_version(verbose: bool = False) -> str | None:
    """
    Get latest version from version-index.yml.

    Args:
        verbose: Enable verbose logging

    Returns:
        Version string (e.g., "3.13") or None if error
    """
    try:
        version_index_path = get_version_index_path()
        log_verbose(f"Reading version index: {version_index_path}", verbose)

        if not version_index_path.exists():
            log_error(f"version-index.yml not found at {version_index_path}")
            return None

        # Read and parse YAML
        with open(version_index_path) as f:
            data = yaml.safe_load(f)

        # Get all Python versions
        python_versions = data.get("python_versions", {})
        if not python_versions:
            log_error("No python_versions found in version-index.yml")
            return None

        log_verbose(f"Found {len(python_versions)} versions in index", verbose)

        # Find the latest version (maximum version number)
        latest = None
        latest_version_obj = None

        for version_str in python_versions.keys():
            try:
                # Parse as packaging.version.Version for comparison
                version_obj = Version(version_str)

                if latest_version_obj is None or version_obj > latest_version_obj:
                    latest = version_str
                    latest_version_obj = version_obj

            except InvalidVersion:
                log_verbose(f"Skipping invalid version: {version_str}", verbose)
                continue

        if latest is None:
            log_error("No valid versions found in version-index.yml")
            return None

        log_verbose(f"Latest supported version: {latest}", verbose)
        return latest

    except FileNotFoundError:
        log_error("version-index.yml not found")
        return None

    except yaml.YAMLError as e:
        log_error(f"Failed to parse version-index.yml: {e}")
        return None

    except Exception as e:
        log_error(f"Unexpected error reading version index: {e}")
        return None


def is_new_major_version(latest: str, current: str, verbose: bool = False) -> bool:
    """
    Check if latest is a new major version compared to current.

    Args:
        latest: Latest version from GitHub (e.g., "3.14.0")
        current: Current version we support (e.g., "3.13")
        verbose: Enable verbose logging

    Returns:
        True if latest has higher major.minor version
    """
    try:
        # Parse both versions
        latest_version = Version(latest)
        current_version = Version(current)

        log_verbose(f"Comparing versions: {latest} vs {current}", verbose)

        # Compare major.minor only (ignore micro/patch)
        # Version objects can be compared directly
        is_newer = latest_version.major > current_version.major or (
            latest_version.major == current_version.major
            and latest_version.minor > current_version.minor
        )

        log_verbose(f"Is newer version: {is_newer}", verbose)
        return is_newer

    except InvalidVersion as e:
        log_error(f"Invalid version format: {e}")
        return False


def format_version_output(version_str: str) -> str:
    """
    Format version string for output (major.minor only).

    Args:
        version_str: Full version string (e.g., "3.14.0")

    Returns:
        Formatted version (e.g., "3.14")
    """
    try:
        version = Version(version_str)
        return f"{version.major}.{version.minor}"
    except InvalidVersion:
        # If parsing fails, try regex extraction
        match = re.match(r"^(\d+\.\d+)", version_str)
        if match:
            return match.group(1)
        return version_str


def main() -> int:
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Monitor Python releases for new versions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    Check for new version (quiet)
  %(prog)s --verbose          Check with detailed logging
  %(prog)s --show-current     Show currently supported version

Output:
  - Prints new version to stdout (e.g., "3.14")
  - Prints empty string if no new version
  - All logging/errors go to stderr
        """,
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging to stderr"
    )

    parser.add_argument(
        "--show-current",
        action="store_true",
        help="Show currently supported version and exit",
    )

    args = parser.parse_args()

    # Show current version if requested
    if args.show_current:
        current = get_our_latest_version(args.verbose)
        if current is None:
            return 1
        print(current)
        return 0

    # Get latest GitHub release
    log_verbose("Starting Python release monitoring", args.verbose)
    github_version = get_latest_github_release(args.verbose)

    if github_version is None:
        log_verbose("No new major release found on GitHub", args.verbose)
        print("")  # Empty string output
        return 0

    # Get our current version
    current_version = get_our_latest_version(args.verbose)

    if current_version is None:
        return 1

    # Compare versions
    if is_new_major_version(github_version, current_version, args.verbose):
        new_version = format_version_output(github_version)
        log_verbose(f"New Python version detected: {new_version}", args.verbose)
        print(new_version)
    else:
        log_verbose("GitHub version is not newer than current version", args.verbose)
        print("")  # Empty string output

    return 0


if __name__ == "__main__":
    sys.exit(main())
