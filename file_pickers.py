import os
import subprocess
import os
from tkinter import filedialog
import customtkinter as ctk


# -------------------------------------------------------------
# File Pickers
# -------------------------------------------------------------

# This controller mediates file-based user input and applies guarded state changes to the app.

class FilePickerController:
    def __init__(self, app):
        """
        app = EXEBuilderApp instance
        """
        self.app = app
        
    def _derive_exe_name_from_script(script_path):
        return os.path.splitext(os.path.basename(script_path))[0]

    # ============================================================
    # This is the open install apps opener the ui logic actually lives in main
    # ============================================================

    def open_installed_apps(self):
        """Open Windows Installed Apps (Programs and Features)."""
        try:
            # Pause always-on-top while system window is open
            self.app.attributes("-topmost", False)

            subprocess.Popen(["appwiz.cpl"], shell=True)

        except Exception as e:
            print("Failed to open Installed Apps:", e)

    # ============================================================
    # Script selection
    # ============================================================
    
    # ============================================================
    # This invokes cmd to find where python and hands it off to select python interpreter
    # ============================================================
    
    def _get_where_python_dirs(self):
        """Return a list of python.exe paths from `where python` (silent)."""
        try:
            result = subprocess.run(
                ["where", "python"],
                capture_output=True,
                text=True,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )

            paths = [
                line.strip()
                for line in result.stdout.splitlines()
                if line.lower().endswith("python.exe")
            ]

            return paths
        except Exception:
            return []
    
    # ============================================================
    # This selects the actual python interpreter
    # ============================================================

    def select_python_interpreter(self):
        start_dir = self._resolve_python_start_dir()

        path = filedialog.askopenfilename(
            title="Select Python Interpreter",
            initialdir=start_dir,
            filetypes=[("Python Interpreter", "python.exe")]
        )

        if not path:
            return

        # Store on app (runtime)
        self.app.python_interpreter_path = path
        self.app.python_path_var.set(path)
        
        # Save last-used directory for next time
        self.app.last_python_dir = os.path.dirname(path)

        # Persist
        self.app.state_ctrl.save_state()  
        
        self.app.validator.update_build_button_state()
        
        
    # ============================================================
    # This is the state handling part of this trio that is invoked on python changing?
    # ============================================================

    def _resolve_python_start_dir(self):
        """Best directory to open the interpreter picker in."""

        # 1️⃣ Last-used interpreter directory (preferred)
        last_dir = getattr(self.app, "last_python_dir", "")
        if last_dir and os.path.isdir(last_dir):
            return last_dir

        # 2️⃣ Use `where python` as a hint
        candidates = self._get_where_python_dirs()
        for path in candidates:
            if "WindowsApps" not in path:
                return os.path.dirname(path)

        return None
    
    #========================================================================================================================================
    #========= This just opens the python file navigation after picking the folder, the Ui itself lives in main unless its multi file then it lives in script_picker
    #========================================================================================================================================
    
    def select_script(self):
        path = filedialog.askopenfilename(
            filetypes=[("Python Files", "*.py")]
        )
        if path:
            self.app.entry_script = path
            self.app.project_root = os.path.dirname(path)
            self.app.script_path_var.set(path)
            self.app.state_ctrl.save_state()
    
    #========================================================================================================================================
    #========= This just opens the python folder navigation, the Ui itself lives in main unless its multi file then it lives in script_picker
    #========================================================================================================================================

    def select_script_folder(self):

        start_dir = None

        # 1️⃣ Existing project root (best case)
        if self.app.project_root and os.path.isdir(self.app.project_root):
            start_dir = self.app.project_root

        # 2️⃣ Last selected script path
        elif self.app.script_path_var.get():
            script = self.app.script_path_var.get()
            if os.path.isfile(script):
                start_dir = os.path.dirname(script)

        # 3️⃣ Fallback: Desktop
        if not start_dir:
            start_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        folder = filedialog.askdirectory(initialdir=start_dir)
        if not folder:
            return

        py_files = [
            f for f in os.listdir(folder)
            if f.endswith(".py") and os.path.isfile(os.path.join(folder, f))
        ]

        if not py_files:
            return

        # Single-file shortcut
        if len(py_files) == 1:
            full_path = os.path.join(folder, py_files[0])
            self._apply_selected_entry(full_path)
            return

        # Multi-file → popup
        ScriptPickerPopup(
            parent=self.app,
            folder_path=folder,
            py_files=py_files,
            callback=self._apply_selected_entry
        )
        
    #========================================================================================================================================
    #========= This just applies selected entry to state (if there was one for a multi file build) the actual ui logic lives in script picker
    #========================================================================================================================================
    
    def _apply_selected_entry(self, full_path):
        """Callback from ScriptPickerPopup"""

        # ------------------------------------
        # Capture previous state BEFORE change
        # ------------------------------------
        
        previous_script = self.app.entry_script
        previous_exe_name = self.app.exe_name_var.get().strip()

        # ------------------------------------
        # Apply new script selection
        # ------------------------------------
        
        self.app.entry_script = full_path
        self.app.project_root = os.path.dirname(full_path)
        self.app.script_path_var.set(full_path)

        # ------------------------------------
        # Auto-update EXE name ONLY if safe
        # ------------------------------------
        
        old_derived = ""
        if previous_script:
            old_derived = os.path.splitext(os.path.basename(previous_script))[0]

        new_derived = os.path.splitext(os.path.basename(full_path))[0]

        # Only update if:
        # - EXE name was empty
        # - OR EXE name still equals the old derived name
        if not previous_exe_name or previous_exe_name in {
            old_derived,
            os.path.splitext(os.path.basename(full_path))[0]
        }:
            self.app.exe_name_var.set(new_derived)

        # ------------------------------------
        # Persist + revalidate
        # ------------------------------------
        
        self.app.state_ctrl.save_state()
        self.app.validator.update_build_button_state()

    # ======================================================================================
    # This just opens the select icon navigation its not thebutton itself that lives in main
    # =======================================================================================

    def select_icon(self):
        path = filedialog.askopenfilename(
            filetypes=[("ICON Files", "*.ico")]
        )
        if path:
            self.app.icon_path_var.set(path)
            self.app.state_ctrl.save_state()

    # ==================================================================================================
    # This just opens file navigation for the output folder its not the button itself that lives in main
    #===================================================================================================
    
    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.app.output_path_var.set(folder)

        # Auto-derive exe name ONLY if empty
        if not self.app.exe_name_var.get():
            script = self.app.entry_script or self.app.script_path_var.get()
            if script:
                base = os.path.splitext(os.path.basename(script))[0]
                self.app.exe_name_var.set(base)

        self.app.state_ctrl.save_state()
        self.app.validator.update_build_button_state()

