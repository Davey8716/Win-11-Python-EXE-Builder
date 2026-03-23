import sys
import os
import ctypes
import threading

from ctypes import wintypes
from build_controller import BuildController
from tooltips import attach_tooltips
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton,QFrame,QApplication,QHBoxLayout,QVBoxLayout,QCheckBox,QLineEdit,QHBoxLayout, QComboBox
from validation_controller import ValidationController
from activation_controller import ActivationController
from PySide6.QtGui import QPalette, QColor,QFont
from file_pickers import FilePickerController
from state_controller import StateController
from recent_controller import RecentController
from ui_handlers import UIHandlers
from ui_dependency_popup import DependencyPopup
from build_ui_controller import BuildUIController
from json_import_controller import JsonImportController
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
        
        self.json_import_controller =JsonImportController(self)
        self.build_ui_controller = BuildUIController(self)
        self.ui_dependency_popup = DependencyPopup(self)
        self.recent_controller = RecentController(self)
        self.ui_handlers = UIHandlers(self)
        self.build_controller = BuildController(self)
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
        self.setFixedSize(500, 790)

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
        # Script / Buttons Section
        # =============================================================
        
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
        self.open_python_site_btn.clicked.connect(self.ui_handlers.open_python_site)

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
        self.interpreter_btn = QPushButton("Select Py Interpreter")
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
        self.recent_folder_dropdown.setFont(QFont("Rubik UI", 12))
        self.recent_folder_dropdown.addItem("Select Recent File")
        
        model = self.recent_folder_dropdown.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        
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
            
        self.delete_recent_folder = QPushButton("❌")
        self.delete_all_folders = QPushButton("💥")
   
        for btns in [
            self.delete_recent_folder,
            self.delete_all_folders
            
            
        ]:
            btns.setFixedSize(35,35)
            btns.setEnabled(True)

        folder_row = QHBoxLayout()
        folder_row.setContentsMargins(0, 0, 0, 0)
        folder_row.setSpacing(5)

        for widget in [
            self.folder_btn,
            self.recent_folder_dropdown,
            self.delete_recent_folder,
            self.delete_all_folders,
            
        ]:
            folder_row.addWidget(widget)
            
        folder_row.addStretch()
        
        self.recent_folder_dropdown.currentIndexChanged.connect(self.recent_controller.on_recent_file_selected)
        self.delete_recent_folder.clicked.connect(self.recent_controller.confirm_delete_recent)
        self.delete_all_folders.clicked.connect(self.recent_controller.confirm_delete_all_folder)
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

        self.script_clear_btn = QPushButton("")
        self.script_clear_btn.clicked.connect(self.ui_handlers.clear_script_path)
        
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
        icon_block_layout.setSpacing(3)

        # -------- Row 1: Select Icon + Recent Dropdown + Delete --------

        icon_row1 = QWidget()
        icon_row1_layout = QHBoxLayout(icon_row1)
        icon_row1_layout.setContentsMargins(1,1,1,1)
        icon_row1_layout.setSpacing(5)

        self.icon_btn = QPushButton("Select Icon (optional)")
        self.icon_btn.clicked.connect(self.file_pickers.select_icon)

        self.select_recent_icons = QComboBox()
        self.select_recent_icons.setFixedSize(180,35)
        self.select_recent_icons.setFont(QFont("Rubik UI", 11))
        self.select_recent_icons.addItem("Select Recent Icon")
        self.recent_controller.populate_recent_icons_dropdown()

        model = self.select_recent_icons.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

        # placeholder behavior
        self.select_recent_icons.setEditable(True)
        self.select_recent_icons.lineEdit().setReadOnly(True)
        if self.select_recent_icons.setEnabled(True):
            self.select_recent_icons.setStyleSheet("""
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
            """)

        self.delete_recent_icons = QPushButton("❌")
        self.delete_all_icons = QPushButton("💥")

        for stuff in [
            self.delete_recent_icons,
            self.delete_recent_folder,
            self.delete_all_icons,
            self.delete_all_folders,
            
        ]:
            stuff.setStyleSheet("""
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
            
            stuff.setFixedSize(35,35)
            stuff.setEnabled(True)

        icon_row1_layout.addWidget(self.icon_btn)
        icon_row1_layout.addWidget(self.select_recent_icons)
        icon_row1_layout.addWidget(self.delete_recent_icons)
        icon_row1_layout.addWidget(self.delete_all_icons)
        icon_row1_layout.addStretch()

        icon_block_layout.addWidget(icon_row1)

        # -------- Row 2: ICO Converter (below) --------

        icon_row2 = QWidget()
        icon_row2_layout = QHBoxLayout(icon_row2)
        icon_row2_layout.setContentsMargins(1,1,1,1)
        icon_row2_layout.setSpacing(5)

        self.ico_convert_btn = QPushButton("Open ICO Converters")
        self.ico_convert_btn.clicked.connect(self.ui_handlers.open_icon_sites)

        icon_row2_layout.addWidget(self.ico_convert_btn)
        icon_row2_layout.addStretch()
        icon_block_layout.addWidget(icon_row2)

        # -------- Row 3: Entry + Clear --------

        icon_entry_row = QWidget()
        icon_entry_layout = QHBoxLayout(icon_entry_row)
        icon_entry_layout.setContentsMargins(1,1,1,1)
        icon_entry_layout.setSpacing(5)

        self.icon_path_input = QLineEdit()
        self.icon_path_input.setPlaceholderText("No icon selected...")

        self.icon_clear_btn = QPushButton("")
        self.icon_clear_btn.clicked.connect(self.ui_handlers.clear_icon)

        icon_entry_layout.addWidget(self.icon_path_input)
        icon_entry_layout.addWidget(self.icon_clear_btn)

        icon_block_layout.addWidget(icon_entry_row)
        
        self.select_recent_icons.currentIndexChanged.connect(self.recent_controller.on_recent_icon_selected)
        self.delete_recent_icons.clicked.connect(self.recent_controller.confirm_delete_recent_icon)
        self.delete_all_icons.clicked.connect(self.recent_controller.confirm_delete_all_icons)

        # -------- Final --------

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

        self.output_refresh_btn = QPushButton("")
        self.output_refresh_btn.clicked.connect(self.ui_handlers.reset_output_to_desktop)

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

        self.refresh_btn = QPushButton("")
        self.refresh_btn.clicked.connect(self.ui_handlers.reset_exe_name_from_script)
        
        exe_layout.addWidget(self.refresh_btn)
        output_layout.addWidget(exe_row)

        # =================================================
        # ADD FRAME (ONLY ONCE, AT THE VERY END)
        # =================================================

        self.main_layout.addWidget(output_frame)
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
        self.build_btn.setFont(QFont("Rubik UI", 11))
        self.build_btn.setFixedSize(125, 35)
        self.build_btn.clicked.connect(self.build_controller.build_exe)

        build_layout.addWidget(self.build_btn, alignment=Qt.AlignLeft)

        # =================================================
        # Row 2: Status
        # =================================================

        self.status_label = QLineEdit("Ready")
        self.status_label.setFont(QFont("Rubik UI", 11))
        self.status_label.setReadOnly(True)
        build_layout.addWidget(self.status_label)
        
        
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
            btns.setFixedSize(160,35)
        
        self.recent_folder_dropdown.setFixedSize(180,35)
            
        for labels in [
            self.script_folder_status_label,
            self.output_path_status_label,
            self.exe_name_status_label
            
            ]:
                labels.setReadOnly(True)
                labels.setFixedSize(200,35)
                labels.setFont(QFont("Rubik Ui", 11))
                
         # Init values for the drag and drop functionality
        for widget in [
            self.recent_folder_dropdown,
            self.select_recent_icons,
        ]:
            widget.setAcceptDrops(True)
            widget.installEventFilter(self)

        # =================================================
        # ADD FRAME
        # =================================================

        self.main_layout.addWidget(build_frame)

        # ----------------------------------------------------
        # Initial validation pass
        # ----------------------------------------------------

        attach_tooltips(self)
        
        self.state_ctrl.load_state()
        self.recent_controller.populate_recent_dropdown()
        self._loading_state = False
        self.validator.validation_status_message()
        self.validator.update_build_button_state()

            
        self.json_import_controller.attach()
    
                
        self.python_status_label.setFixedSize(250,35)
        
        self.dependency_notice.stateChanged.connect(self.ui_handlers.on_dependency_toggle)
        self.tooltips_checkbox.stateChanged.connect(self.ui_handlers.on_tooltips_toggle)
        self.exe_name_input.textChanged.connect(self.ui_handlers._on_exe_name_user_edit)
        self.exe_name_input.textChanged.connect(self.ui_handlers.on_exe_name_change)
        self.script_path_input.textChanged.connect(self.ui_handlers.on_script_path_change)

        for widget in [
            self.output_path_input,
            self.exe_name_input,
            self.icon_path_input,
        ]:
            widget.textChanged.connect(
                lambda text: None if getattr(self, "_loading_state", False) else self.validator.update_build_button_state()
            )
                



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