import os
import json
import time
import sys
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont

class StateController:
    def __init__(self, app):
        self.app = app
        self.last_build_counter = 0

    def _state_file_path(self) -> str:
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.abspath(".")
        return os.path.join(base_dir, "exe_builder_state.json")
    
    # ============================================================
    # ETA time estimator
    # ============================================================
    def update_eta_loop(self):
        if not getattr(self.app, "_eta_running", False):
            return

        if not getattr(self.app, "building", False):
            return

        
        elapsed = int(time.time() - self.app.build_start_time)
        est_total = self.app.last_build_seconds
        remaining = max(est_total - elapsed, 0)
            # 🔑 FORCE FONT EVERY TICK (kills jump)
        self.app.status_label.setFont(QFont("Rubik UI", 13, QFont.Bold))
        self.app.status_label.setText(
            f"Building... {elapsed}s elapsed\n — approx {remaining}s remaining"
        )
        self.app.status_label.setFixedSize(315,100)

        QTimer.singleShot(1, self.update_eta_loop)
        
    # ============================================================
    # LOAD
    # ============================================================
    def load_state(self):
        state_path = self._state_file_path()

        if not os.path.isfile(state_path):
            self.app.state_data = {"recent_scripts": []}
            return

        blocked_widgets = []

        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            def _norm(p):
                return os.path.normpath(p) if p else ""

            # keep full raw state in memory
            self.app.state_data = data

            # -------------------------
            # Block UI signals during hydrate
            # -------------------------
            for name in (
                "tooltips_checkbox",
                "dependency_notice",
                "script_path_input",
                "icon_path_input",
                "output_path_input",
                "exe_name_input",
                "python_entry_input",
            ):
                widget = getattr(self.app, name, None)
                if widget is not None:
                    widget.blockSignals(True)
                    blocked_widgets.append(widget)

            # -------------------------
            # Rehydrate app state FIRST
            # -------------------------
            self.app.tooltips_enabled = data.get("tooltips_enabled", True)
            self.app.dependency_notice_enabled = data.get("dependency_notice_enabled", True)

            self.app.script_path = _norm(data.get("last_script_path", ""))
            self.app.icon_path = _norm(data.get("last_icon_path", ""))
            self.app.output_path = _norm(data.get("last_output_folder", ""))
            self.app.python_interpreter_path = _norm(data.get("python_interpreter_path", ""))
            self.app.python_path = self.app.python_interpreter_path
            self.app.exe_name = data.get("last_exe_name", "")

            self.app.last_build_seconds = data.get("last_build_seconds", 45)
            self.app.last_build_counter = data.get("last_build_counter", 0)

            self.app.icon_user_cleared = data.get("icon_user_cleared", False)
            self.app.script_user_cleared = data.get("script_user_cleared", False)

            if self.app.python_interpreter_path:
                self.app.last_python_dir = os.path.dirname(self.app.python_interpreter_path)

            # -------------------------
            # Runtime rehydrate
            # -------------------------
            if self.app.script_path:
                self.app.entry_script = self.app.script_path
                self.app.project_root = os.path.dirname(self.app.script_path)
            else:
                self.app.entry_script = None
                self.app.project_root = None

            # -------------------------
            # Sync state -> UI
            # -------------------------
            if hasattr(self.app, "tooltips_checkbox"):
                self.app.tooltips_checkbox.setChecked(self.app.tooltips_enabled)

            if hasattr(self.app, "dependency_notice"):
                self.app.dependency_notice.setChecked(self.app.dependency_notice_enabled)

            if hasattr(self.app, "script_path_input"):
                self.app.script_path_input.setText(self.app.script_path)

            if hasattr(self.app, "icon_path_input"):
                self.app.icon_path_input.setText(self.app.icon_path)

            if hasattr(self.app, "output_path_input"):
                self.app.output_path_input.setText(self.app.output_path)

            if hasattr(self.app, "exe_name_input"):
                self.app.exe_name_input.setText(self.app.exe_name)

            if hasattr(self.app, "python_entry_input"):
                self.app.python_entry_input.setText(self.app.python_interpreter_path)

                
            self.app.validator.update_ui_state()

        except Exception as e:
            self.app.state_data = {"recent_scripts": []}
            print("State load error:", e)

        finally:
            for widget in blocked_widgets:
                widget.blockSignals(False)
    
    def save_state(self):
        def _norm(p):
            return os.path.normpath(p) if p else ""

        state_path = self._state_file_path()

        # preserve existing recent scripts from memory/file
        existing_data = {}

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
        except Exception:
            existing_data = {}

        recent_scripts = getattr(self.app, "state_data", {}).get(
            "recent_scripts",
            existing_data.get("recent_scripts", [])
        )
        
        recent_icons = getattr(self.app, "state_data", {}).get(
            "recent_icons",
            existing_data.get("recent_icons", [])
        )

        recent_interpreters =  getattr(self.app, "state_data", {}).get(
            "recent_interpreters",
            existing_data.get("recent_interpreters", [])
        )

        data = {
            "python_interpreter_path": _norm(
                getattr(self.app, "python_interpreter_path", "")
            ),

            "last_script_path": _norm(self.app.script_path),
            "last_icon_path": _norm(self.app.icon_path),
            "last_output_folder": _norm(self.app.output_path),
            "last_exe_name": self.app.exe_name,

            "recent_scripts": recent_scripts,
            "recent_icons": recent_icons,
            "recent_interpreters": recent_interpreters,

            "last_build_seconds": self.app.last_build_seconds,
            "last_build_counter": self.app.last_build_counter,

            "tooltips_enabled": getattr(self.app, "tooltips_enabled", True),
            "dependency_notice_enabled": getattr(self.app, "dependency_notice_enabled", True),

            "icon_user_cleared": getattr(self.app, "icon_user_cleared", False),
            "script_user_cleared": getattr(self.app, "script_user_cleared", False),
            }

        self.app.state_data = data

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("State save error:", e)