# -------------------------------------------------------------
#  Popup: Choose Entry Script When Selecting a Folder
# -------------------------------------------------------------

class ScriptPickerPopup(ctk.CTkToplevel):
    def __init__(self, parent, folder_path, py_files, callback):
        super().__init__(parent)
        
        self.title("Select Entry Script")
        self.geometry("325x125")
        self.resizable(False, False)
        
        # -------------------------------------------------------------
        #  Alignment: snap popup to the right side of main GUI
        # -------------------------------------------------------------
        
        self.update_idletasks()

        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()

        popup_w = self.winfo_width()

        # Align vertically with the parent
        y = parent_y    # slight downward offset so it looks nice

        # Snap to the right-hand side of the main window
        x = parent_x + parent_w 

        self.geometry(f"{popup_w}x200+{x}+{y}")

        self.folder_path = folder_path
        self.callback = callback

        label = ctk.CTkLabel(
            self,
            text="Select the script that starts your program:",
            font=("Rubik UI", 15, "bold"),
            wraplength=300
        )
        label.pack(pady=(15, 10))

        # Dropdown containing all .py files
        self.choice_var = ctk.StringVar(value=py_files[0])

        dropdown = ctk.CTkOptionMenu(
            self,
            values=py_files,
            variable=self.choice_var,
            width=260,
            font=("Rubik UI", 14)
        )
        dropdown.pack(pady=10)

        confirm_btn = ctk.CTkButton(
            self,
            text="Confirm",
            command=self.confirm,
            width=160,
            font=("Rubik UI", 15, "bold")
        )
        confirm_btn.pack(pady=15)

    def confirm(self):
        selected_file = self.choice_var.get()
        full_path = os.path.join(self.folder_path, selected_file)

        # Return the chosen file to the EXEBuilderApp
        self.callback(full_path)

        self.destroy()
