Win 11 → Python → EXE Builder



**Why build this ?**



The tool is designed around the full build workflow, not just running PyInstaller.

It includes shortcuts to Windows Installed Apps for managing Python installations and direct links to Python.org, reducing context switching when setting up or fixing build environments.



Win 11 → Python → EXE Builder is a Windows GUI that converts Python scripts and projects into standalone Windows executables by managing interpreter selection, validation, build execution, and clean-up around PyInstaller.



**Build Requirements**



* Python 3.13 or 3.14
* PyInstaller installed in the selected interpreter
* Windows 11
* Not tested or supported on other operating systems



**Distribution**



This repository contains both:



* the full source code
* This repository contains the full source code and a prebuilt executable for users who prefer not to build from source.



**Local state \& portability**



* Each user’s settings are stored locally on their own machine.
* No configuration or state is shared or bundled with the EXE.
* The application stores its JSON state file alongside the executable.
* This application is distributed as a one-folder build.
* Do not move individual files. Move the entire folder to preserve functionality.
* Settings are stored locally alongside the executable, allowing the application folder to be moved without losing configuration.
* A shortcut of the exe can be put on desktop or it pinned to taskbar.



**Important limitations**



This tool does not:



* Determine whether third-party libraries are compatible with specific Python versions (e.g. 3.13 vs 3.14)
* Fix broken or unsupported dependencies.
* Modify, downgrade, or patch Python packages.
* Automatically resolve PyInstaller-specific compatibility issues.



The tool assumes a working Python environment and focuses on providing a safe, predictable build process, not dependency analysis or repair.



At the time of testing, Python 3.13 and 3.14 produced stable builds.

Python 3.11–3.12 are not supported due to PyInstaller/runtime incompatibilities observed during testing.



**Building from source**



* Install Python 3.13 or 3.14.
* Install PyInstaller into the interpreter you intend to use for the build:
* py -3.13 -m pip install pyinstaller.
* Run main.py.
* In the GUI, select the Python interpreter that has PyInstaller installed, then start the build.



**Debug Log Path (Do Not Modify)**



**The application writes its debug log to a predefined location(Desktop) used during the build and troubleshooting process.**



**Do not change the debug log path in the source code unless you fully understand the build workflow.**

**Altering this path can interfere with diagnostics and may cause builds to fail or behave unpredictably.**



**If you need logs stored elsewhere, modify the path only after confirming the application builds and runs correctly.**







