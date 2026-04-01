Updated as of 1/3/26 to use PySide6 QtWidgets

Win 11 → Python → EXE Builder

If this tool was useful, consider starring the repo — feedback is appreciated.

Why this exists

This tool is designed around the full Windows EXE build workflow, not just invoking PyInstaller.

It provides a Windows GUI for:

Selecting and validating Python interpreters
Managing build inputs and outputs
Executing PyInstaller in a controlled, predictable way

It also includes shortcuts to Windows Installed Apps and direct links to Python.org, reducing context switching when configuring or repairing build environments.

Win 11 → Python → EXE Builder converts Python scripts and projects into standalone Windows executables by orchestrating interpreter selection, validation, build execution, and cleanup around PyInstaller.

Dependency Notice

Scans your project for imported modules and highlights external packages that may need to be installed.

Recursively scans all Python files in the project folder
Filters out standard library and local modules
Classifies results into:
✔ External — likely required packages
⚠ Maybe — common/internal names to verify
? Uncertain — ambiguous or optional imports
Displays results in a categorized, color-coded popup with legend
Runs asynchronously to avoid blocking the UI
Runs when the selected script changes (if enabled), with safeguards to prevent repeated scans

Limitations

May include false positives (e.g. indirect or optional imports)
Does not resolve exact package names or versions
Does not detect dynamic imports or runtime dependencies

This feature is a lightweight advisory to help catch missing packages before building, not a full dependency resolver.

Protected folders

Avoid building in protected folders (e.g. Pictures, Music). These locations may prevent file writes and cause build failures or stalled output.

Multiple builds

If you plan to build multiple versions of the same EXE:

Use a date/time format that includes minutes (HH-MM)
Builds created within the same minute will share the same name
If you need another build, wait for the next minute before rebuilding

This ensures each build generates a unique output folder and EXE.

Build requirements:

Windows 11
Python 3.11, 3.12, 3.13, or 3.14
PyInstaller installed in the selected interpreter

Not tested or supported on other operating systems.

The tool assumes a working Python environment and focuses on providing a safe, predictable build process, not full dependency resolution or repair.

Tested versions

At the time of testing:

Python 3.11, 3.12, 3.13, and 3.14 produced stable builds

Distribution

This repository contains source code only.

Users must run the application locally or build their own executable using the tool.

Local state & portability:

Each user’s settings are stored locally on their machine
No user configuration or state is embedded inside any executable binary
The _internal folder, JSON state files, and EXE must remain in the same directory
The application can be moved freely as long as this structure is preserved
No configuration or data is shared, uploaded, or transmitted

Pin to taskbar works
Copy shortcut works

Important limitations

This tool does not:

Determine whether third-party libraries are compatible with specific Python versions (e.g. 3.13 vs 3.14)
Fix broken or unsupported dependencies
Modify, downgrade, or patch Python packages
Automatically resolve PyInstaller-specific compatibility issues

Building and running from source

Install a recent Python version (3.11+)

Install PyInstaller:

py -3.14 -m pip install pyinstaller
Clone this repository
In the GUI, select the Python interpreter that has PyInstaller installed
Start the build
Build the EXE for the EXE Builder itself

Debug log path

The application writes its debug log to a predefined Desktop location during builds.

This path is used for diagnostics and troubleshooting.

Do not change the debug log path in the source code unless you fully understand the build workflow.

Altering this path can interfere with diagnostics and may cause builds to fail or behave unpredictably.

If you need logs stored elsewhere, modify the path only after confirming the application builds and runs correctly.
