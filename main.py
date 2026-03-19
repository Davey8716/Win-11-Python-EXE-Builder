import sys
import os
import subprocess
import time
import webbrowser
import ctypes
import threading
import json

from datetime import datetime
from ctypes import wintypes
from bundle_validation import validate_bundle_inputs
from tooltips import attach_tooltips


from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton,QFrame,QApplication,QHBoxLayout,QVBoxLayout,QCheckBox,QLineEdit, QDialog,QSizePolicy

from validation_controller import ValidationController
from activation_controller import ActivationController
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from file_pickers import FilePickerController
from state_controller import StateController
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

from PySide6.QtWidgets import QHBoxLayout, QComboBox,QMessageBox

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

        self._last_advisory_script = None
        self._eta_running = False
        self._loading_state = True

        self.entry_script = None
        self.project_root = None
        self.exe_name_user_modified = False
        
        self.validation_controller = ValidationController(self)
        self.state_ctrl = StateController(self)
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
        self.setFixedSize(500, 770)

        if not hasattr(self, "tooltips_enabled"):
            self.tooltips_enabled = True

        if not hasattr(self, "dependency_notice_enabled"):
            self.dependency_notice_enabled = True

        if not hasattr(self, "script_path"):
            self.script_path = ""

        if not hasattr(self, "icon_path"):
            self.icon_path = ""

        if not hasattr(self, "output_path"):
            self.output_path = ""

        if not hasattr(self, "python_path"):
            self.python_path = ""

        if not hasattr(self, "exe_name"):
            self.exe_name = ""
        # =============================================================
        # Title + Tooltip Toggle
        # =============================================================
        
        title_row = QWidget(self)
        title_row.setFixedHeight(40)

        toggles_row = QWidget(self)
        toggles_row.setFixedHeight(70)

        title_layout = QHBoxLayout(title_row)
        title_layout.setContentsMargins(8, 0, 8, 0)
        title_layout.setSpacing(2)

        toggles_layout = QVBoxLayout(toggles_row)
        toggles_layout.setContentsMargins(8, 0, 8, 0)
        toggles_layout.setSpacing(2)

        self.tooltips_checkbox = QCheckBox("Tooltips")
        self.dependency_notice = QCheckBox("Dependency Notice")

        for checkbox in [
            self.tooltips_checkbox,
            self.dependency_notice
            
        ]:
            checkbox.setFont(QFont("Rubik Ui",11, QFont.Bold))
            checkbox.setChecked(True)
            checkbox.setFixedSize(185,35)
            

        title_label = QLabel(" Win 11 → Python → EXE Builder")
        title_label.setFont(QFont("Rubik UI", 12, QFont.Bold))
        title_label.setFixedSize(290,35)


        toggles_layout.addWidget(self.tooltips_checkbox)
        toggles_layout.addWidget(self.dependency_notice)
        toggles_layout.setAlignment(Qt.AlignLeft)
        toggles_layout.setContentsMargins(3,3,3,3)
        
        toggles_layout.addStretch()

        title_layout.addWidget(title_label)
        title_layout.setContentsMargins(3,3,3,3)
        title_layout.addStretch()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(2)

        self.main_layout.addWidget(title_row)
        self.main_layout.addWidget(toggles_row)
        
        
        
        
        # =============================================================
   




        # =============================================================
        # Script / Buttons Section
        # =============================================================

        def open_python_site():
            webbrowser.open("https://www.python.org")


        row2 = QWidget(self)
        row2_layout = QVBoxLayout(row2)
        row2_layout.setContentsMargins(1,1,1,1)
        row2_layout.setSpacing(1)

        
        # -------------------------
        # Combined FRAME (apps + interpreter)
        # -------------------------

        combined_frame = QFrame()
        combined_frame.setFrameShape(QFrame.StyledPanel)
        combined_frame.setFrameShadow(QFrame.Raised)
        combined_frame.setLineWidth(1)

        combined_layout = QVBoxLayout(combined_frame)
        combined_layout.setContentsMargins(1,1,1,1)
        combined_layout.setSpacing(1)


        # =================================================
        # Apps (ROW inside vertical stack)
        # =================================================

        apps_row = QWidget()
        apps_layout = QHBoxLayout(apps_row)
        apps_layout.setContentsMargins(1,1,1,1)

        self.apps_btn = QPushButton("Open Installed Apps")
        self.apps_btn.clicked.connect(self.file_pickers.open_installed_apps)

        self.open_python_site_btn = QPushButton("Python.org")
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
        interpreter_layout.setContentsMargins(1,1,1,1)
        interpreter_layout.setSpacing(1)


        # --- Button ---
        self.interpreter_btn = QPushButton("Select Python Interpreter")
        self.interpreter_btn.clicked.connect(
            self.file_pickers.select_python_interpreter
        )
        interpreter_layout.addWidget(self.interpreter_btn, alignment=Qt.AlignLeft)

        # --- Status ---
        self.python_status_label = QLineEdit("PYTHON INTERPRETER NOT SET")
        self.python_status_label.setReadOnly(True)
        self.python_status_label.setFont(QFont("Rubik UI", 11))
        self.python_status_label.setStyleSheet("color: #be1a1a;")
        interpreter_layout.addWidget(self.python_status_label)

        # --- Path ---
        self.python_entry_input = QLineEdit()
        self.python_entry_input.setPlaceholderText("No Python interpreter selected...")
        interpreter_layout.addWidget(self.python_entry_input)

        # add interpreter block into frame
        combined_layout.addWidget(interpreter_container)

        # =================================================
        # ADD FRAME (only once)
        # =================================================

        row2_layout.addWidget(combined_frame)

        self.main_layout.addWidget(row2)

        # ---------------------------------
        # Python Folder FRAME (vertical)
        # ---------------------------------

        python_frame = QFrame()
        python_frame.setFrameShape(QFrame.StyledPanel)
        python_frame.setFrameShadow(QFrame.Raised)
        python_frame.setLineWidth(1)

        python_layout = QVBoxLayout(python_frame)
        python_layout.setContentsMargins(3,3,3,3)
        python_layout.setSpacing(3)

        # =================================================
        # Row 1: Select folder button + recent dropdown
        # =================================================


        self.folder_btn = QPushButton("Select Python Folder")
        self.folder_btn.clicked.connect(self.file_pickers.select_script_folder)

        self.recent_folder_dropdown = QComboBox()
        self.recent_folder_dropdown.setFixedSize(150, 35)

        # header item (non-clickable)
        self.recent_folder_dropdown.addItem("Select Recent File")
        self.recent_folder_dropdown.setFont(QFont("Rubik UI", 12))
        
        self.delete_recent_folder = QPushButton("✖")
        self.delete_recent_folder.setFixedSize(35, 35)
        self.delete_recent_folder.setCursor(Qt.PointingHandCursor)

        self.delete_recent_folder.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                color: #e0e0e0;
                font-size: 14px;
            }

            QPushButton:hover {
                background-color: #3a3a3a;
            }

            QPushButton:pressed {
                background-color: #1f1f1f;
            }

            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #555;
            }
        """)

                

        model = self.recent_folder_dropdown.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        
        self.recent_folder_dropdown.setEditable(True)
        if self.recent_folder_dropdown.lineEdit():
            self.recent_folder_dropdown.lineEdit().setFont(QFont("Rubik UI", 12))
      

        # keep header visible initially
        self.recent_folder_dropdown.setCurrentIndex(0)

        # make it look like placeholder but still behave normally
        self.recent_folder_dropdown.setEditable(True)
        self.recent_folder_dropdown.lineEdit().setReadOnly(True)


        self.recent_folder_dropdown.setCurrentIndex(-1)
        if self.recent_folder_dropdown.setEnabled(True):
            self.recent_folder_dropdown.setStyleSheet("""
                QComboBox {
                    background-color: #121212;
                    color: #e0e0e0;
                    border: 1px solid #2a2a2a;
                    padding: 4px;
                }

                QComboBox::drop-down {
                    border: none;
                    background: #121212;
                }

                QComboBox QAbstractItemView {
                    background-color: #121212;
                    color: #e0e0e0;
                    selection-background-color: #2a2a2a;
                }

                QComboBox:disabled {
                    background-color: #1e1e1e;
                    color: #777;
                }
            """)

            

        
        folder_row = QHBoxLayout()
        folder_row.setContentsMargins(0, 0, 0, 0)
        folder_row.setSpacing(5)

        folder_row.addWidget(self.folder_btn)
        folder_row.addWidget(self.recent_folder_dropdown)
        folder_row.addWidget(self.delete_recent_folder)
        folder_row.addStretch()
        
        self.recent_folder_dropdown.currentIndexChanged.connect(self.on_recent_file_selected)
        self.delete_recent_folder.clicked.connect(self.confirm_delete_recent)
  

        python_layout.addLayout(folder_row)
                

        # =================================================
        # Row 2: Status
        # =================================================

        self.script_folder_status_label = QLineEdit("PYTHON FOLDER NOT SET")
        self.script_folder_status_label.setFont(QFont("Rubik UI", 11))
        self.script_folder_status_label.setStyleSheet("color: #be1a1a;")
        self.script_folder_status_label.setReadOnly(True)

        python_layout.addWidget(self.script_folder_status_label)
        
     
        # =================================================
        # Row 3: Path + reset (side-by-side)
        # =================================================

        script_row = QWidget()
        script_layout = QHBoxLayout(script_row)
        script_layout.setContentsMargins(3,3,3,3)
        script_layout.setSpacing(3)


        self.script_path_input = QLineEdit()
    
        self.script_path_input.setPlaceholderText("Select script or folder...")
        script_layout.addWidget(self.script_path_input)

        def clear_script_path():
            self.script_path_input.clear()
            self.entry_script = None
            self.project_root = None
            self.script_path = ""
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()
            
      

        self.script_clear_btn = QPushButton("")
        self.script_clear_btn.clicked.connect(clear_script_path)
        
   

        script_layout.addWidget(self.script_clear_btn)
        script_layout.setContentsMargins(1,1,1,1)

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
        icon_frame_layout.setContentsMargins(1,1,1,1)
        icon_frame_layout.setSpacing(1)


        icon_block = QWidget()
        icon_block_layout = QVBoxLayout(icon_block)
        icon_block_layout.setContentsMargins(1,1,1,1)
        icon_block_layout.setSpacing(1)


        # -------- Row 1: buttons --------

        icon_btn_row = QWidget()
        icon_btn_layout = QHBoxLayout(icon_btn_row)
        icon_btn_layout.setContentsMargins(1,1,1,1)
        icon_btn_layout.setSpacing(1)

        self.icon_btn = QPushButton("Select Icon (optional)")

        self.icon_btn.clicked.connect(self.file_pickers.select_icon)
        icon_btn_layout.addWidget(self.icon_btn)

        self.ico_convert_btn = QPushButton("Open ICO Converters")
        self.ico_convert_btn.clicked.connect(open_icon_sites)
        icon_btn_layout.addWidget(self.ico_convert_btn)

        icon_btn_layout.addStretch()
        icon_btn_layout.setSpacing(5)
        icon_block_layout.addWidget(icon_btn_row)

        # -------- Row 2: entry + clear --------

        icon_entry_row = QWidget()
        icon_entry_layout = QHBoxLayout(icon_entry_row)
        icon_entry_layout.setContentsMargins(1,1,1,1)
        icon_entry_layout.setSpacing(1)

        self.icon_path_input = QLineEdit()
        self.icon_path_input.setPlaceholderText("No icon selected...")


        def clear_icon():
            self.icon_path_input.clear()
            self.icon_path = ""
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.icon_clear_btn = QPushButton("")
        self.icon_clear_btn.clicked.connect(clear_icon)
        
        
        icon_entry_layout.addWidget(self.icon_path_input)
        icon_entry_layout.addWidget(self.icon_clear_btn)
  
        icon_block_layout.addWidget(icon_entry_row)

        icon_frame_layout.addWidget(icon_block)
        self.main_layout.addWidget(icon_frame)
































































        # =============================================================
        # Output Folder
        # =============================================================

        output_block = QWidget()
        output_block_layout = QVBoxLayout(output_block)
        output_block_layout.setContentsMargins(3,3,3,3)
        output_block_layout.setSpacing(3)

        # =============================================================
        # Output FRAME (structured vertical)
        # =============================================================

        output_frame = QFrame()
        output_frame.setFrameShape(QFrame.StyledPanel)
        output_frame.setFrameShadow(QFrame.Raised)
        output_frame.setLineWidth(1)

        output_layout = QVBoxLayout(output_frame)
        output_layout.setContentsMargins(3,3,3,3)
        output_layout.setSpacing(3)

        # =================================================
        # Row 1: Select Output Folder button
        # =================================================

        self.output_btn = QPushButton("Select Output Folder")
        self.output_btn.clicked.connect(self.file_pickers.select_output_folder)

        output_layout.addWidget(self.output_btn, alignment=Qt.AlignLeft)

        # =================================================
        # Row 2: Status lines (stacked)
        # =================================================

        self.output_path_status_label = QLineEdit("EXE OUTPUT PATH NOT SET")
        self.exe_name_status_label = QLineEdit("EXE NAME NOT SET")
    
        output_layout.addWidget(self.output_path_status_label)
        output_layout.addWidget(self.exe_name_status_label)

        # =================================================
        # Row 3: Output path + reset
        # =================================================

        output_entry_row = QWidget()
        output_entry_layout = QHBoxLayout(output_entry_row)
        output_entry_layout.setContentsMargins(1,1,1,1)

        self.output_path_input = QLineEdit()
        self.output_path_input.setPlaceholderText("No output folder selected...")
        output_entry_layout.addWidget(self.output_path_input)

        def get_desktop_path():
            return os.path.join(os.path.expanduser("~"), "Desktop")

        def reset_output_to_desktop():
            desktop = get_desktop_path()
            self.output_path_input.setText(desktop)
            self.output_path = desktop
            self.state_ctrl.save_state()
            self.validator.update_build_button_state()

        self.output_refresh_btn = QPushButton("")
        self.output_refresh_btn.clicked.connect(reset_output_to_desktop)

        output_entry_layout.addWidget(self.output_refresh_btn)
        output_layout.addWidget(output_entry_row)

        # =================================================
        # Row 4: EXE name + reset (INSIDE FRAME)
        # =================================================

        exe_row = QWidget()
        exe_layout = QHBoxLayout(exe_row)
        exe_layout.setContentsMargins(1,1,1,1)

        self.exe_name_input = QLineEdit()
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

        self.refresh_btn = QPushButton("")
        self.refresh_btn.clicked.connect(reset_exe_name_from_script)
        
        exe_layout.addWidget(self.refresh_btn)
        output_layout.addWidget(exe_row)

        # =================================================
        # ADD FRAME (ONLY ONCE, AT THE VERY END)
        # =================================================

        self.main_layout.addWidget(output_frame)
        
        

                

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
                self.state_ctrl.save_state()

            self.validator.update_build_button_state()


        def on_script_path_change(text):
            if getattr(self, "_loading_state", False):
                return

            value = text.strip()

            if not value:
                self.entry_script = None
                self.project_root = None

                # ✅ clear dependent fields
                if hasattr(self, "output_path_input"):
                    self.output_path_input.clear()
                self.output_path = ""

                if hasattr(self, "exe_name_input"):
                    self.exe_name_input.clear()
                self.exe_name = ""

                self.state_ctrl.save_state()

            self.validator.update_build_button_state()

        def on_dependency_toggle(state):
            self.dependency_notice_enabled = bool(state)

            # -------------------------
            # ON → show popup
            # -------------------------
            if self.dependency_notice_enabled:
                script = self.script_path

                if script and os.path.isfile(script):
                    packages = self.validator.run_dependency_advisory(script)

                    if packages:
                        self.show_dependency_warning_popup(packages)

            # -------------------------
            # OFF → close popup
            # -------------------------
            else:
                if hasattr(self, "popup") and self.popup:
                    self.popup.close()

            self.state_ctrl.save_state()
                
        
        def on_tooltips_toggle(state):
            self.tooltips_enabled = bool(state)
            self.state_ctrl.save_state()

        self.dependency_notice.stateChanged.connect(on_dependency_toggle)
        self.tooltips_checkbox.stateChanged.connect(on_tooltips_toggle)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        # -----------------------------
        # CONNECT SIGNALS (PySide6)
        # -----------------------------

        self.exe_name_input.textChanged.connect(_on_exe_name_user_edit)
        self.exe_name_input.textChanged.connect(on_exe_name_change)

        self.script_path_input.textChanged.connect(on_script_path_change)

        self.output_path_input.textChanged.connect(
            lambda text: None if getattr(self, "_loading_state", False) else self.validator.update_build_button_state()
        )

        self.exe_name_input.textChanged.connect(
            lambda text: None if getattr(self, "_loading_state", False) else self.validator.update_build_button_state()
        )

        self.icon_path_input.textChanged.connect(
            lambda text: None if getattr(self, "_loading_state", False) else self.validator.update_build_button_state()
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
        build_layout.setSpacing(3)


        # =================================================
        # Row 1: Build button (centered)
        # =================================================

        self.build_btn = QPushButton("Build EXE")
        
        font = QFont("Rubik UI", 12, QFont.Bold)
        self.build_btn.setFont(font)
        self.build_btn.setFixedSize(125, 35)
        self.build_btn.clicked.connect(self.build_exe)

        build_layout.addWidget(self.build_btn, alignment=Qt.AlignLeft)

        # =================================================
        # Row 2: Status
        # =================================================

        self.status_label = QLineEdit("Ready")
        self.status_label.setFont(QFont("Rubik UI", 11))
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
        self.populate_recent_dropdown()
        self._loading_state = False
        self.validator.validation_status_message()
        self.validator.update_build_button_state()

        for refresh_btns in [
            self.refresh_btn,
            self.output_refresh_btn,
            self.icon_clear_btn,
            self.script_clear_btn
            
        ]:
            refresh_btns.setText("🔃")
            refresh_btns.setFixedSize(35,35)

        for output_paths in [
            self.python_entry_input,
            self.script_path_input,
            self.icon_path_input,
            self.output_path_input,
            self.exe_name_input,
        ]:
            output_paths.setReadOnly(True)
            output_paths.setFont(QFont("Rubik UI", 10))
    
        self.exe_name_input.setReadOnly(False)


        for btns in [
            self.open_python_site_btn,
            self.apps_btn,
            self.folder_btn,
            self.interpreter_btn,
            self.icon_btn,
            self.ico_convert_btn,
            self.output_btn,

            
        ]:
            
            btns.setStyleSheet("background-color: #494949")
            btns.setFont(QFont("Rubik UI", 11,))
            btns.setFixedSize(180,35)
        
        self.recent_folder_dropdown.setFixedSize(180,35)
            
        for labels in [
            self.script_folder_status_label,
            self.output_path_status_label,
            self.exe_name_status_label
            
            ]:
                labels.setReadOnly(True)
                labels.setFixedSize(200,35)
                labels.setFont(QFont("Rubik Ui", 11))
    
                
        self.python_status_label.setFixedSize(250,35)
        
    def add_recent_script(self, path):
        ap = os.path.abspath(os.path.normpath(path)) if path else ""
        if not ap:
            return

        state_path = self.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        lst = data.get("recent_scripts", [])

        if ap in lst:
            lst.remove(ap)

        lst.insert(0, ap)
        lst = lst[:10]

        data["recent_scripts"] = lst

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Recent scripts save error:", e)

        # 🔑 IMPORTANT: keep in-memory copy synced
        self.state_data = data
        
    def populate_recent_dropdown(self):
        def _abs(p):
            return os.path.abspath(os.path.normpath(p)) if p else ""

        self.recent_folder_dropdown.blockSignals(True)
        self.recent_folder_dropdown.clear()
        
        # 🔑 HEADER (non-clickable)
        self.recent_folder_dropdown.addItem("Select Recent File")
        model = self.recent_folder_dropdown.model()
        item = model.item(0)
        
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
       
        # 🔑 ALWAYS READ FROM FILE (source of truth)
        state_path = self.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        paths = data.get("recent_scripts", [])

        seen = set()

        for p in paths:
            ap = _abs(p)

            if not ap:
                continue
            if not os.path.isfile(ap):
                continue
            if ap in seen:
                continue

            seen.add(ap)

            name = os.path.basename(ap)
            parent = os.path.basename(os.path.dirname(ap))

            # 🔑 DISPLAY ONLY (no logic impact)
            display = f"{parent}\\{name}" if parent else name

            # 🔑 IMPORTANT: FULL PATH still stored
            self.recent_folder_dropdown.addItem(display, ap)

        self.recent_folder_dropdown.blockSignals(False)
                
    def on_recent_file_selected(self, index):
        if index < 0:
            return

        path = self.recent_folder_dropdown.currentData()

        if not path:
            return

        path = os.path.abspath(os.path.normpath(path))

        print("Selected:", path)

        # 🔑 USE SAME PIPELINE AS EVERYTHING ELSE
        if hasattr(self, "file_pickers"):
            self.file_pickers._apply_selected_entry(path)
            
    def confirm_delete_recent(self):
        full_path = getattr(self, "entry_script", "") or getattr(self, "script_path", "")

        if not full_path:
            return

        reply = QMessageBox.question(
            self,
            "Delete Recent File",
            f"Are you sure you want to remove:\n\n{full_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if os.path.abspath(os.path.normpath(full_path)) == os.path.abspath(os.path.normpath(getattr(self, "entry_script", ""))):
            self.script_path_input.clear()
            self.entry_script = None
            self.project_root = None
            self.script_path = ""

        state_path = self.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        lst = data.get("recent_scripts", [])

        norm = os.path.abspath(os.path.normpath(full_path))
        lst = [p for p in lst if os.path.abspath(os.path.normpath(p)) != norm]

        data["recent_scripts"] = lst
        self.state_data = data

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.populate_recent_dropdown()
        
            

    def closeEvent(self, event):
        self.state_ctrl.save_state()

    # =============================================================
    # Dependency Popup (PySide6)
    # =============================================================

    def build_dependency_popup(self, packages: list[str]):
        if not packages:
            return None

        # close existing popup
        if hasattr(self, "popup") and self.popup:
            self.popup.close()

        popup = QDialog(self)
        popup.setFixedSize(300, 300)
        popup.setWindowTitle("Dependency Notice")
        popup.setModal(False)
        popup.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        layout = QVBoxLayout(popup)

        label1 = QLabel(
            "This script references the following external packages:"
        )
        label1.setWordWrap(True)
        label1.setFont(QFont("Rubik UI", 11, QFont.Bold))
        layout.addWidget(label1)

        pkg_text = ", ".join(packages)

        label2 = QLabel(pkg_text)
        label2.setWordWrap(True)
        label2.setFont(QFont("Rubik UI", 11, QFont.Bold))
        layout.addWidget(label2)

        label3 = QLabel(
            "Ensure they are installed in the selected Python environment. "
            "E.g. py -3.13 -m pip install <package-name>."
        )
        label3.setWordWrap(True)
        label3.setFont(QFont("Rubik UI", 11, QFont.Bold))
        layout.addWidget(label3)

        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(popup.close)
        layout.addWidget(ok_btn, alignment=Qt.AlignHCenter)

        # Position
        popup.adjustSize()
        x = self.x() + self.width() + 10
        y = self.y() + 50
        popup.move(x, y)

        self.popup = popup
        return popup
    
    def show_dependency_warning_popup(self, packages: list[str]):
        if not getattr(self, "dependency_notice_enabled", True):
            if hasattr(self, "popup") and self.popup:
                self.popup.close()
            return

        popup = self.build_dependency_popup(packages)

        if popup:
            popup.show()

        
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
        self.building = False  # kill any previous loop instantly
        self._eta_running = True
        self.state_ctrl.update_eta_loop()


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

        if self.build_process:
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

        script = os.path.normpath(script) if script else ""
        outdir = os.path.normpath(outdir) if outdir else ""
        icon = os.path.normpath(icon) if icon else ""

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
        if hasattr(self, "script_clear_btn"):
            self.script_clear_btn.setDisabled(True)
        self.build_btn.setText("Cancel EXE")
        self.build_btn.setStyleSheet("background-color: #d43c3c;")
        self.build_btn.clicked.disconnect()
        self.build_btn.clicked.connect(self.build_exe)
        self.status_label.setFixedWidth(425)
        


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
        
        
        # ⛔ move this OUT of thread (safe here)
        self.set_controls_enabled(False)
        
        def run_build(cmd):
            self.recent_folder_dropdown.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.exe_name_input.setReadOnly(False)
            
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

                # ✅ SAFE HANDOFF TO UI THREAD
                def on_complete():
                    if not self.building:
                        return

                    if ret == 0:
                        self.last_build_seconds = int(time.time() - self.build_start_time)
                        self.state_ctrl.save_state()

                        self.set_status("Build complete.")
                        QTimer.singleShot(5000, self.showMinimized)
                    else:
                        self.set_status("Build failed. See debug log.")
                
                
                self.refresh_btn.setEnabled(True)
                self.exe_name_input.setReadOnly(True)
                self._eta_running = False
                self.recent_folder_dropdown.setEnabled(True)
                self.build_btn.setText("Build EXE")
                self.build_btn.setStyleSheet("background-color: #3bbf3b;")
                self.set_status("Build complete." if ret == 0 else "Build failed. See debug log.")

                try:
                    self.build_btn.clicked.disconnect()
                except:
                    pass

                self.build_btn.clicked.connect(self.build_exe)
                                
                QTimer.singleShot(0, lambda: on_complete())  # ← SAFE

            finally:
                # ✅ SAFE UI CLEANUP
                def finalize_ui():
                    self.build_process = None
                    self.restore_build_ui()
                    
                QTimer.singleShot(0, lambda: finalize_ui())  # ← SAFE


        # ✅ THIS MUST BE RIGHT AFTER THE FUNCTION
        threading.Thread(
            target=run_build,
            args=(cmd,),
            daemon=True
        ).start()
        
        self.set_controls_enabled(True)
        self.validator.update_build_button_state()
            
    def ui_safe(self, fn):
        QTimer.singleShot(0, fn)



    def set_controls_enabled(self, enabled: bool):

        # 🔒 LOCK DURING BUILD
        locked_controls = [
            self.script_clear_btn,
            self.icon_clear_btn,
            self.output_refresh_btn,
            self.refresh_btn,   # exe name reset
        ]

        for btn in locked_controls:
            btn.setEnabled(enabled)
            
            


    # ==================================================
    # UI RESTORE: Build finished / aborted / cancelled
    # ==================================================

    def restore_build_ui(self):
        self.building = False
        self.set_controls_enabled(True)
        self._eta_running = False

        # -------------------------------
        # Restore Build buttonet_controls_enable
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
        # 🔑 FORCE validation AFTER unlock
        QTimer.singleShot(0, self.validator.update_build_button_state)


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
    app.setStyle("Fusion")
    
    palette = QPalette()   # ✅ MUST create instance
    
    palette.setColor(QPalette.Window, QColor(18, 18, 18))
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(35, 35, 35))

    palette.setColor(QPalette.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.WindowText, QColor(220, 220, 220))

    palette.setColor(QPalette.Button, QColor(60, 60, 60))
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))

    palette.setColor(QPalette.Highlight, QColor(80, 120, 200))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    

    app.setPalette(palette)
    
    app.setStyleSheet("""
    /* -----------------------------
    GLOBAL BACKGROUND
    ----------------------------- */
    QWidget {
        background-color: #121212;
        color: #e0e0e0;
        font-family: "Rubik UI";
    }
    /* -----------------------------
    CHECK BOXES(CONTRAST GREY)
    ----------------------------- */
    QCheckBox {
        background-color: #1c1c1c;
        border: 1px solid #1c1c1c;
        border-radius: 3px;
    }
    

    /* -----------------------------
    FRAMES (FORCE CONSISTENT GREY)
    ----------------------------- */
    QFrame {
        background-color: #1c1c1c;
        border: 1px solid #2e2e2e;
        border-radius: 6px;
    }

    /* 🔴 FORCE CHILDREN INSIDE FRAMES */
    QFrame QWidget {
        background-color: #1c1c1c;
    }

    /* subtle highlight edge */
    QFrame:hover {
        border: 1px solid #3a3a3a;
    }

    /* -----------------------------
    INPUT FIELDS
    ----------------------------- */
    QLineEdit {
        background-color: #252525;
        border: 1px solid #3a3a3a;
        padding: 6px;
        border-radius: 4px;
    }

    /* -----------------------------
    STATUS COLORS
    ----------------------------- */
    QLineEdit[readOnly="true"] {
        background-color: #202020;
    }

    /* -----------------------------
    BUTTONS
    ----------------------------- */
    QPushButton {
        background-color: #494949;
        border: 1px solid #3a3a3a;
        border-radius: 5px;
        padding: 6px;
    }

    QPushButton:hover {
        background-color: #5a5a5a;
    }

    QPushButton:pressed {
        background-color: #3f3f3f;
    }
    """)
    
    
    window = EXEBuilderApp()
    window.show()
    sys.exit(app.exec())