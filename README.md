**Win 11 → Python → EXE Builder**

"If this tool was useful, consider starring the repo, some feedback would be nice."

**Why this exists:**



This tool is designed around the entire Windows EXE build workflow, not just invoking PyInstaller.



**It provides a Windows GUI for:**



* Selecting and validating Python interpreters.
* Managing build inputs and outputs.
* Executing PyInstaller in a controlled, predictable way.
* It also includes shortcuts to Windows Installed Apps for managing Python installations and direct links to Python.org, reducing context switching when configuring or repairing build environments.
* Win 11 → Python → EXE Builder converts Python scripts and projects into standalone Windows executables by orchestrating interpreter selection, validation, build execution, and clean-up around PyInstaller.



**Build requirements:**



* Windows 11
* Python 3.11 3.12 3.13 or 3.14
* PyInstaller installed in the selected interpreter
* Not tested or supported on other operating systems



**The tool assumes a working Python environment and focuses on providing a safe, predictable build process, not dependency analysis or repair.**



**At the time of testing:**



**Python 3.11 3.12 3.13 and 3.14 produced stable builds**



**Distribution:**



* This repository contains source code only.



* Prebuilt executables are not distributed through this repository.

* Users must run the application from source using a local Python installation.



**Local state \& portability:**



* Each user’s settings are stored locally on their own machine.
* No user configuration or state is embedded inside any executable binary.
* Must have \_internal folder and any json state and the app EXE in the same folder, can then just move it all wherever you want.
* No configuration or data is shared, uploaded, or transmitted.
* Pin to taskbar works
* Copy shortcut works



**Important limitations:**



**This tool does not:**



* **Determine whether third-party libraries are compatible with specific Python versions (e.g. 3.13 vs 3.14)**
* **Fix broken or unsupported dependencies**
* **Modify, downgrade, or patch Python packages**
* **Automatically resolve PyInstaller-specific compatibility issues**



**Building and running from source:**



* **Install a recent python (haven't tested it on earier versions before 3.11)**
* **py -3.14 -m pip install pyinstaller**
* **Clone this repository**
* **In the GUI, select the Python interpreter that has PyInstaller installed, then start the build**
* **Build the EXE for the EXE builder itself**



**Debug log path**



**The application writes its debug log to a predefined Desktop location during builds.**



**This path is used for diagnostics and troubleshooting.**



**Do not change the debug log path in the source code unless you fully understand the build workflow.**

**Altering this path can interfere with diagnostics and may cause builds to fail or behave unpredictably.**



**If you need logs stored elsewhere, modify the path only after confirming the application builds and runs correctly.**



