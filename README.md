**Updated as of 6/4/26 to use PySide6 QtWidgets**

# Win 11 → Python → EXE Builder
	
	If this tool saved you time or simplified your workflow, consider giving the repo a ⭐.
	
	There’s also a sponsor option available if you’d like to support continued development.

---

## Overview

	Win 11 → Python → EXE Builder is a Windows GUI tool for converting Python scripts and projects into standalone executables using PyInstaller.
	
	It handles interpreter selection, input validation, and build execution in a controlled workflow, reducing friction and avoiding common build issues.

---

## Core Features

	* Select and validate Python interpreters
	* Manage build inputs and output locations
	* Execute PyInstaller in a predictable, controlled way
	* Quick access to Windows Installed Apps
	* Direct links to Python.org for environment setup

---

## Dependency Notice

	Scans your project for imported modules and highlights external packages that may need to be installed.

**How it works:**

	* Recursively scans all Python files in the project folder
	* Filters out standard library and local modules
	* Classifies results into:
	
	  * ✔ External — likely required packages
	  * ⚠ Maybe — common/internal names to verify
	  * ? Uncertain — ambiguous or optional imports

**Behavior:**

	* Displays results in a categorized, color-coded popup
	* Runs asynchronously (does not block UI)
	* Triggers when the selected script changes (if enabled)
	* Includes safeguards to prevent repeated scans

**Limitations:**

	* May include false positives
	* Does not resolve exact package names or versions
	* Does not detect dynamic imports or runtime dependencies

	This is a lightweight advisory tool, not a full dependency resolver.

---

## Protected Folders

	Avoid building in protected folders (e.g. Pictures, Music).
	These locations may block file writes and cause build failures or stalled output.

---

## Icon Behavior (Important)

	Windows aggressively caches application icons.
	
	If you rebuild an EXE with the same filename:
	
	* The EXE updates correctly
	* The embedded icon updates correctly
	* Windows may still display the old icon

	This is a Windows Explorer caching behavior, not a bug in the builder or PyInstaller.

**Recommended solution:**

	Use a unique filename for each build.

Built-in options:

	* Append Date/Time (HH-MM) ✅ recommended
	* Append Python Version (optional)

**Practical rule:**
	
	* Same filename → possible stale icon
	* Unique filename → always correct icon

---

## Multiple Builds

	Builds created within the same minute will share the same filename and be overwritten.
	
	If you need a distinct build, wait until the next minute or adjust naming settings.

---

## Requirements

	* Windows 11
	* Python 3.11, 3.12, 3.13, or 3.14
	* PyInstaller installed in the selected interpreter
	
	Tested on Python 3.11–3.14.

---

## Limitations

This tool does not:
	
	* Determine compatibility of libraries with specific Python versions
	* Fix broken or unsupported dependencies
	* Modify, downgrade, or patch Python packages
	* Automatically resolve PyInstaller-specific issues
	
	It assumes a working Python environment and focuses on providing a safe, predictable build process.

---

## Distribution

	* This repository contains source code only
	* Users must run locally or build their own executable

---

## Local State & Portability
	
	* All settings are stored locally on the user’s machine
	* No data is embedded inside generated executables
	* No data is uploaded or transmitted

To keep the app working:

* `_internal` folder, and EXE must remain together
* The json state files now is resolve to /Appdata/Local

The application can be moved freely as long as this structure is preserved.

---

	## Building and Running from Source

	1. Install Python 3.11+
	2. Install PyInstaller:

   ```
   py -3.14 -m pip install pyinstaller
   ```
	3. Clone the repository
	4. Select the Python interpreter with PyInstaller installed
	5. Start the build

---

## Debug Log Path

	The application writes debug logs to a predefined Desktop location during builds.

	* Used for diagnostics and troubleshooting
	* Do not change this path unless you fully understand the build workflow

	Changing the log path incorrectly may interfere with diagnostics or cause unexpected behavior.
	
	Modify only after confirming the application builds and runs correctly.

---

