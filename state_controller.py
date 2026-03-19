import os
import json
import time
import sys
from pathlib import Path
from PySide6.QtCore import QTimer


class StateController:
    def __init__(self, app):
        self.app = app
        self.build_counter = 0

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

        self.app.status_label.setText(
            f"Building... {elapsed}s elapsed — approx {remaining}s remaining"
        )

        QTimer.singleShot(500, self.update_eta_loop)
        

    # ============================================================
    # LOAD
    # ============================================================

    def load_state(self):
        state_path = self._state_file_path()

        if not os.path.isfile(state_path):
            return

        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # -------------------------
            # Tooltips
            # -------------------------
            tooltips = data.get("tooltips_enabled", True)
            self.app.tooltips_enabled = tooltips
            self.app.tooltips_checkbox.setChecked(tooltips)

            # -------------------------
            # Dependency Notice
            # -------------------------
            dependency = data.get("dependency_notice_enabled", True)
            self.app.dependency_notice_enabled = dependency
            self.app.dependency_notice.setChecked(dependency)

            # -------------------------
            # Core paths (NORMALIZED)
            # -------------------------
            def _norm(p):
                return os.path.normpath(p) if p else ""

            script = _norm(data.get("last_script_path", ""))
            icon = _norm(data.get("last_icon_path", ""))
            output = _norm(data.get("last_output_folder", ""))

            self.app.script_path = script if os.path.isfile(script) else ""
            self.app.icon_path = icon if os.path.isfile(icon) else ""
            self.app.output_path = output if os.path.isdir(output) else ""

            # -------------------------
            # Build info
            # -------------------------
            self.app.last_build_seconds = data.get("last_build_seconds", 45)
            self.app.build_counter = data.get("build_counter", 0)
            self.app.exe_name = data.get("last_exe_name", "")

            # -------------------------
            # Flags
            # -------------------------
            self.app.icon_user_cleared = data.get("icon_user_cleared", False)
            self.app.script_user_cleared = data.get("script_user_cleared", False)
            
            if self.app.output_path:
                if hasattr(self.app, "output_path_input"):
                    self.app.output_path_input.setText(self.app.output_path)

            # -------------------------
            # Python interpreter
            # -------------------------
            python_path = _norm(data.get("python_interpreter_path", ""))
            if python_path and os.path.isfile(python_path):
                self.app.python_interpreter_path = python_path
                
            # -------------------------
            # Push into UI (CRITICAL)
            # -------------------------
            if python_path and os.path.isfile(python_path):
                if hasattr(self.app, "python_entry_input"):
                    self.app.python_entry_input.setText(python_path)
                    
            # -------------------------
            # Push script into UI
            # -------------------------
            if self.app.script_path:
                if hasattr(self.app, "script_path_input"):
                    self.app.script_path_input.setText(self.app.script_path)
                    
            if self.app.exe_name:
                if hasattr(self.app, "exe_name_input"):
                    self.app.exe_name_input.setText(self.app.exe_name)
                    
            # -------------------------
            # Push icon into UI
            # -------------------------
            if self.app.icon_path:
                if hasattr(self.app, "icon_path_input"):
                    self.app.icon_path_input.setText(self.app.icon_path)

            # -------------------------
            # Runtime rehydrate
            # -------------------------
            if self.app.script_path:
                self.app.entry_script = self.app.script_path
                self.app.project_root = os.path.dirname(self.app.script_path)
            else:
                self.app.entry_script = None
                self.app.project_root = None

        except Exception as e:
            print("State load error:", e)
            
            # -------------------------
            # PUSH ALL STATE → UI (ALWAYS)
            # -------------------------

            if hasattr(self.app, "exe_name_input"):
                self.app.exe_name_input.setText(self.app.exe_name or "")

            if hasattr(self.app, "icon_path_input"):
                self.app.icon_path_input.setText(self.app.icon_path or "")

            if hasattr(self.app, "script_path_input"):
                self.app.script_path_input.setText(self.app.script_path or "")

            # 🔑 ONLY validate if not loading
            if hasattr(self.app, "validator") and not self.app._loading_state:
                self.app.validator.update_build_button_state()
    

    def save_state(self):
        def _norm(p):
            return os.path.normpath(p) if p else ""

        data = {
            "last_script_path": _norm(self.app.script_path),
            "last_icon_path": _norm(self.app.icon_path),
            "last_output_folder": _norm(self.app.output_path),
            "last_build_seconds": self.app.last_build_seconds,
            "build_counter": self.app.build_counter,
            "last_exe_name": self.app.exe_name,
            "icon_user_cleared": getattr(self.app, "icon_user_cleared", False),
            "script_user_cleared": getattr(self.app, "script_user_cleared", False),
            "python_interpreter_path": _norm(getattr(self.app, "python_interpreter_path", "")),
            "tooltips_enabled": getattr(self.app, "tooltips_enabled", True),
            "dependency_notice_enabled": getattr(self.app, "dependency_notice_enabled", True),
            "recent_scripts": []
        }

        state_path = self._state_file_path()

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("State save error:", e)