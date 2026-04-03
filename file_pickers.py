import os
import subprocess
from PySide6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QPushButton, QLabel, QComboBox, QVBoxLayout, QPushButton,QFrame
from PySide6.QtCore import Qt

# -------------------------------------------------------------
# File Pickers (Qt version)
# -------------------------------------------------------------

class FilePickerController:
    def __init__(self, app):
        """
        app = EXEBuilderApp instance
        """
        self.app = app

    def _derive_exe_name_from_script(self, script_path):
        return os.path.splitext(os.path.basename(script_path))[0]

    # ============================================================
    # Locate python installs
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
    # Select python interpreter
    # ============================================================
    def select_python_interpreter(self):
        start_dir = self._resolve_python_start_dir() or os.path.expanduser("~")

        path, _ = QFileDialog.getOpenFileName(
            self.app,
            "Select Python Interpreter",
            start_dir,
            "Python Interpreter (python.exe)"
        )

        if not path:
            return

        # 🔑 NORMALIZE
        path = os.path.normpath(path)

        # ✅ SINGLE SOURCE OF TRUTH (current)
        self.app.python_interpreter_path = path
        self.app.python_path = path

        # ✅ UI update
        if hasattr(self.app, "python_entry_input"):
            self.app.python_entry_input.setText(path)

        # 🔑 ADD → recents system
        if hasattr(self.app, "recent_controller"):
            self.app.recent_controller.add_recent_interpreter(path)
            self.app.recent_controller.populate_recent_interpreters_dropdown()

        # remember last dir
        self.app.last_python_dir = os.path.dirname(path)

        # persist
        if hasattr(self.app, "state_ctrl"):
            self.app.state_ctrl.save_state()

        # refresh validation
        if hasattr(self.app, "validator"):
            self.app.validator.validation_status_message()
            self.app.validator.update_ui_state()

        self.app.state_ctrl.save_state()
            
    def _resolve_python_start_dir(self):
        """Best directory to open the interpreter picker in."""

        # 1️⃣ Last-used interpreter directory (preferred)
        last_dir = getattr(self.app, "last_python_dir", "")
        last_dir = os.path.normpath(last_dir) if last_dir else ""

        if last_dir and os.path.isdir(last_dir):
            return last_dir

        # 2️⃣ Use `where python` as a hint
        candidates = self._get_where_python_dirs()
        for path in candidates:
            if "WindowsApps" not in path:
                path = os.path.normpath(path)
                return os.path.dirname(path)

        return None

    # ============================================================
    # Select single script
    # ============================================================

    def select_script(self):
        path, _ = QFileDialog.getOpenFileName(
            self.app,
            "Select Python Script",
            "",
            "Python Files (*.py)"
        )

        if not path:
            return

        path = os.path.normpath(path)

        # 🔑 SINGLE SOURCE OF TRUTH
        self._apply_selected_entry(path)

    # ============================================================
    # Select script folder
    # ============================================================

    def select_script_folder(self):

        start_dir = None

        # 1️⃣ Existing project root
        if getattr(self.app, "project_root", None):
            root = os.path.normpath(self.app.project_root)
            if os.path.isdir(root):
                start_dir = root

        # 2️⃣ Last selected script path
        elif getattr(self.app, "script_path", ""):
            script = os.path.normpath(self.app.script_path)
            if os.path.isfile(script):
                start_dir = os.path.dirname(script)

        # 3️⃣ Fallback: Desktop
        if not start_dir:
            start_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        folder = QFileDialog.getExistingDirectory(
            self.app,
            "Select Python Folder",
            start_dir
        )

        if not folder:
            return

        folder = os.path.normpath(folder)

        py_files = [
            f for f in os.listdir(folder)
            if f.endswith(".py") and os.path.isfile(os.path.join(folder, f))
        ]

        if not py_files:
            return

        # Single-file shortcut
        if len(py_files) == 1:
            full_path = os.path.join(folder, py_files[0])
            full_path = os.path.normpath(full_path)
            self._apply_selected_entry(full_path)
            return

        # Multi-file → popup
        popup = ScriptPickerPopup(
            parent=self.app,
            folder_path=folder,
            py_files=py_files,
            callback=self._apply_selected_entry
        )
        popup.exec()

    # ============================================================
    # Apply selected entry
    # ============================================================
    def _apply_selected_entry(self, full_path):
        """Callback from ScriptPickerPopup"""

        # 🔑 NORMALIZE
        full_path = os.path.normpath(full_path)

        # ------------------------------------
        # Capture previous state BEFORE change
        # ------------------------------------

        previous_script = getattr(self.app, "entry_script", "")
        previous_exe_name = getattr(self.app, "exe_name", "").strip()

        # ------------------------------------
        # Apply new script selection
        # ------------------------------------

        self.app.entry_script = full_path
        
        if hasattr(self.app, "script_path_input"):
            parent = os.path.basename(os.path.dirname(full_path))
            name = os.path.basename(full_path)

            display = os.path.normpath(full_path)

            self.app.script_path_input.setText(display)
            self.app.script_path_input.setCursorPosition(len(display))

        self.app.project_root = os.path.dirname(full_path)
        self.app.script_path = full_path

        # ------------------------------------
        # Auto-update EXE name ONLY if safe
        # ------------------------------------

        old_derived = ""
        if previous_script:
            previous_script = os.path.normpath(previous_script)
            old_derived = os.path.splitext(os.path.basename(previous_script))[0]

        new_derived = os.path.splitext(os.path.basename(full_path))[0]

        if not previous_exe_name or previous_exe_name in {
            old_derived,
            new_derived
        }:
            self.app.exe_name = new_derived

            if hasattr(self.app, "exe_name_input"):
                self.app.exe_name_input.setText(new_derived)

      
        # ------------------------------------
        # Persist + revalidate
        # ------------------------------------

        self.app.recent_controller.add_recent_script(full_path)
        self.app.recent_controller.populate_recent_dropdown()

        self.app.state_ctrl.save_state()
        self.app.validator.validation_status_message()
        self.app.validator.update_ui_state()
        
    def _apply_selected_icon(self, full_path):
    # 🔑 NORMALIZE
        full_path = os.path.normpath(full_path)

        # ------------------------------------
        # Apply new icon selection
        # ------------------------------------

        self.app.icon_path = full_path

        if hasattr(self.app, "icon_path_input"):
            display = os.path.normpath(full_path)
            self.app.icon_path_input.setText(display)
            self.app.icon_path_input.setCursorPosition(len(display))

        # ------------------------------------
        # Persist + revalidate (MATCH SCRIPT)
        # ------------------------------------

        self.app.recent_controller.add_recent_icon(full_path)
        self.app.recent_controller.populate_recent_icons_dropdown()

        self.app.state_ctrl.save_state()
        self.app.validator.validation_status_message()
        self.app.validator.update_ui_state()

    # ============================================================
    # Select icon
    # ============================================================

    def select_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self.app,
            "Select Icon",
            "",
            "ICON Files (*.ico)"
        )

        if path:
            # 🔑 NORMALIZE
            path = os.path.normpath(path)

            self.app.icon_path = path

            # ✅ update UI
            if hasattr(self.app, "icon_path_input"):
                self.app.icon_path_input.setText(path)
                
            self.app.recent_controller.add_recent_icon(path)
            self.app.recent_controller.populate_recent_icons_dropdown()


            self.app.state_ctrl.save_state()
            self.app.validator.validation_status_message()
            self.app.validator.update_ui_state()

    # ============================================================
    # Select output folder
    # ============================================================
    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self.app,
            "Select Output Folder",
            getattr(self.app, "last_output_dir", "")
        )

        if not folder:
            return

        # 🔑 NORMALIZE
        folder = os.path.normpath(folder)

        # optional alias
        self.app.output_path = folder

        # remember last location
        self.app.last_output_dir = folder

        if hasattr(self.app, "output_path_input"):
            self.app.output_path_input.setText(folder)

        # Auto-derive exe name ONLY if empty
        if not getattr(self.app, "exe_name", "").strip():
            script = getattr(self.app, "entry_script", "") or getattr(self.app, "script_path", "")
            if script:
                script = os.path.normpath(script)
                base = os.path.splitext(os.path.basename(script))[0]
                self.app.exe_name = base

                if hasattr(self.app, "exe_name_input"):
                    self.app.exe_name_input.setText(base)

        self.app.state_ctrl.save_state()
        self.app.validator.validation_status_message()
        self.app.validator.update_ui_state()
    
