import sys
import os
import subprocess
import time
import webbrowser
import ctypes
import threading

from datetime import datetime
from ctypes import wintypes
from bundle_validation import validate_bundle_inputs
from tooltips import attach_tooltips


from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton,QFrame,QApplication,QHBoxLayout,QVBoxLayout,QCheckBox,QLineEdit, QDialog

from validation_controller import ValidationController
from activation_controller import ActivationController
from file_pickers import FilePickerController
from state_controller import StateController
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

CREATE_NO_WINDOW = 0x08000000

# Try to create a mutex
mutex = ctypes.windll.kernel32.CreateMutexW(
    None,
    wintypes.BOOL(True),
    "EXEBUILDER_MUTEX"
)

# ERROR_ALREADY_EXISTS means another instance is running
if ctypes.GetLastError() == 183:
    event = ctypes.windll.kernel32.OpenEventW(
        0x00100002,
        False,
        "EXEBUILDER_ACTIVATE_EVENT"
    )

    if event:
        ctypes.windll.kernel32.SetEvent(event)

    sys.exit(0)


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# -------------------------------------------------------------
#  EXE Builder App
# -------------------------------------------------------------

class EXEBuilderApp(QWidget):
    def __init__(self):
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
            None,
            False,
            False,
            "EXEBUILDER_ACTIVATE_EVENT"
        )

        threading.Thread(
            target=self.activation_controller.listen_for_activation,
            daemon=True
        ).start()

        # ---------------------------------------------------------
        # ALWAYS ON TOP
        # ---------------------------------------------------------

        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.building = False
        self.build_process = None
        self.current_build_paths = []
        self.build_btn = None
        self.last_build_seconds = 45
        self.build_counter = 0

        self.setWindowTitle("")
        self.setFixedSize(500, 725)

        # --------------------
        # VARIABLES
        # --------------------

        self.tooltips_enabled = True
        self.script_path = ""
        self.icon_path = ""
        self.output_path = ""
        self.python_path = ""
        self.exe_name = ""

        self._loading_state = True
        self.script_user_cleared = False
        self.python_user_cleared = False
        self.icon_user_cleared = False
        self.output_user_cleared = False
        self.exe_name_user_cleared = False

        self._was_build_ready = False
        self._dependency_popup_shown = False
        
        


        # =============================================================
        # EXE name ownership tracking (USER intent only)
        # =============================================================

        def _on_exe_name_user_edit(text):
            if self._loading_state:
                return
            self.exe_name_user_modified = True


        # =============================================================
        # EXE name cleared by USER
        # =============================================================

        def on_exe_name_change(text):
            if self._loading_state:
                return

            value = text.strip()
            if not value:
                self.exe_name_user_cleared = True
                self.state_ctrl.save_state()

            self.validator.update_build_button_state()


        def on_script_path_change(text):
            if self._loading_state:
                return

            value = text.strip()

            if not value:
                self.entry_script = None
                self.project_root = None
                self.script_user_cleared = True
                self.state_ctrl.save_state()

            self.validator.update_build_button_state()


        # =============================================================
        # Title + Tooltip Toggle
        # =============================================================

        title_row = QWidget(self)
        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(10)

        # Toggle
        self.tooltips_checkbox = QCheckBox("Tooltips")
        self.tooltips_checkbox.setChecked(True)
        self.tooltips_checkbox.setFont(QFont("Rubik UI", 13, QFont.Bold))

        def on_tooltips_toggle(state):
            self.tooltips_enabled = bool(state)
            self.state_ctrl.save_state()

        self.tooltips_checkbox.stateChanged.connect(on_tooltips_toggle)
        title_layout.addWidget(self.tooltips_checkbox)

        # Title
        title_label = QLabel(" Win 11 → Python → EXE Builder")
        title_label.setFont(QFont("Rubik UI", 15, QFont.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        self.main_layout.addWidget(title_row)


        # =============================================================
        # Script / Buttons Section
        # =============================================================

        def open_python_site():
            webbrowser.open("https://www.python.org")


        row2 = QWidget(self)
        row2_layout = QVBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(5)
        
        # -------------------------
        # Combined FRAME (apps + interpreter)
        # -------------------------

        combined_frame = QFrame()
        combined_frame.setFrameShape(QFrame.StyledPanel)
        combined_frame.setFrameShadow(QFrame.Raised)
        combined_frame.setLineWidth(1)

        combined_layout = QVBoxLayout(combined_frame)
        combined_layout.setContentsMargins(6, 6, 6, 6)
        combined_layout.setSpacing(6)

        # =================================================
        # Apps (ROW inside vertical stack)
        # =================================================

        apps_row = QWidget()
        apps_layout = QHBoxLayout(apps_row)
        apps_layout.setContentsMargins(0, 0, 0, 0)

        self.apps_btn = QPushButton("Open Installed Apps")
        self.apps_btn.setFixedWidth(160)
        self.apps_btn.clicked.connect(self.file_pickers.open_installed_apps)

        self.open_python_site_btn = QPushButton("Python.org")
        self.open_python_site_btn.setFixedWidth(120)
        self.open_python_site_btn.clicked.connect(open_python_site)

        apps_layout.addWidget(self.apps_btn)
        apps_layout.addWidget(self.open_python_site_btn)
        apps_layout.addStretch()

        combined_layout.addWidget(apps_row)

        # =================================================
        # Interpreter (VERTICAL stack)
        # =================================================

        interpreter_container = QWidget()
        interpreter_layout = QVBoxLayout(interpreter_container)
        interpreter_layout.setContentsMargins(0, 0, 0, 0)
        interpreter_layout.setSpacing(4)

        # --- Button ---
        self.interpreter_btn = QPushButton("Select Python Interpreter")
        self.interpreter_btn.setFixedWidth(180)
        self.interpreter_btn.clicked.connect(
            self.file_pickers.select_python_interpreter
        )
        interpreter_layout.addWidget(self.interpreter_btn, alignment=Qt.AlignLeft)

        # --- Status ---
        self.python_status_label = QLineEdit("PYTHON INTERPRETER NOT SET")
        self.python_status_label.setReadOnly(True)
        self.python_status_label.setFont(QFont("Rubik UI", 13))
        self.python_status_label.setStyleSheet("color: #be1a1a;")
        interpreter_layout.addWidget(self.python_status_label)

        # --- Path ---
        self.python_entry = QLineEdit()
        self.python_entry.setReadOnly(True)
        self.python_entry.setPlaceholderText("No Python interpreter selected...")
        interpreter_layout.addWidget(self.python_entry)

        # add interpreter block into frame
        combined_layout.addWidget(interpreter_container)

        # IMPORTANT: this keeps everything sitting correctly under apps
        combined_layout.addStretch()

        # =================================================
        # ADD FRAME (only once)
        # =================================================

        row2_layout.addWidget(combined_frame)
        
        # ✅ ADD THIS RIGHT HERE
        self.main_layout.addWidget(row2)

        # ---------------------------------
        # Python Folder FRAME (vertical)
        # ---------------------------------

        python_frame = QFrame()
        python_frame.setFrameShape(QFrame.StyledPanel)
        python_frame.setFrameShadow(QFrame.Raised)
        python_frame.setLineWidth(1)

        python_layout = QVBoxLayout(python_frame)
        python_layout.setContentsMargins(6, 6, 6, 6)
        python_layout.setSpacing(5)

        # =================================================
        # Row 1: Select folder button
        # =================================================

        self.folder_btn = QPushButton("Select Python Folder")
        self.folder_btn.setFixedWidth(160)
        self.folder_btn.clicked.connect(self.file_pickers.select_script_folder)

        python_layout.addWidget(self.folder_btn, alignment=Qt.AlignLeft)

        # =================================================
        # Row 2: Status
        # =================================================

        self.script_folder_status_label = QLineEdit("PYTHON FOLDER NOT SET")
        self.script_folder_status_label.setFont(QFont("Rubik UI", 13))
        self.script_folder_status_label.setStyleSheet("color: #be1a1a;")
        self.script_folder_status_label.setReadOnly(True)

        python_layout.addWidget(self.script_folder_status_label)

        # =================================================
        # Row 3: Path + reset (side-by-side)
        # =================================================

        script_row = QWidget()
        script_layout = QHBoxLayout(script_row)
        script_layout.setContentsMargins(0, 0, 0, 0)

        self.script_path_input = QLineEdit()
        self.script_path_input.setReadOnly(True)
        self.script_path_input.setPlaceholderText("Select script or folder...")
        script_layout.addWidget(self.script_path_input)

        def clear_script_path():
            self.script_path_input.clear()
            self.script_user_cleared = True
            self.entry_script = None
            self.project_root = None
            self.script_path = ""
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.script_clear_btn = QPushButton("↺")
        self.script_clear_btn.setFixedSize(36, 32)
        self.script_clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #444444;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.script_clear_btn.clicked.connect(clear_script_path)

        script_layout.addWidget(self.script_clear_btn)

        python_layout.addWidget(script_row)

        # =================================================
        # ADD FRAME
        # =================================================

        self.main_layout.addWidget(python_frame)
       

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


        icon_frame = QFrame()
        icon_frame.setFrameShape(QFrame.StyledPanel)
        icon_frame.setFrameShadow(QFrame.Raised)
        icon_frame.setLineWidth(1)

        icon_frame_layout = QVBoxLayout(icon_frame)
        icon_frame_layout.setContentsMargins(6, 6, 6, 6)
        icon_frame_layout.setSpacing(0)

        icon_block = QWidget()
        icon_block_layout = QVBoxLayout(icon_block)
        icon_block_layout.setContentsMargins(0, 0, 0, 0)
        icon_block_layout.setSpacing(6)

        # -------- Row 1: buttons --------

        icon_btn_row = QWidget()
        icon_btn_layout = QHBoxLayout(icon_btn_row)
        icon_btn_layout.setContentsMargins(0, 0, 0, 0)

        self.icon_btn = QPushButton("Select Icon (optional)")
        self.icon_btn.setFixedWidth(160)
        self.icon_btn.clicked.connect(self.file_pickers.select_icon)
        icon_btn_layout.addWidget(self.icon_btn)

        self.ico_convert_btn = QPushButton("Open ICO Converters")
        self.ico_convert_btn.setFixedWidth(160)
        self.ico_convert_btn.clicked.connect(open_icon_sites)
        icon_btn_layout.addWidget(self.ico_convert_btn)

        icon_btn_layout.addStretch()
        icon_block_layout.addWidget(icon_btn_row)

        # -------- Row 2: entry + clear --------

        icon_entry_row = QWidget()
        icon_entry_layout = QHBoxLayout(icon_entry_row)
        icon_entry_layout.setContentsMargins(0, 0, 0, 0)

        self.icon_path_input = QLineEdit()
        self.icon_path_input.setReadOnly(True)
        self.icon_path_input.setPlaceholderText("No icon selected...")
        self.icon_path_input.setFixedWidth(360)
        icon_entry_layout.addWidget(self.icon_path_input)

        def clear_icon():
            self.icon_path_input.clear()
            self.icon_user_cleared = True
            self.icon_path = ""
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.icon_clear_btn = QPushButton("↺")
        self.icon_clear_btn.setFixedSize(36, 32)
        self.icon_clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #444444;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.icon_clear_btn.clicked.connect(clear_icon)

        icon_entry_layout.addWidget(self.icon_clear_btn)
        
        
        icon_block_layout.addWidget(icon_entry_row)
        icon_block_layout.addStretch(5)

        icon_frame_layout.addWidget(icon_block)
        self.main_layout.addWidget(icon_frame)

        # =============================================================
        # Output Folder
        # =============================================================

        output_block = QWidget()
        output_block_layout = QVBoxLayout(output_block)
        output_block_layout.setContentsMargins(0, 0, 0, 0)
        output_block_layout.setSpacing(2)

        # -------- Row 1: button + status stack --------

        # =============================================================
        # Output FRAME (structured vertical)
        # =============================================================

        output_frame = QFrame()
        output_frame.setFrameShape(QFrame.StyledPanel)
        output_frame.setFrameShadow(QFrame.Raised)
        output_frame.setLineWidth(1)

        output_layout = QVBoxLayout(output_frame)
        output_layout.setContentsMargins(6, 6, 6, 6)
        output_layout.setSpacing(5)

        # =================================================
        # Row 1: Select Output Folder button
        # =================================================

        self.output_btn = QPushButton("Select Output Folder")
        self.output_btn.setFixedWidth(160)
        self.output_btn.clicked.connect(self.file_pickers.select_output_folder)

        output_layout.addWidget(self.output_btn, alignment=Qt.AlignLeft)

        # =================================================
        # Row 2: Status lines (stacked)
        # =================================================

        self.output_path_status_label = QLineEdit("EXE OUTPUT PATH NOT SET")
        self.output_path_status_label.setReadOnly(True)
        self.output_path_status_label.setFont(QFont("Rubik UI", 13))
        self.output_path_status_label.setStyleSheet("color: #be1a1a;")

        self.exe_name_status_label = QLineEdit("EXE NAME NOT SET")
        self.exe_name_status_label.setReadOnly(True)
        self.exe_name_status_label.setFont(QFont("Rubik UI", 13))
        self.exe_name_status_label.setStyleSheet("color: #be1a1a;")

        output_layout.addWidget(self.output_path_status_label)
        output_layout.addWidget(self.exe_name_status_label)

        # =================================================
        # Row 3: Output path + reset
        # =================================================

        output_entry_row = QWidget()
        output_entry_layout = QHBoxLayout(output_entry_row)
        output_entry_layout.setContentsMargins(0, 0, 0, 0)

        self.output_path_input = QLineEdit()
        self.output_path_input.setReadOnly(True)
        self.output_path_input.setPlaceholderText("No output folder selected...")
        output_entry_layout.addWidget(self.output_path_input)

        def get_desktop_path():
            return os.path.join(os.path.expanduser("~"), "Desktop")

        def reset_output_to_desktop():
            desktop = get_desktop_path()
            self.output_path_input.setText(desktop)
            self.output_user_cleared = True
            self.output_path = desktop
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.output_refresh_btn = QPushButton("↺")
        self.output_refresh_btn.setFixedSize(36, 32)
        self.output_refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #444444;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.output_refresh_btn.clicked.connect(reset_output_to_desktop)

        output_entry_layout.addWidget(self.output_refresh_btn)
        output_layout.addWidget(output_entry_row)

        # =================================================
        # Row 4: EXE name + reset (INSIDE FRAME)
        # =================================================

        exe_row = QWidget()
        exe_layout = QHBoxLayout(exe_row)
        exe_layout.setContentsMargins(0, 0, 0, 0)

        self.exe_name_input = QLineEdit()
        self.exe_name_input.setReadOnly(True)
        self.exe_name_input.setPlaceholderText("Output file name (without .exe)")
        exe_layout.addWidget(self.exe_name_input)

        def reset_exe_name_from_script():
            script = self.entry_script
            if not script or not os.path.isfile(script):
                return

            derived = os.path.splitext(os.path.basename(script))[0]

            self.exe_name_user_modified = False
            self.exe_name_input.setText(derived)

            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.refresh_btn = QPushButton("↺")
        self.refresh_btn.setFixedSize(36, 32)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #444444;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        self.refresh_btn.clicked.connect(reset_exe_name_from_script)

        exe_layout.addWidget(self.refresh_btn)

        # ✅ THIS is the key line (must be BEFORE adding frame to main_layout)
        output_layout.addWidget(exe_row)

        # =================================================
        # ADD FRAME (ONLY ONCE, AT THE VERY END)
        # =================================================

        self.main_layout.addWidget(output_frame)
                
        
        # -----------------------------
        # CONNECT SIGNALS (PySide6)
        # -----------------------------

        self.exe_name_input.textChanged.connect(_on_exe_name_user_edit)
        self.exe_name_input.textChanged.connect(on_exe_name_change)

        self.script_path_input.textChanged.connect(on_script_path_change)

        self.output_path_input.textChanged.connect(
            lambda text: None if self._loading_state else self.validator.update_build_button_state()
        )

        self.exe_name_input.textChanged.connect(
            lambda text: None if self._loading_state else self.validator.update_build_button_state()
        )

        self.icon_path_input.textChanged.connect(
            lambda text: None if self._loading_state else self.validator.update_build_button_state()
        )
        

        # Store default style (Qt doesn't expose border color directly like CTk)
        self.exe_entry_default_style = self.exe_name_input.styleSheet()
        
        # =============================================================
        # Build FRAME
        # =============================================================

        build_frame = QFrame()
        build_frame.setFrameShape(QFrame.StyledPanel)
        build_frame.setFrameShadow(QFrame.Raised)
        build_frame.setLineWidth(1)

        build_layout = QVBoxLayout(build_frame)
        build_layout.setContentsMargins(6, 6, 6, 6)
        build_layout.setSpacing(6)

        # =================================================
        # Row 1: Build button (centered)
        # =================================================

        self.build_btn = QPushButton("Build EXE")
        self.build_btn.clicked.connect(self.build_exe)

        build_layout.addWidget(self.build_btn, alignment=Qt.AlignHCenter)

        # =================================================
        # Row 2: Status
        # =================================================

        self.status_label = QLineEdit("Ready")
        self.status_label.setReadOnly(True)
        
        

        build_layout.addWidget(self.status_label)

        # =================================================
        # ADD FRAME
        # =================================================

        self.main_layout.addWidget(build_frame)

        # ----------------------------------------------------
        # Initial validation pass
        # ----------------------------------------------------

        attach_tooltips(self)

        self.state_ctrl.load_state()
        self._loading_state = False
        self.validator.validation_status_message()
        self.validator.update_build_button_state()

        self.validation_controller = ValidationController(self)
        
        for btns in [
            self.open_python_site_btn,
            self.apps_btn,
            self.folder_btn,
            self.interpreter_btn,
            self.icon_btn,
            self.ico_convert_btn,
            self.build_btn,
            self.output_btn
            
        ]:
            
            btns.setStyleSheet("background-color: #494949")
            btns.setFixedHeight(35)
            
        for lines in [
            self.script_folder_status_label,
            self.output_path_status_label,
            self.exe_name_status_label
            
            ]:
                lines.setReadOnly(True)
                lines.setFixedSize(225,35)
                
        self.python_status_label.setFixedSize(325,35)

    # =============================================================
    # Dependency Popup (PySide6)
    # =============================================================

    def show_dependency_warning_popup(self, packages: list[str]):
        if not packages:
            return



        self.popup = QDialog(self)
        self.popup.setWindowTitle("Dependency Notice")
        self.popup.setModal(False)
        self.popup.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        layout = QVBoxLayout(self.popup)

        label1 = QLabel(
            "This script references the following external packages:"
        )
        label1.setWordWrap(True)
        label1.setFont(QFont("Rubik UI", 13, QFont.Bold))
        layout.addWidget(label1)

        pkg_text = ", ".join(packages)

        label2 = QLabel(pkg_text)
        label2.setWordWrap(True)
        label2.setFont(QFont("Rubik UI", 13, QFont.Bold))
        layout.addWidget(label2)

        label3 = QLabel(
            "Ensure they are installed in the selected Python environment. "
            "E.g. py -3.13 -m pip install <package-name>."
        )
        label3.setWordWrap(True)
        label3.setFont(QFont("Rubik UI", 13, QFont.Bold))
        layout.addWidget(label3)

        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(self.popup.close)
        layout.addWidget(ok_btn, alignment=Qt.AlignRight)

        # Position to the right of main window
        self.popup.adjustSize()
        x = self.x() + self.width() + 10
        y = self.y() + 50
        self.popup.move(x, y)

        self.popup.show()

    # -------------------------------------------------------------
    # Restore always-on-top when user returns to the app
    # -------------------------------------------------------------

    def _restore_topmost(self, event=None):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()


    # -------------------------------------------------------------
    # Build EXE
    # -------------------------------------------------------------

    def build_exe(self):



        # ==================================================
        # Debug log (Desktop, user-visible)
        # ==================================================

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.debug_log_path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            f"EXE_BUILDER_DEBUG_{timestamp}.log"
        )

        with open(self.debug_log_path, "w", encoding="utf-8") as f:
            f.write("BUILD STARTED\n")

        IS_FROZEN = getattr(sys, "frozen", False)

        with open(self.debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"IS_FROZEN={IS_FROZEN}\n")
            f.write(f"ENTRY_SCRIPT={repr(self.entry_script)}\n")
            f.write(f"PROJECT_ROOT={repr(self.project_root)}\n")
            f.write(f"PYTHON_INTERPRETER_PATH={repr(self.python_interpreter_path)}\n")

        # ==================================================
        # CANCEL MODE
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

        script = self.script_path_input.text().strip()
        outdir = self.output_path_input.text().strip()
        icon = self.icon_path_input.text().strip()

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

        ok, error = validate_bundle_inputs(self)

        if not ok:
            self.build_cancellation.abort_build(error)
            return

        # ==================================================
        # ENTER BUILD MODE
        # ==================================================

        self.building = True
        self.build_btn.setText("Cancel EXE")
        self.build_btn.setStyleSheet("background-color: #d43c3c;")
        self.build_btn.clicked.disconnect()
        self.build_btn.clicked.connect(self.build_exe)

        self.status_label.setFont(self.status_font_building)
        self.status_label.setFixedWidth(425)

        if hasattr(self, "icon_clear_btn"):
            self.icon_clear_btn.setEnabled(False)
            self.icon_clear_btn.setStyleSheet("background-color: #2a2a2a;")

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

        exe_name = self.exe_name_input.text().strip()
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

        self.status_label.setText("Using PyInstaller (python -m)")
        self.repaint()

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
            "--collect-all=qt_material",
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

        self.status_label.setText("Building...")

        def run_build():
            try:
                with open(self.debug_log_path, "a", encoding="utf-8") as f:
                    f.write("ENTERED run_build\n")
                    f.write("CMD: " + " ".join(cmd) + "\n")

                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=CREATE_NO_WINDOW
                )

                self.build_process = proc

                out, err = proc.communicate()
                ret = proc.returncode

                with open(self.debug_log_path, "a", encoding="utf-8") as f:
                    f.write(f"RETURN CODE: {ret}\n")
                    f.write("STDERR:\n" + (err or "<empty>") + "\n")

                if not self.building:
                    return

                if ret == 0:
                    QTimer.singleShot(0, lambda: self.status_label.setText("Build complete."))
                    self.last_build_seconds = int(time.time() - self.build_start_time)
                    self.state_ctrl.save_state()
                    QTimer.singleShot(5000, self.showMinimized)
                else:
                    QTimer.singleShot(0, lambda: self.status_label.setText("Build failed. See debug log."))

            finally:
                self.build_process = None
                QTimer.singleShot(0, self.restore_build_ui)


        threading.Thread(target=run_build, daemon=True).start()

    # ==================================================
    # UI RESTORE: Build finished / aborted / cancelled
    # ==================================================

    def restore_build_ui(self):
        self.building = False

        # -------------------------------
        # Restore Build button
        # -------------------------------

        try:
            self.build_btn.clicked.disconnect()
        except:
            pass

        self.build_btn.setText("Build EXE")
        self.build_btn.setStyleSheet("background-color: #3bbf3b;")
        self.build_btn.clicked.connect(self.build_exe)

        # -------------------------------
        # Re-enable recovery buttons
        # -------------------------------

        if hasattr(self, "output_refresh_btn"):
            self.output_refresh_btn.setEnabled(True)

        if hasattr(self, "icon_clear_btn"):
            self.icon_clear_btn.setEnabled(True)

        # -------------------------------
        # Re-apply validation policy
        # -------------------------------

        self.validator.update_build_button_state()
       

    def set_status(self, text):
        self.status_label.setText(text)


# -------------------------------------------------------------
# Launch
# -------------------------------------------------------------

if __name__ == "__main__":

    # ✅ FORCE valid default font (kills -1 propagation)
    font = QFont("Rubik UI")
    font.setPointSize(10)
    QApplication.setFont(font)

    app = QApplication(sys.argv)
    window = EXEBuilderApp()
    window.show()
    sys.exit(app.exec())