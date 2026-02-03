import customtkinter as ctk
import webbrowser
import sys, os
import ctypes
import threading
from validation_controller import ValidationController
from activation_controller import ActivationController
from file_pickers import FilePickerController
from ctypes import wintypes
from state_controller import StateController

CREATE_NO_WINDOW = 0x08000000

# Try to create a mutex
mutex = ctypes.windll.kernel32.CreateMutexW(None, wintypes.BOOL(True), "EXEBUILDER_MUTEX")

# ERROR_ALREADY_EXISTS means another instance is running
if ctypes.GetLastError() == 183:
    # Try to open the activation event in the running app
    event = ctypes.windll.kernel32.OpenEventW(
        0x00100002,   # EVENT_MODIFY_STATEP
        False,
        "EXEBUILDER_ACTIVATE_EVENT"
    )

    # If the event exists, signal it
    if event:
        ctypes.windll.kernel32.SetEvent(event)

    # Exit this second instance
    sys.exit(0)

def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# -------------------------------------------------------------
#  EXE Builder App
# -------------------------------------------------------------

class EXEBuilderApp(ctk.CTk):
    def __init__(self):
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        super().__init__()
        self.state_ctrl = StateController(self)

        self.entry_script = None
        self.project_root = None
        self.exe_name_user_modified = False
        self.python_interpreter_path = ""
        self.last_python_dir = ""
        self.validator = ValidationController(self)
        self.activation_controller = ActivationController(self)
        self.file_pickers = FilePickerController(self)


        # 🔒 A build cannot survive a restart
        self.building = False

        # ---------------------------------------------------------
        # SINGLE INSTANCE: Listen for activation events
        # ---------------------------------------------------------


        self.activate_event = ctypes.windll.kernel32.CreateEventW(
            None, False, False, "EXEBUILDER_ACTIVATE_EVENT"
        )

        threading.Thread(
            target=self.activation_controller.listen_for_activation,
            daemon=True
        ).start()
        
        # ---------------------------------------------------------
        # ALWAYS ON TOP
        # ---------------------------------------------------------
        
        self.attributes("-topmost", True)
        self.building = False
        self.build_process = None
        self.current_build_paths = []
        self.build_btn = None
        self.last_build_seconds = 45
        self.build_counter = 0

        self.title("")
        self.geometry("480x600")
        self.resizable(False, False)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.bind("<FocusIn>", self._restore_topmost)

        # --------------------
        # VARIABLES
        # --------------------
        
        self.tooltips_enabled = True
        self.script_path_var = ctk.StringVar()
        self.icon_path_var = ctk.StringVar()
        self.output_path_var = ctk.StringVar()
        self.python_path_var = ctk.StringVar()
        self.exe_name_var = ctk.StringVar()
        
        self._loading_state = True
        self.script_user_cleared = False
        self.python_user_cleared = False
        self.icon_user_cleared = False
        self.output_user_cleared = False
        self.exe_name_user_cleared = False


        # =============================================================
        # EXE name ownership tracking (USER intent only)
        # =============================================================

        def _on_exe_name_user_edit(*_):
            if self._loading_state:
                return
            self.exe_name_user_modified = True

        self.exe_name_var.trace_add("write", _on_exe_name_user_edit)
        
        # =============================================================
        # EXE name cleared by USER
        # =============================================================

        def on_exe_name_change(*_):
            if self._loading_state:
                return

            value = self.exe_name_var.get().strip()
            if not value:
                self.exe_name_user_cleared = True
                self.state_ctrl.save_state()

        self.exe_name_var.trace_add("write", on_exe_name_change)

        def on_script_path_change(*_):
            value = self.script_path_var.get().strip()

            if self._loading_state:
                return

            if not value:
                self.entry_script = None
                self.project_root = None
                self.script_user_cleared = True
                self.state_ctrl.save_state()

            self.validator.update_build_button_state()

        self.script_path_var.trace_add("write", on_script_path_change)

        self.output_path_var.trace_add(
            "write",
            lambda *_: (
                None if self._loading_state
                else self.validator.update_build_button_state()
            )
        )

        self.exe_name_var.trace_add(
            "write",
            lambda *_: (
                None if self._loading_state
                else self.validator.update_build_button_state()
            )
        )

        self.icon_path_var.trace_add(
            "write",
            lambda *_: (
                None if self._loading_state
                else self.validator.update_build_button_state()
            )
        )

        # =============================================================
        # Title + Tooltip Toggle (Switch)
        # =============================================================

        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(pady=10, padx=20, fill="x")

        # Toggle variable
        self.tooltips_var = ctk.BooleanVar(value=True)

        def on_tooltips_toggle():
            self.tooltips_enabled = self.tooltips_var.get()
            self.state_ctrl.save_state()

        self.tooltips_switch = ctk.CTkSwitch(
            title_row,
            text="Tooltips",
            variable=self.tooltips_var,
            command=on_tooltips_toggle,
            font=("Rubik UI", 15, "bold")
        )
        self.tooltips_switch.pack(side="left")

        title_label = ctk.CTkLabel(
            title_row,
            text=" Win 11 → Python → EXE Builder",
            font=("Rubik UI", 20, "bold")
        )
        title_label.pack(side="left", padx=(12, 0))

        # =============================================================
        # Script Picker Section
        # =============================================================
        # =============================================================
        # Icon Picker
        # =============================================================

        def open_python_site():
            urls = [
                "www.python.org"]
            for url in urls:
                webbrowser.open(url)

        # ---------------------------------
        # Left-side vertical button stack
        # ---------------------------------
        
        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(pady=5, padx=20, fill="x")

        btn_stack = ctk.CTkFrame(row2, fg_color="transparent")
        btn_stack.pack(anchor="w")
        
        apps_row = ctk.CTkFrame(btn_stack, fg_color="transparent")
        apps_row.pack(anchor="w", pady=(0, 5))

        self.apps_btn = ctk.CTkButton(
            apps_row,
            text="Open Installed Apps",
            command=self.file_pickers.open_installed_apps,
            width=160,
            font=("Rubik UI", 15, "bold")
        )
        self.apps_btn.pack(side="left")

        self.open_python_site_btn = ctk.CTkButton(
            apps_row,
            text="Python.org",
            command=open_python_site,
            fg_color="#0B62A8",
            hover_color="#0B62A8",
            font=("Rubik UI", 15, "bold"),
            width=120
        )
        self.open_python_site_btn.pack(side="left", padx=(10, 0))


        # ---------------------------------
        # Python Interpreter (INLINE ROW)
        # ---------------------------------

        interpreter_row = ctk.CTkFrame(btn_stack, fg_color="transparent")
        interpreter_row.pack(anchor="w", pady=(0, 10), fill="x")

        self.interpreter_btn = ctk.CTkButton(
            interpreter_row,
            text="Select Python Interpreter",
            command=self.file_pickers.select_python_interpreter,
            width=160,
            font=("Rubik UI", 15, "bold")
        )
        self.interpreter_btn.pack(side="left", pady = (5,2))

        self.python_status_label = ctk.CTkLabel(
            interpreter_row,
            text="PYTHON INTERPRETER NOT SET",
            font=("Rubik UI", 15),
            text_color="#be1a1a"
        )
        self.python_status_label.pack(side="left", padx=(8, 0))

        self.python_entry = ctk.CTkEntry(
            btn_stack,
            textvariable=self.python_path_var,
            width=360,
            state="readonly",
            placeholder_text="No Python interpreter selected..."
        )
        self.python_entry.pack(anchor="w", pady=(0, 5))

        # ---------------------------------
        # Python Folder (STACKED, TIGHT)
        # ---------------------------------

        python_block = ctk.CTkFrame(btn_stack, fg_color="transparent")
        python_block.pack(anchor="w", pady=(0, 5), fill="x")

        # -------- Row 1: button + status --------
        folder_row = ctk.CTkFrame(python_block, fg_color="transparent")
        folder_row.pack(anchor="w", pady=(0, 5), fill="x")

        self.folder_btn = ctk.CTkButton(
            folder_row,
            text="Select Python Folder",
            command=self.file_pickers.select_script_folder,
            width=160,
            font=("Rubik UI", 15, "bold")
        )
        self.folder_btn.pack(side="left", pady = 5)   # ❌ no pady here

        self.script_folder_status_label = ctk.CTkLabel(
            folder_row,
            text="PYTHON FOLDER NOT SET",
            font=("Rubik UI", 15),
            text_color="#be1a1a"
        )
        self.script_folder_status_label.pack(side="left", padx=(8, 0))

        # -------- Row 2: entry + clear --------
        script_row = ctk.CTkFrame(python_block, fg_color="transparent")
        script_row.pack(anchor="w", pady=(0, 0), fill="x")

        self.script_entry = ctk.CTkEntry(
            script_row,
            textvariable=self.script_path_var,
            width=360,
            placeholder_text="Select script or folder..."
        )
        self.script_entry.pack(side="left")
        
        def clear_script_path():
            # Clear exactly like icon clear behavior
            self.script_path_var.set("")
            self.script_user_cleared = True
            self.entry_script = None
            self.project_root = None
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()


        self.script_clear_btn = ctk.CTkButton(
            script_row,
            text="↺",
            width=36,
            height=32,
            fg_color="#444444",
            hover_color="#555555",
            command=clear_script_path
        )
        self.script_clear_btn.pack(side="left", padx=(8, 0))

        # =============================================================
        # Icon Picker
        # =============================================================

        def open_icon_sites():
            urls = [
                "https://convertico.com/",
                "https://cloudconvert.com/png-to-ico",
                "https://www.icoconverter.com/"
            ]
            for url in urls:
                webbrowser.open(url)

        icon_block = ctk.CTkFrame(self, fg_color="transparent")
        icon_block.pack(anchor="w", pady=(0, 6), padx=20, fill="x")

        # -------- Row 1: buttons --------
        icon_btn_row = ctk.CTkFrame(icon_block, fg_color="transparent")
        icon_btn_row.pack(anchor="w", pady=(0, 6), fill="x")

        self.icon_btn = ctk.CTkButton(
            icon_btn_row,
            text="Select Icon (optional)",
            command=self.file_pickers.select_icon,
            fg_color="#0B62A8",
            hover_color="#0B62A8",
            width=160,
            font=("Rubik UI", 15, "bold")
        )
        self.icon_btn.pack(side="left", padx=(0, 6))

        self.ico_convert_btn = ctk.CTkButton(
            icon_btn_row,
            text="Open ICO Converters",
            command=open_icon_sites,
            fg_color="#0B62A8",
            hover_color="#0B62A8",
            font=("Rubik UI", 15, "bold"),
            width=160
        )
        self.ico_convert_btn.pack(side="left")

        # -------- Row 2: entry + clear --------
        icon_entry_row = ctk.CTkFrame(icon_block, fg_color="transparent")
        icon_entry_row.pack(anchor="w", pady=(0, 0), fill="x")

        self.icon_entry = ctk.CTkEntry(
            icon_entry_row,
            textvariable=self.icon_path_var,
            width=360,
            placeholder_text="No icon selected..."
        )
        self.icon_entry.pack(side="left")

        def clear_icon():
            self.icon_path_var.set("")
            self.icon_user_cleared = True
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.icon_clear_btn = ctk.CTkButton(
            icon_entry_row,
            text="↺",
            width=36,
            height=32,
            fg_color="#444444",
            hover_color="#555555",
            command=clear_icon
        )
        self.icon_clear_btn.pack(side="left", padx=(8, 0))

        # =============================================================
        # Output Folder
        # =============================================================

        output_block = ctk.CTkFrame(self, fg_color="transparent")
        output_block.pack(anchor="w", pady=(0, 2), padx=20, fill="x")

        # -------- Row 1: button + status stack (TIGHT) --------
        output_btn_row = ctk.CTkFrame(output_block, fg_color="transparent")
        output_btn_row.pack(anchor="w", pady=(0, 2), fill="x")

        self.output_btn = ctk.CTkButton(
            output_btn_row,
            text="Select Output Folder",
            command=self.file_pickers.select_output_folder,
            width=160,
            font=("Rubik UI", 15, "bold")
        )
        self.output_btn.pack(side="left")   # ❌ no pady

        output_status_stack = ctk.CTkFrame(output_btn_row, fg_color="transparent")
        output_status_stack.pack(side="left", padx=(8, 0))

        self.output_path_status_label = ctk.CTkLabel(
            output_status_stack,
            text="EXE OUTPUT PATH NOT SET",
            font=("Rubik UI", 15),
            text_color="#be1a1a"
        )
        self.output_path_status_label.pack(anchor="w", pady=(1, 1))

        self.exe_name_status_label = ctk.CTkLabel(
            output_status_stack,
            text="EXE NAME NOT SET",
            font=("Rubik UI", 15),
            text_color="#be1a1a"
        )
        self.exe_name_status_label.pack(anchor="w", pady=(1, 1))

        # -------- Row 2: output entry + reset --------
        output_entry_row = ctk.CTkFrame(output_block, fg_color="transparent")
        output_entry_row.pack(anchor="w", pady=(0, 5), fill="x")

        self.output_entry = ctk.CTkEntry(
            output_entry_row,
            textvariable=self.output_path_var,
            width=360,
            placeholder_text="No output folder selected..."
        )
        self.output_entry.pack(side="left")

        def get_desktop_path():
            return os.path.join(os.path.expanduser("~"), "Desktop")

        def reset_output_to_desktop():
            desktop = get_desktop_path()
            self.output_path_var.set(desktop)
            self.output_user_cleared = True
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.output_refresh_btn = ctk.CTkButton(
            output_entry_row,
            text="↺",
            width=36,
            height=32,
            fg_color="#444444",
            hover_color="#555555",
            command=reset_output_to_desktop
        )
        self.output_refresh_btn.pack(side="left", padx=(8, 0))

        # -------- Row 3: EXE name + reset (TIGHT) --------
        exe_row = ctk.CTkFrame(output_block, fg_color="transparent")
        exe_row.pack(anchor="w", pady=(1, 0), fill="x")

        self.exe_entry = ctk.CTkEntry(
            exe_row,
            textvariable=self.exe_name_var,
            width=360,
            placeholder_text="Output file name (without .exe)"
        )
        self.exe_entry.pack(side="left")

        self.exe_entry_default_border = self.exe_entry.cget("border_color")

        def reset_exe_name_from_script():
            script = self.entry_script
            if not script or not os.path.isfile(script):
                return

            derived = os.path.splitext(os.path.basename(script))[0]

            self.exe_name_user_modified = False
            self.exe_name_var.set(derived)

            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.refresh_btn = ctk.CTkButton(
            exe_row,
            text="↺",
            width=36,
            height=32,
            fg_color="#444444",
            hover_color="#555555",
            command=reset_exe_name_from_script
        )
        self.refresh_btn.pack(side="left", padx=(8, 0))

        # =============================================================
        # Build Button
        # =============================================================

        self.build_btn = ctk.CTkButton(
            self,
            text="Build EXE",
            command=self.build_exe,
            fg_color="#082e08",
            hover_color="#082e08",
            font=("Rubik UI", 16, "bold")
        )
        self.build_btn.pack(pady=(10, 8), anchor="w", padx=20)

        # ---------------------------------------------------------
        # Fonts
        # ---------------------------------------------------------

        self.status_font_normal = ("Rubik UI", 15, "bold")
        self.status_font_building = ("Rubik UI", 16, "bold")

        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=self.status_font_normal
        )
        self.status_label.pack(pady=(6, 8), anchor="w", padx=20)


        # ----------------------------------------------------
        # Initial validation pass
        # ----------------------------------------------------
        
        from tooltips import attach_tooltips
        attach_tooltips(self)
        
        self.state_ctrl.load_state()
        self._loading_state = False
        self.validator.update_build_button_state()

    # -------------------------------------------------------------
    #  Restore always-on-top when user returns to the app
    # -------------------------------------------------------------

    def _restore_topmost(self, event=None):
        # Restore always-on-top only when user returns to the app
        self.attributes("-topmost", True)

    # -------------------------------------------------------------
    #  Build EXE
    # -------------------------------------------------------------

    def build_exe(self):

        # ==================================================
        # Debug log (Desktop, user-visible)
        # ==================================================

        from datetime import datetime
        import os, time, subprocess

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S") 
        self.debug_log_path = os.path.join( os.path.expanduser("~"), "Desktop", f"EXE_BUILDER_DEBUG_{timestamp}.log" )


        with open(self.debug_log_path, "w", encoding="utf-8") as f:
            f.write("BUILD STARTED\n")

        IS_FROZEN = getattr(sys, "frozen", False)

        with open(self.debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"IS_FROZEN={IS_FROZEN}\n")
            f.write(f"ENTRY_SCRIPT={repr(self.entry_script)}\n")
            f.write(f"PROJECT_ROOT={repr(self.project_root)}\n")
            f.write(f"PYTHON_INTERPRETER_PATH={repr(self.python_interpreter_path)}\n")

        # ==================================================
        # CANCEL MODE — if build already running
        # ==================================================

        if self.building:
            self.build_cancellation.cancel_build()
            return

        import build_cancellation
        self.build_cancellation = build_cancellation.BuildCancellation(
            app=self, ui=self
        )

        # ==================================================
        # READ UI VALUES
        # ==================================================

        script = self.script_path_var.get().strip()
        outdir = self.output_path_var.get().strip()
        icon = self.icon_path_var.get().strip()

        entry_point = self.entry_script
        project_root = self.project_root

        if not entry_point and script and os.path.isfile(script):
            entry_point = script
            project_root = os.path.dirname(script)

        self.entry_script = entry_point
        self.project_root = project_root

        # ==================================================
        # Bundle validation
        # ==================================================

        from bundle_validation import validate_bundle_inputs
        ok, error = validate_bundle_inputs(self)

        if not ok:
            self.build_cancellation.abort_build(error)
            return

        # ==================================================
        # ENTER BUILD MODE
        # ==================================================

        self.building = True
        self.build_btn.configure(
            text="Cancel EXE",
            fg_color="#d43c3c",
            hover_color="#b22d2d",
            command=self.build_exe
        )

        self.status_label.configure(font=self.status_font_building)

        if hasattr(self, "icon_clear_btn"):
            self.icon_clear_btn.configure(
                state="disabled",
                fg_color="#2a2a2a",
                hover_color="#2a2a2a"
            )

        self.build_start_time = time.time()
        self.state_ctrl.update_eta_loop()

        # ==================================================
        # Final validation
        # ==================================================

        if not entry_point or not os.path.isfile(entry_point):
            self.build_cancellation.abort_build("Invalid or missing entry script.")
            return

        if not project_root or not os.path.isdir(project_root):
            self.build_cancellation.abort_build("Invalid project folder.")
            return

        exe_name = self.exe_name_var.get().strip()
        if not exe_name:
            self.build_cancellation.abort_build("Please enter an EXE name.")
            return

        # ==================================================
        # Resolve PyInstaller (ALWAYS via Python interpreter)
        # ==================================================

        python = self.python_interpreter_path
        if not python or not os.path.isfile(python):
            self.build_cancellation.abort_build(
                "Python interpreter not found.\n"
                "Please select a Python interpreter before building."
            )
            return

        result = subprocess.run(
            [python, "-m", "PyInstaller", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            self.build_cancellation.abort_build(
                "PyInstaller is not available in the selected Python interpreter.\n\n"
                "Install it with:\n\npip install pyinstaller"
            )
            return

        cmd_prefix = [python, "-m", "PyInstaller"]

        self.status_label.configure(text="Using PyInstaller (python -m)")
        self.update()

        # ==================================================
        # Build paths
        # ==================================================

        self.build_counter += 1
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        final_exe_name = f"{exe_name}_{timestamp}"

        build_path = os.path.join(outdir, "build", final_exe_name)
        spec_path = os.path.join(outdir, "spec", final_exe_name)

        os.makedirs(build_path, exist_ok=True)
        os.makedirs(spec_path, exist_ok=True)

        cmd = [
            *cmd_prefix,
            "--onedir",
            "--clean",
            "--noconfirm",
            "--collect-all=tkinter",
            "--collect-all=tk",
            "--windowed",
            "--noconsole",
            "--hidden-import=pynput",
            "--hidden-import=win32gui",
            "--hidden-import=win32con",
            "--hidden-import=win32api",
            "--hidden-import=win32process",
            "--hidden-import=pygetwindow",
            "--hidden-import=pystray",
            f"--distpath={outdir}",
            f"--workpath={build_path}",
            f"--specpath={spec_path}",
            f"--name={final_exe_name}",
            entry_point
        ]

        if project_root:
            cmd.append(f"--add-data={project_root}{os.pathsep}.")

        data_file = os.path.join(project_root, "screen_mover_state.json")
        if os.path.isfile(data_file):
            cmd.append(f"--add-data={data_file}{os.pathsep}.")

        if icon:
            cmd += ["--icon", icon]

        self.current_build_paths = [
            os.path.join(outdir, final_exe_name + ".exe"),
            os.path.join(outdir, "build", final_exe_name),
            os.path.join(outdir, "spec", final_exe_name),
        ]

        # ==================================================
        # Run PyInstaller (threaded)
        # ==================================================

        self.status_label.configure(text="Building...")

        def run_build():
            try:
                with open(self.debug_log_path, "a", encoding="utf-8") as f:
                    f.write("ENTERED run_build\n")
                    f.write("CMD: " + " ".join(cmd) + "\n")

                self.build_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=CREATE_NO_WINDOW
                )

                out, err = self.build_process.communicate()
                ret = self.build_process.returncode

                with open(self.debug_log_path, "a", encoding="utf-8") as f:
                    f.write(f"RETURN CODE: {ret}\n")
                    f.write("STDERR:\n" + (err or "<empty>") + "\n")

                if not self.building:
                    return

                if ret == 0:
                    self.after(0, lambda: self.status_label.configure(
                        text="Build complete."
                    ))
                    self.last_build_seconds = int(
                        time.time() - self.build_start_time
                    )
                    self.state_ctrl.save_state()
                    self.after(5000, self.iconify)
                else:
                    self.after(0, lambda: self.status_label.configure(
                        text="Build failed. See debug log."
                    ))

            finally:
                self.after(0, self.restore_build_ui)

        threading.Thread(target=run_build, daemon=True).start()

    # ==================================================
    # UI RESTORE: Build finished / aborted / cancelled
    # ==================================================

    def restore_build_ui(self):
        self.building = False

        # -------------------------------
        # Restore Build button
        # -------------------------------
        
        self.build_btn.configure(
            text="Build EXE",
            fg_color="#3bbf3b",
            hover_color="#2e9e2e",
            command=self.build_exe
        )

        # -------------------------------
        # Re-enable recovery buttons
        # -------------------------------
        
        if hasattr(self, "output_refresh_btn"):
            self.output_refresh_btn.configure(state="normal")

        if hasattr(self, "icon_clear_btn"):
            self.icon_clear_btn.configure(state="normal")

        # -------------------------------
        # Re-apply validation policy
        # -------------------------------
        
        self.validator.update_build_button_state()
        self.status_label.configure(font=self.status_font_normal)

    def set_status(self, text):
        self.status_label.configure(text=text)

# -------------------------------------------------------------
# Launch
# -------------------------------------------------------------

if __name__ == "__main__":
    app = EXEBuilderApp()
    app.mainloop()