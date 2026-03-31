import sys
import os
import ctypes
import threading

from ctypes import wintypes
from build_controller import BuildController
from tooltips import attach_tooltips
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton,QFrame,QApplication,QHBoxLayout,QVBoxLayout,QCheckBox,QLineEdit,QHBoxLayout, QComboBox
from validation_controller import ValidationController
from activation_controller import ActivationController
from PySide6.QtGui import QFont, QPalette,QColor
from PySide6.QtWidgets import QSizePolicy
from file_pickers import FilePickerController
from state_controller import StateController
from recent_controller import RecentController
from ui_handlers import UIHandlers
from ui_dependency_popup import DependencyPopup
from json_import_controller import JsonImportController
from PySide6.QtGui import QFontMetrics

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
        self.building = False

        self.entry_script = None
        self.project_root = None
        self.exe_name_user_modified = False
        
        self.json_import_controller =JsonImportController(self)
        self.ui_dependency_popup = DependencyPopup(self)
        self.recent_controller = RecentController(self)
        self.ui_handlers = UIHandlers(self)
        self.build_controller = BuildController(self)
        self.validation_controller = ValidationController(self)
        self.state_ctrl = StateController(self)
        self.validator = ValidationController(self)
        self.activation_controller = ActivationController(self)
        self.file_pickers = FilePickerController(self)

        # ---------------------------------------------------------
        # SINGLE INSTANCE: Listen for activation events
        # ---------------------------------------------------------

        self.activate_event = ctypes.windll.kernel32.CreateEventW(None,False,False,"EXEBUILDER_ACTIVATE_EVENT")
        threading.Thread(target=self.activation_controller.listen_for_activation,daemon=True).start()

        # ---------------------------------------------------------
        # ALWAYS ON TOP
        # ---------------------------------------------------------

        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.build_process = None
        self.current_build_paths = []
        self.build_btn = None
        self.last_build_seconds = 45
        self.last_build_counter = 0
        
        self.setFixedSize(500, 985)
    

        self.tooltips_enabled = getattr(self, "tooltips_enabled", True)
        self.dependency_notice_enabled = getattr(self, "dependency_notice_enabled", True)
        self.script_path = getattr(self, "script_path", "")
        self.icon_path = getattr(self, "icon_path", "")
        self.output_path = getattr(self, "output_path", "")
        self.python_path = getattr(self, "python_path", "")
        self.exe_name = getattr(self, "exe_name", "")
                    
        # =============================================================
        # Title + Tooltip Toggle
        # =============================================================
        title_frame = QFrame()
        title_frame.setFrameShape(QFrame.StyledPanel)
        title_frame.setFrameShadow(QFrame.Raised)
        title_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(2,2,2,2)
        title_layout.setSpacing(2)

        title_label = QLabel(" Win 11 → Python → EXE Builder")
        title_label.setFont(QFont("Rubik UI", 15, QFont.Bold))
        title_label.setFixedSize(350,35)

        title_layout.addWidget(title_label)  
        title_layout.addStretch()

        # -------------------------------
        # TOGGLES FRAME
        # -------------------------------

        toggles_frame = QFrame()
        toggles_frame.setFixedSize(200,75)
        toggles_frame.setFrameShape(QFrame.StyledPanel)
        toggles_frame.setFrameShadow(QFrame.Raised)
        toggles_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


        toggles_layout = QVBoxLayout(toggles_frame)
        toggles_layout.setContentsMargins(5,5,5,5)
        toggles_layout.setSpacing(1)

        self.tooltips_checkbox = QCheckBox("Tooltips")
        self.dependency_notice = QCheckBox("Dependency Notice")

        for cb in [
            self.tooltips_checkbox,
            self.dependency_notice,
        ]:
            cb.setFixedSize(200,15)

        toggles_layout.addWidget(self.tooltips_checkbox)
        toggles_layout.addWidget(self.dependency_notice)

        # -------------------------------
        # WRAPPER (forces vertical alignment)
        # -------------------------------

        toggles_wrapper = QWidget()
        toggles_wrapper_layout = QVBoxLayout(toggles_wrapper)
        toggles_wrapper_layout.setContentsMargins(0,0,0,0)
        toggles_wrapper_layout.setSpacing(0)

        toggles_wrapper_layout.addStretch()  # 🔑 pushes toggles DOWN
        toggles_wrapper_layout.addWidget(toggles_frame, alignment=Qt.AlignLeft)

        # -------------------------------
        # MAIN LAYOUT
        # -------------------------------

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(1, 1, 1, 1)
        self.main_layout.setSpacing(2)
        self.main_layout.addWidget(title_frame, alignment= Qt.AlignCenter)

        # =============================================================
        # Script / Buttons Section
        # =============================================================

        row2 = QWidget(self)
        row2_layout = QVBoxLayout(row2)
        row2_layout.setContentsMargins(1,1,1,1)
        row2_layout.setSpacing(1)

        combined_frame = QFrame()
        combined_frame.setFrameShape(QFrame.StyledPanel)
        combined_frame.setFrameShadow(QFrame.Raised)

        combined_layout = QVBoxLayout(combined_frame)
        combined_layout.setContentsMargins(1,1,1,1)
        combined_layout.setSpacing(1)

        # =================================================
        # Apps TITLE FRAME
        # =================================================

        apps_title_frame = QFrame()
        apps_title_frame.setFrameShape(QFrame.StyledPanel)
        apps_title_frame.setFrameShadow(QFrame.Raised)
        apps_title_frame.setFixedHeight(40)

        apps_title_layout = QHBoxLayout(apps_title_frame)
        apps_title_layout.setContentsMargins(3,3,3,3)

        self.apps_title = QLabel("Apps Section")
        self.apps_title.setFont(QFont("Rubik UI", 14, QFont.Bold))

        apps_title_layout.addWidget(self.apps_title)
        apps_title_layout.addStretch()

        # =================================================
        # INLINE ROW (Apps title + toggles)
        # =================================================

        apps_toggles_row = QWidget()
        apps_toggles_layout = QHBoxLayout(apps_toggles_row)
        apps_toggles_layout.setContentsMargins(5,5,5,5)
        apps_toggles_layout.setSpacing(1)

        apps_toggles_layout.addWidget(apps_title_frame,alignment=Qt.AlignCenter | Qt.AlignBottom)
        apps_toggles_layout.addWidget(toggles_wrapper,alignment=Qt.AlignCenter | Qt.AlignBottom)

        # =================================================
        # Apps ROW (buttons)
        # =================================================

        apps_row = QWidget()
        apps_layout = QHBoxLayout(apps_row)
        apps_layout.setContentsMargins(1,1,1,1)
        apps_layout.setSpacing(1)

        self.open_python_site_btn = QPushButton("Python.org")
        apps_layout.addWidget(self.open_python_site_btn)
        apps_layout.addStretch()

        # =================================================
        # FINAL ATTACH
        # =================================================

        self.main_layout.addWidget(apps_toggles_row)   # ✅ inline row
        combined_layout.addWidget(apps_row)

        row2_layout.addWidget(combined_frame)
        self.main_layout.addWidget(row2)

        # =================================================
        # Interpreter (VERTICAL stack)
        # =================================================

        interpreter_container = QWidget()
        interpreter_layout = QVBoxLayout(interpreter_container)
        interpreter_layout.setContentsMargins(1,1,1,1)
        interpreter_layout.setSpacing(3)

        interpreter_btn_row = QWidget()
        interpreter_btn_layout = QHBoxLayout(interpreter_btn_row)
        interpreter_btn_layout.setContentsMargins(1,1,1,1)
        interpreter_btn_layout.setSpacing(3)
        self.interpreter_btn = QPushButton("Py Interpreter")
    
        self.select_interpreter = QComboBox()
        self.select_interpreter.setFixedSize(245,35)
        self.select_interpreter.setFont(QFont("Rubik UI", 12))

        # 🔑 Header
        self.select_interpreter.addItem("Select Recent Interpreter")
    
        model = self.select_interpreter.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

        # 🔑 Placeholder behavior
        self.select_interpreter.setEditable(True)
        self.select_interpreter.lineEdit().setReadOnly(True)
        self.select_interpreter.setEnabled(True)

        self.python_delete_interpreter = QPushButton("❌")
        self.python_delete_all_interpreter = QPushButton("💥")

        interpreter_btn_layout.addWidget(self.interpreter_btn)
        interpreter_btn_layout.addWidget(self.select_interpreter)
        interpreter_btn_layout.addWidget(self.python_delete_interpreter)
        interpreter_btn_layout.addWidget(self.python_delete_all_interpreter)
        interpreter_btn_layout.addStretch()

        interpreter_layout.addWidget(interpreter_btn_row)

        # --- Path row (input + refresh inline) ---
        interpreter_entry_row = QWidget()
        interpreter_entry_layout = QHBoxLayout(interpreter_entry_row)
        interpreter_entry_layout.setContentsMargins(3,3,3,3)
        interpreter_entry_layout.setSpacing(5)

        self.python_entry_input = QLineEdit()
        self.python_entry_input.setPlaceholderText("No python entry is selected.")

        self.interpreter_refresh_btn = QPushButton("🔃")
        self.interpreter_refresh_btn.setFixedSize(35,35)

        interpreter_entry_layout.addWidget(self.python_entry_input)
        interpreter_entry_layout.addWidget(self.interpreter_refresh_btn)
        interpreter_layout.addWidget(interpreter_entry_row)

        # --- Final attach ---
        self.main_layout.addWidget(apps_title_frame,alignment=Qt.AlignCenter)
        combined_layout.addWidget(apps_row)
        combined_layout.addWidget(interpreter_container)

        row2_layout.addWidget(combined_frame)
        self.main_layout.addWidget(row2)
 
        # =============================================================
        # Icon Picker
        # =============================================================

        icons_title_frame = QFrame()
        icons_title_frame.setFrameShape(QFrame.StyledPanel)
        icons_title_frame.setFrameShadow(QFrame.Raised)
  
        icons_title_layout = QHBoxLayout(icons_title_frame)
        icons_title_layout.setContentsMargins(3,3,3,3)
        icons_title_layout.setSpacing(3)

        self.icons_title = QLabel("Icons Section")
        self.icons_title.setFixedHeight(30)
        self.icons_title.setFont(QFont("Rubik UI", 14, QFont.Bold))

        icons_title_layout.addWidget(self.icons_title)
        icons_title_layout.addStretch()

        icon_frame = QFrame()
        icon_frame.setFrameShape(QFrame.StyledPanel)
        icon_frame.setFrameShadow(QFrame.Raised)

        icon_frame_layout = QVBoxLayout(icon_frame)
        icon_frame_layout.setContentsMargins(1,1,1,1)
        icon_frame_layout.setSpacing(1)

        icon_block = QWidget()
        icon_block_layout = QVBoxLayout(icon_block)
        icon_block_layout.setContentsMargins(1,1,1,1)
        icon_block_layout.setSpacing(1)

        # -------- Row 1: Select Icon + Recent Dropdown + Delete --------

        icon_row1 = QWidget()
        icon_row1_layout = QHBoxLayout(icon_row1)
        icon_row1_layout.setContentsMargins(1,1,1,1)
        icon_row1_layout.setSpacing(1)

        self.icon_btn = QPushButton("Select Ico (optional)")

        self.select_recent_icons = QComboBox()
        self.select_recent_icons.setFixedSize(245,35)
        self.select_recent_icons.setFont(QFont("Rubik UI", 12))
        self.select_recent_icons.addItem("Select Recent Icon")

        model = self.select_recent_icons.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

        # placeholder behavior
        self.select_recent_icons.setEditable(True)
        self.select_recent_icons.lineEdit().setReadOnly(True)
        self.select_recent_icons.setEnabled(True)

        self.delete_recent_icons = QPushButton("❌")
        self.delete_all_icons = QPushButton("💥")

        # -------- Row 2: ICO Converter (below) --------

        icon_row2 = QWidget()
        icon_row2_layout = QHBoxLayout(icon_row2)
        icon_row2_layout.setContentsMargins(1,1,1,1)
        icon_row2_layout.setSpacing(5)

        self.ico_convert_btn = QPushButton("Open ICO Convert")
        icon_row1_layout.addWidget(self.ico_convert_btn)
        icon_row1_layout.addStretch()
        icon_block_layout.addWidget(icon_row1)

        icon_row2_layout.addWidget(self.icon_btn)
        icon_row2_layout.addWidget(self.select_recent_icons)
        icon_row2_layout.addWidget(self.delete_recent_icons)
        icon_row2_layout.addWidget(self.delete_all_icons)
        icon_row2_layout.addStretch()
        icon_block_layout.addWidget(icon_row2)

        # -------- Row 3: Entry + Clear --------

        icon_entry_row = QWidget()
        icon_entry_layout = QHBoxLayout(icon_entry_row)
        icon_entry_layout.setContentsMargins(1,1,1,1)
        icon_entry_layout.setSpacing(5)

        self.icon_path_input = QLineEdit()
        self.icon_path_input.setPlaceholderText("icon_path_input")
        self.icon_clear_btn = QPushButton("")

        icon_entry_layout.addWidget(self.icon_path_input)
        icon_entry_layout.addWidget(self.icon_clear_btn)
        icon_block_layout.addWidget(icon_entry_row)
        
        icon_frame_layout.addWidget(icon_block)
        self.main_layout.addWidget(icons_title_frame,alignment=Qt.AlignCenter)
        self.main_layout.addWidget(icon_frame)

        # =================================================
        # PYTHON FILE TITLE FRAME
        # =================================================

        python_title_frame = QFrame()
        python_title_frame.setFrameShape(QFrame.StyledPanel)
        python_title_frame.setFrameShadow(QFrame.Raised)

        python_title_layout = QHBoxLayout(python_title_frame)
        python_title_layout.setContentsMargins(3,3,3,3)
        python_title_layout.setSpacing(3)

        self.python_title = QLabel("File Section")
        self.python_title.setFixedHeight(30)
        self.python_title.setFont(QFont("Rubik UI", 14, QFont.Bold))

        python_title_layout.addWidget(self.python_title)
        python_title_layout.addStretch()

        python_frame = QFrame()
        python_frame.setFrameShape(QFrame.StyledPanel)
        python_frame.setFrameShadow(QFrame.Raised)


        python_layout = QVBoxLayout(python_frame)
        python_layout.setContentsMargins(3,3,3,3)
        python_layout.setSpacing(3)

        # =================================================
        # Row 1: Select folder button + recent dropdown
        # =================================================

        self.folder_btn = QPushButton("Python File")
      
        self.recent_folder_dropdown = QComboBox()
        self.recent_folder_dropdown.setFixedSize(245, 35)
        self.recent_folder_dropdown.setFont(QFont("Rubik UI", 12))
        self.recent_folder_dropdown.addItem("Select Recent File")
        
        model = self.recent_folder_dropdown.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        
        self.recent_folder_dropdown.setEditable(True)
        self.recent_folder_dropdown.lineEdit().setReadOnly(True)
        self.recent_folder_dropdown.setEnabled(True)
        
        self.delete_recent_folder = QPushButton("❌")
        self.delete_all_folders = QPushButton("💥")
   
        folder_row = QHBoxLayout()
        folder_row.setContentsMargins(0, 0, 0, 0)
        folder_row.setSpacing(5)

        python_layout.addLayout(folder_row)

        # =================================================
        # Row 3: Path + clear (side-by-side)
        # =================================================

        script_row = QWidget()
        script_layout = QHBoxLayout(script_row)
        script_layout.setContentsMargins(3,3,3,3)
        script_layout.setSpacing(3)

        self.script_path_input = QLineEdit()

        self.script_path_input.setPlaceholderText("No python file has been selected.")
        script_layout.addWidget(self.script_path_input)

        self.script_clear_btn = QPushButton("")
        script_layout.addWidget(self.script_clear_btn)

        script_layout.setContentsMargins(1,1,1,1)
        python_layout.addWidget(script_row)
        self.main_layout.addWidget(python_title_frame,alignment=Qt.AlignCenter)
        self.main_layout.addWidget(python_frame)

        # =============================================================
        # Output Folder
        # =============================================================

        output_block = QWidget()
        output_block_layout = QVBoxLayout(output_block)
        output_block_layout.setContentsMargins(3,3,3,3)
        output_block_layout.setSpacing(3)

        # =================================================
        # OUTPUT TITLE FRAME
        # =================================================

        output_title_frame = QFrame()
        output_title_frame.setFrameShape(QFrame.StyledPanel)
        output_title_frame.setFrameShadow(QFrame.Raised)

        output_title_layout = QHBoxLayout(output_title_frame)
        output_title_layout.setContentsMargins(3,3,3,3)
        output_title_layout.setSpacing(3)

        self.output_title = QLabel("Output Section")
        self.output_title.setFixedHeight(30)
        self.output_title.setFont(QFont("Rubik UI", 14, QFont.Bold))

        output_title_layout.addWidget(self.output_title)
        output_title_layout.addStretch()

        output_frame = QFrame()
        output_frame.setFrameShape(QFrame.StyledPanel)
        output_frame.setFrameShadow(QFrame.Raised)

        output_layout = QVBoxLayout(output_frame)
        output_layout.setContentsMargins(3,3,3,3)
        output_layout.setSpacing(3)

        # =================================================
        # Row 1: Select Output Folder button
        # =================================================

        self.output_btn = QPushButton("Output Folder")

        self.date_time_dropdown = QComboBox()
        self.date_time_dropdown.setFixedSize(245, 35)
        self.date_time_dropdown.setFont(QFont("Rubik UI", 12))
        self.date_time_dropdown.addItem("Date Time Append")

        self.appened_py_version = QPushButton("Append Py Version")
        self.appened_py_version.setFixedSize(125,35)
        self.appened_py_version.setCheckable(True)

        self.appened_py_version.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: black;
                border: 1px solid #8a8a8a;
            }

            QPushButton:checked {
                background-color: #3bbf3b;
                color: black;
                border: 1px solid #2e9e2e;
            }

            QPushButton:pressed {
                background-color: #2e9e2e;
            }
            QPushButton:disabled {
                color: #7a7a7a;
                background-color: #d3d3d3;
                border: 1px solid #8a8a8a;
                            
            }
        """)
                
        self.date_time_dropdown.clear()

        def _add(label, data=None, enabled=True):
            self.date_time_dropdown.addItem(label, data)
            item = self.date_time_dropdown.model().item(self.date_time_dropdown.count() - 1)
            if not enabled:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

        # Header
        _add("Append Date/Time", None, enabled=False)

        _add("──────────", enabled=False)
        # Top option
        _add("None", None)

        # ISO
        _add("──────────", enabled=False)
        _add("ISO", enabled=False)
        _add("YYYY-MM-DD", "%Y-%m-%d")
        _add("YYYY-MM-DD_HH-MM", "%Y-%m-%d_%H-%M")

        # UK
        _add("──────────", enabled=False)
        _add("UK", enabled=False)
        _add("DD-MM-YYYY", "%d-%m-%Y")
        _add("DD-MM-YYYY_HH-MM", "%d-%m-%Y_%H-%M")

        # USA
        _add("──────────", enabled=False)
        _add("USA", enabled=False)
        _add("MM-DD-YYYY", "%m-%d-%Y")
        _add("MM-DD-YYYY_HH-MM", "%m-%d-%Y_%H-%M")

        model = self.date_time_dropdown.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        
        self.date_time_dropdown.setEditable(True)
        self.date_time_dropdown.lineEdit().setReadOnly(True)
        self.date_time_dropdown.setCurrentIndex(0)
        self.date_time_dropdown.setEnabled(True)
            
        row1 = QHBoxLayout()
        row1.setContentsMargins(1,1,1,1)
        row1.setSpacing(4)

        row1.addWidget(self.appened_py_version)
        row1.addStretch()

        row2 = QHBoxLayout()
        row2.setContentsMargins(1,1,1,1)
        row2.setSpacing(4)
        row2.addWidget(self.output_btn)
        row2.addWidget(self.date_time_dropdown)
        row2.addStretch()
    
        output_layout.addLayout(row1)
        output_layout.addLayout(row2)

        # =================================================
        # Row 2: Output path + reset
        # =================================================

        output_entry_row = QWidget()
        output_entry_layout = QHBoxLayout(output_entry_row)
        output_entry_layout.setContentsMargins(1,1,1,1)
        output_entry_layout.setSpacing(3)

        self.output_path_input = QLineEdit()
        self.output_path_input.setPlaceholderText("No output path selected.")
        output_entry_layout.addWidget(self.output_path_input)

        self.output_refresh_btn = QPushButton("")
        output_entry_layout.addWidget(self.output_refresh_btn)

        output_layout.addWidget(output_entry_row)
        # =================================================
        # Row 4: EXE name + reset
        # =================================================

        exe_row = QWidget()
        exe_layout = QHBoxLayout(exe_row)
        exe_layout.setContentsMargins(1,1,1,1)
        exe_layout.setSpacing(3)

        self.exe_name_input = QLineEdit()
        self.exe_name_input.setPlaceholderText("Exe has not been named.")
        exe_layout.addWidget(self.exe_name_input)

        self.refresh_btn = QPushButton("")
        exe_layout.addWidget(self.refresh_btn)

        output_layout.addWidget(exe_row)
        self.main_layout.addWidget(output_title_frame, alignment=Qt.AlignCenter)
        self.main_layout.addWidget(output_frame)
        
        # =============================================================
        # Build FRAME
        # =============================================================
        
        build_title_frame = QFrame()
        build_title_frame.setFrameShape(QFrame.StyledPanel)
        build_title_frame.setFrameShadow(QFrame.Raised)


        build_title_layout = QHBoxLayout(build_title_frame)
        build_title_layout.setContentsMargins(3,3,3,3)
        build_title_layout.setSpacing(3)

        self.build_title = QLabel("Build Section")
        self.build_title.setFixedHeight(30)
        self.build_title.setFont(QFont("Rubik UI", 14, QFont.Bold))

        build_title_layout.addWidget(self.build_title)
        build_title_layout.addStretch()

        build_frame = QFrame()
        build_frame.setFrameShape(QFrame.StyledPanel)
        build_frame.setFrameShadow(QFrame.Raised)
        build_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        build_layout = QVBoxLayout(build_frame)
        build_layout.setContentsMargins(5,5,5,5)
        build_layout.setSpacing(4)

        self.status_label = QLabel("Ready")
        self.status_label.setFixedSize(200,100)
        self.status_label.setFont(QFont("Rubik UI", 12, QFont.Bold))

        self.build_btn = QPushButton("Build EXE")
        self.build_btn.setFont(QFont("Rubik UI", 13, QFont.Bold))
        self.build_btn.setFixedSize(150, 35)
        self.build_btn.clicked.connect(self.build_controller.build_exe)

        build_layout.addWidget(self.status_label)
        build_layout.addWidget(self.build_btn, alignment=Qt.AlignCenter)

        self.main_layout.addWidget(build_title_frame, alignment= Qt.AlignCenter)

        for dropdowns in [
            self.date_time_dropdown,
            self.recent_folder_dropdown,
            self.select_recent_icons,
            self.select_interpreter,
        ]:
            dropdowns.setStyleSheet("""
                QComboBox {
                    background-color: #F3F2F2;   /* matches title frames */
                    color: #2a2a2a;              /* dark readable text */
                    border: 1px solid #8a8a8a;   /* soft grey border */
                    padding: 4px;
                }

                QComboBox::drop-down {
                    border: none;
                    background: #817E7E;
                }

                QComboBox QAbstractItemView {
                    background-color: #DCDBDB;   /* matches main frames */
                    color: #2a2a2a;
                    selection-background-color: #c6c6c6;  /* subtle highlight */
                    font-family: "Rubik UI";
                    font-size: 15px;
                    font-weight: bold;
                }

                QComboBox:disabled {
                    background-color: #e0e0e0;
                    color: #888;
                }
            """)

        frames = [
            combined_frame,
            interpreter_container,
            icon_frame,
            python_frame,
            output_frame,
            build_frame,
            toggles_frame,
        ]

        for frame in frames:
            if frame:
                frame.setStyleSheet("""
                    QFrame {
                        border: 2px solid #080B12;   /* thickness */
                        border-radius: 2px;
                        background-color:   #DCDBDB;
                    }
        """)
                
        frames = [
            title_frame,
            apps_title_frame,
            icons_title_frame,
            python_title_frame,
            output_title_frame,
            build_title_frame,
        ]

        for frame in frames:
            if frame:
                frame.setStyleSheet("""
                    QFrame {
                        border: 2px solid #080B12;   /* thickness */
                        border-radius: 2px;
                        background-color:   #F3F2F2;
                    }
        """)

        # -------------------------------
        # TITLE FRAMES — shrink to content
        # -------------------------------

        title_pairs = [
            (apps_title_frame, self.apps_title),
            (icons_title_frame, self.icons_title),
            (python_title_frame, self.python_title),
            (output_title_frame, self.output_title),
            (build_title_frame, self.build_title),
        ]

        for frame, label in title_pairs:
            if frame and label:
                fm = QFontMetrics(label.font())
                text_width = fm.horizontalAdvance(label.text())

                padding = 25 # space for margins + breathing room

                frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                frame.setMaximumHeight(40)
                frame.setFixedWidth(text_width + padding)

        # -------------------------------
        # INPUT DEFAULTS (placeholders + font)
        # -------------------------------

        inputs = [
            (self.exe_name_input, "Exe has not been named."),
            (self.python_entry_input, "No Python interpreter selected."),
            (self.icon_path_input, "No icon selected."),
            (self.output_path_input, "No output folder selected."),
            (self.script_path_input,"No python file has been selected.")
        ]

        font = QFont("Rubik UI", 11)
        font.setBold(True)

        for widget, text in inputs:
            if widget:
                widget.setPlaceholderText(text)
                widget.setFont(font)

        for checkbox in [
            self.tooltips_checkbox,
            self.dependency_notice
            
        ]:
            checkbox.setFont(QFont("Rubik Ui",12, QFont.Bold))
            checkbox.setChecked(True)
            checkbox.setFixedSize(185,35)

        for widget in [
            self.folder_btn,
            self.recent_folder_dropdown,
            self.delete_recent_folder,
            self.delete_all_folders,
            
        ]:  
            
            folder_row.addWidget(widget)
            
        folder_row.addStretch()

        for btns in [
            self.delete_recent_folder,
            self.delete_all_folders,
        ]:
            btns.setFixedSize(35,35)
            btns.setEnabled(True)

        for delete_btns in [
            self.delete_recent_icons,
            self.delete_recent_folder,
            self.delete_all_icons,
            self.delete_all_folders,
            self.python_delete_all_interpreter,
            self.python_delete_interpreter,
            
        ]:

            delete_btns.setFixedSize(35,35)
            delete_btns.setEnabled(True)
        
        for refresh_btns in [
            self.refresh_btn,
            self.output_refresh_btn,
            self.icon_clear_btn,
            self.script_clear_btn,
            self.interpreter_refresh_btn,
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
    
        self.exe_name_input.setReadOnly(False)

        for btns in [
            self.open_python_site_btn,
            self.appened_py_version, 
        ]:
            
            btns.setFont(QFont("Rubik UI", 11,QFont.Bold))
            btns.setFixedSize(160,35)

        for btns in [
            self.icon_btn,
            self.ico_convert_btn,
        ]:
            btns.setFont(QFont("Rubik UI",11, QFont.Bold))
            btns.setFixedSize(160,35)

        for btns in [
            self.interpreter_btn,
            self.folder_btn,
            self.output_btn

        ]:
            btns.setFixedSize(160,35)
            btns.setFont(QFont("Rubik Ui",11, QFont.Bold))
            font.setBold(True)
        
        self.recent_folder_dropdown.setFixedSize(245,35)
            
        for widget in [
            self.recent_folder_dropdown,
            self.select_recent_icons,
        ]:
            widget.setAcceptDrops(True)
            widget.installEventFilter(self)

        self.main_layout.addWidget(build_frame,alignment=Qt.AlignCenter)

        attach_tooltips(self)
        self._loading_state = False
        self.state_ctrl.load_state()
        self.recent_controller.populate_recent_dropdown()
        self.validator.validation_status_message()
        self.json_import_controller.attach()
        self.interpreter_btn.clicked.connect(self.file_pickers.select_python_interpreter)
        self.python_delete_interpreter.clicked.connect(self.recent_controller.interpreter_delete)
        self.select_interpreter.currentIndexChanged.connect(self.recent_controller.on_recent_interpreter_selected)
        self.python_delete_all_interpreter.clicked.connect(
            self.recent_controller.all_interpreter_delete
        )

        self.recent_controller.populate_recent_icons_dropdown()
        self.recent_folder_dropdown.currentIndexChanged.connect(self.recent_controller.on_recent_file_selected)
        self.delete_recent_folder.clicked.connect(self.recent_controller.confirm_delete_recent)
        self.delete_all_folders.clicked.connect(self.recent_controller.confirm_delete_all_folder)
        self.ico_convert_btn.clicked.connect(self.ui_handlers.open_icon_sites)

        self.open_python_site_btn.clicked.connect(self.ui_handlers.open_python_site)
        self.select_recent_icons.currentIndexChanged.connect(self.recent_controller.on_recent_icon_selected)
        self.delete_recent_icons.clicked.connect(self.recent_controller.confirm_delete_recent_icon)
        self.delete_all_icons.clicked.connect(self.recent_controller.confirm_delete_all_icons)

        self.date_time_dropdown.currentIndexChanged.connect(self.ui_handlers.on_datetime_format_changed)
        self.appened_py_version.toggled.connect(self.ui_handlers.on_append_py_version_toggle)
        self.recent_controller.populate_recent_interpreters_dropdown()
        self.interpreter_refresh_btn.clicked.connect(self.ui_handlers.clear_interpreter_path)
        self.icon_btn.clicked.connect(self.file_pickers.select_icon)
        self.icon_clear_btn.clicked.connect(self.ui_handlers.clear_icon)
        self.folder_btn.clicked.connect(self.file_pickers.select_script_folder)
        self.script_clear_btn.clicked.connect(self.ui_handlers.clear_script_path)
        self.output_btn.clicked.connect(self.file_pickers.select_output_folder)
        self.output_refresh_btn.clicked.connect(self.ui_handlers.reset_output_to_desktop)
        self.refresh_btn.clicked.connect(self.ui_handlers.reset_exe_name_from_script)
        self.dependency_notice.stateChanged.connect(self.ui_handlers.on_dependency_toggle)
        self.tooltips_checkbox.stateChanged.connect(self.ui_handlers.on_tooltips_toggle)
        self.exe_name_input.textChanged.connect(self.ui_handlers._on_exe_name_user_edit)
        self.exe_name_input.textChanged.connect(self.ui_handlers.on_exe_name_change)
        self.script_path_input.textChanged.connect(self.ui_handlers.on_script_path_change)

        self.validator.update_ui_state()

    def set_status(self, text):
        self.status_label.setText(text)

    def closeEvent(self, event):
        self.state_ctrl.save_state()

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

    palette = QPalette()

    # Main background (empty space / non-widget areas)
    palette.setColor(QPalette.Window, QColor("#949494"))

    app.setPalette(palette)

    window = EXEBuilderApp()
    window.show()
    sys.exit(app.exec())