class ScriptPickerPopup(QDialog):
    def __init__(self, parent, folder_path, py_files, callback):
        super().__init__(parent)

        self.setWindowTitle("Select Entry Script")
        self.setFixedSize(300, 200)

        # 🔑 NORMALIZE
        self.folder_path = os.path.normpath(folder_path)

        self.callback = callback

        # -------------------------------------------------------------
        # Position: snap to right side of parent
        # -------------------------------------------------------------

        parent_geom = parent.geometry()
        x = parent_geom.x() + parent_geom.width()
        y = parent_geom.y()

        self.move(x, y)

    # -------------------------------------------------------------
        # Layout
        # -------------------------------------------------------------

        layout = QVBoxLayout(self)

        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.frame.setLineWidth(1)

        self.frame.setStyleSheet("""
            QFrame {
                border: 2px solid #080B12;
                border-radius: 6px;
                background-color: #DCDBDB;
            }
        """)

        frame_layout = QVBoxLayout(self.frame)
        frame_layout.setContentsMargins(8, 8, 8, 8)
        frame_layout.setSpacing(6)

        label = QLabel("Select the script\nthat starts your program:")
        label.setWordWrap(True)
        label.setStyleSheet("""
            font-family: "Rubik";
            font-size: 13px;
            font-weight: bold;
        """)
        frame_layout.addWidget(label, alignment=Qt.AlignHCenter)

        self.dropdown = QComboBox()
        self.dropdown.addItems(py_files)
        self.dropdown.setStyleSheet("""
            font-family: "Rubik";
            font-size: 13px;
        """)
        frame_layout.addWidget(self.dropdown, alignment=Qt.AlignHCenter)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setFixedWidth(120)
        confirm_btn.clicked.connect(self.confirm)
        confirm_btn.setStyleSheet("""
            font-family: "Rubik";
            font-size: 13px;
            font-weight: bold;
        """)
        frame_layout.addWidget(confirm_btn, alignment=Qt.AlignHCenter)

        layout.addWidget(self.frame, alignment=Qt.AlignHCenter)

    def confirm(self):
        selected_file = self.dropdown.currentText()

        full_path = os.path.join(self.folder_path, selected_file)

        # 🔑 NORMALIZE
        full_path = os.path.normpath(full_path)

        # Return selection
        self.callback(full_path)

        self.accept()