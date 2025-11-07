# Installation Guide

Welcome to Legesher! This guide will help you install Legesher so you can start coding in your native language.

## Table of Contents

- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Installation Methods](#installation-methods)
  - [Method 1: Using uv (Recommended)](#method-1-using-uv-recommended)
  - [Method 2: Using pip](#method-2-using-pip)
  - [Method 3: Development Installation](#method-3-development-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## Prerequisites

Before installing Legesher, ensure you have the following:

- **Python 3.10 or newer** (up to Python 3.13)
- **Package Manager**: Either `uv` (recommended) or `pip`
- **Operating System**: macOS, Linux, or Windows

### Checking Your Python Version

Open your terminal or command prompt and run:

```bash
python --version
```

**Expected output:**

```text
Python 3.10.x (or 3.11.x, 3.12.x, 3.13.x)
```

**Note for Windows users:** You may need to use `python3` or `py` instead of `python`.

**Note for macOS/Linux users:** If you see Python 2.x, try `python3 --version` instead.

If you don't have Python 3.10+, download it from [python.org](https://www.python.org/downloads/).

## System Requirements

Legesher works on all major operating systems:

- **macOS**: 10.15 (Catalina) or newer
- **Linux**: Most modern distributions (Ubuntu 20.04+, Fedora 35+, etc.)
- **Windows**: Windows 10 or newer

**Minimum Hardware:**

- 2 GB RAM
- 500 MB available disk space
- Internet connection (for installation only)

## Installation Methods

### Method 1: Using uv (Recommended)

`uv` is a fast Python package manager that makes installation quick and reliable.

#### Step 1: Install uv

If you don't have `uv` installed, follow the installation instructions at
[docs.astral.sh/uv](https://docs.astral.sh/uv/).

**Quick install (macOS/Linux):**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Quick install (Windows):**

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Step 2: Install Legesher

Install the main Legesher package:

```bash
uv pip install legesher
```

**Expected output:**

```text
Resolved 5 packages in 1.2s
Installed 5 packages in 0.8s
 + legesher==0.1.0
 + legesher-core==0.1.0
 + legesher-i18n==0.1.0
 + ...
```

#### Step 3: Install Language Packs (Optional)

Install language packs for the languages you want to code in:

**For Spanish:**

```bash
uv pip install legesher-i18n-python-es
```

**For Arabic:**

```bash
uv pip install legesher-i18n-python-ar
```

**For all languages:**

```bash
uv pip install legesher[all]
```

### Method 2: Using pip

If you prefer using `pip`, follow these steps:

#### Step 1: Upgrade pip

Ensure you have the latest version of pip:

```bash
python -m pip install --upgrade pip
```

**Expected output:**

```text
Requirement already satisfied: pip in /usr/local/lib/python3.10/site-packages
Successfully installed pip-24.0
```

#### Step 2: Install Legesher

Install the main Legesher package:

```bash
pip install legesher
```

**Note for macOS/Linux users:** You may need to use `pip3` instead of `pip`.

**Note for permission errors:** Use `pip install --user legesher` to install for your user only.

#### Step 3: Install Language Packs (Optional)

Install language packs for the languages you want to code in:

**For Spanish:**

```bash
pip install legesher-i18n-python-es
```

**For Arabic:**

```bash
pip install legesher-i18n-python-ar
```

**For all languages:**

```bash
pip install legesher[all]
```

### Method 3: Development Installation

This method is for contributors who want to modify Legesher's source code.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/legesher/legesher.git
cd legesher
```

**Expected output:**

```text
Cloning into 'legesher'...
remote: Enumerating objects: 1234, done.
remote: Counting objects: 100% (1234/1234), done.
```

#### Step 2: Install Development Dependencies

**Using uv (recommended):**

```bash
uv pip install -e ".[dev]"
```

**Using pip:**

```bash
pip install -e ".[dev]"
```

The `-e` flag installs Legesher in "editable" mode, meaning changes you make to the source code
will immediately affect the installed package.

**Expected output:**

```text
Obtaining file:///path/to/legesher
Installing collected packages: legesher-core, legesher-i18n, legesher
  Running setup.py develop for legesher
Successfully installed legesher
```

#### Step 3: Install Pre-commit Hooks (Optional)

If you plan to contribute code, install pre-commit hooks:

```bash
pre-commit install
```

## Verification

After installation, verify that Legesher is installed correctly.

### Step 1: Check Installation

Run the following command:

```bash
legesher --version
```

**Expected output:**

```text
Legesher version 0.1.0
```

If you see this, congratulations! Legesher is installed successfully.

### Step 2: Check Available Languages

List the installed language packs:

```bash
legesher languages list
```

**Expected output:**

```text
Available languages:
  - Spanish (es) - Python 3.10-3.13
  - Arabic (ar) - Python 3.10-3.13
```

If you haven't installed any language packs, you'll see:

```text
No language packs installed. Install one with: pip install legesher-i18n-python-<language>
```

### Step 3: Run a Quick Test

Create a simple test file:

```bash
echo "imprimir('Hola mundo')" > test_es.py
legesher run test_es.py
```

**Expected output:**

```text
Hola mundo
```

If you see "Hola mundo" printed, everything is working correctly!

## Troubleshooting

### Issue: "command not found: legesher"

**Cause:** The installation directory is not in your system's PATH.

**Solution:**

1. Find where Legesher was installed:

   ```bash
   python -m pip show legesher
   ```

2. Add the installation directory to your PATH:

   **macOS/Linux (bash/zsh):**

   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

   **Windows:**

   Add `%USERPROFILE%\AppData\Local\Programs\Python\Python310\Scripts` to your PATH
   environment variable.

### Issue: "ModuleNotFoundError: No module named 'legesher'"

**Cause:** Legesher is not installed, or you're using the wrong Python interpreter.

**Solution:**

1. Verify which Python you're using:

   ```bash
   which python
   python --version
   ```

2. Reinstall Legesher with the correct Python:

   ```bash
   python3.10 -m pip install legesher
   ```

### Issue: "Permission denied" on macOS/Linux

**Cause:** You're trying to install system-wide without administrator privileges.

**Solution:**

Use the `--user` flag to install for your user only:

```bash
pip install --user legesher
```

### Issue: "This package is incompatible with Python X.X"

**Cause:** You're using a Python version that Legesher doesn't support.

**Solution:**

Upgrade to Python 3.10 or newer:

1. Download from [python.org](https://www.python.org/downloads/)
2. Install the new version
3. Use the new Python to install Legesher:

   ```bash
   python3.10 -m pip install legesher
   ```

### Issue: SSL Certificate Errors

**Cause:** Corporate firewall or outdated certificates.

**Solution:**

Use the `--trusted-host` flag (not recommended for security, use only if necessary):

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org legesher
```

Better solution: Update your certificates or contact your IT department.

### Issue: Installation is Very Slow

**Cause:** Slow internet connection or mirror issues.

**Solution:**

1. **For pip users:** Try using a different mirror:

   ```bash
   pip install --index-url https://pypi.org/simple legesher
   ```

2. **For uv users:** uv is already optimized, but ensure you have a stable connection.

### Issue: "No matching distribution found"

**Cause:** The package name is misspelled or the version doesn't exist.

**Solution:**

1. Check the spelling:

   ```bash
   pip install legesher  # correct
   pip install leghesher  # incorrect
   ```

2. Check available versions:

   ```bash
   pip index versions legesher
   ```

### Still Having Issues?

If you're still experiencing problems:

1. Check our [GitHub Issues](https://github.com/legesher/legesher/issues) for known problems
2. Search our [Discussions](https://github.com/legesher/legesher/discussions) for solutions
3. Create a new issue with:
   - Your operating system and version
   - Python version (`python --version`)
   - Full error message
   - Steps you've already tried

## Next Steps

Now that Legesher is installed, you're ready to start coding in your native language!

- **Get Started:** Read the [Getting Started Guide](getting-started.md) to write your first
  program
- **Learn More:** Explore the [User Guide](../user-guide.md) for in-depth features
- **Contribute:** Check the [Contributing Guide](../../CONTRIBUTING.md) to help improve Legesher
- **Join the Community:** Visit [legesher.io/community](https://legesher.io/community) to connect
  with other users

Welcome to the Legesher community! We're excited to have you here.
