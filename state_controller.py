import os
import json
import time
import sys

class StateController:
    def __init__(self, app):
        """
        app = EXEBuilderApp instance
        """
        self.app = app
        self.build_counter = 0
        
        
    def _state_file_path(self) -> str:
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)   # folder containing the EXE
        else:
            base_dir = os.path.abspath(".")              # project run dir (fine for script)
        return os.path.join(base_dir, "exe_builder_state.json")
        
    # ============================================================
    # ETA time estimator
    # ============================================================

    def update_eta_loop(self):
        if not self.app.building:
            return

        elapsed = int(time.time() - self.app.build_start_time)

        est_total = self.app.last_build_seconds
        remaining = max(est_total - elapsed, 0)

        self.app.status_label.configure(
            text=f"Building... {elapsed}s elapsed — approx {remaining}s remaining"
        )

        self.app.after(500, self.update_eta_loop)

    # ============================================================
    # JSON Save / Load
    # ============================================================

    def load_state(self):
        state_path = self._state_file_path()

        if not os.path.isfile(state_path):
            return

        try:
            with open(state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # -------------------------
            # Restore tooltip setting
            # -------------------------

            tooltips = data.get("tooltips_enabled", True)
            self.app.tooltips_enabled = tooltips
            self.app.tooltips_var.set(tooltips)


            # -------------------------
            # Restore StringVars
            # -------------------------

            script = data.get("last_script_path", "")
            self.app.script_path_var.set(script)

            icon = data.get("last_icon_path", "")
            icon_cleared = data.get("icon_user_cleared", False)

            if not icon_cleared and icon and os.path.isfile(icon):
                self.app.icon_path_var.set(icon)
            else:
                self.app.icon_path_var.set("")

            self.app.output_path_var.set(
                data.get("last_output_folder", "")
            )

            self.app.last_build_seconds = data.get(
                "last_build_seconds", 45
            )

            self.app.exe_name_var.set(
                data.get("last_exe_name", "")
            )

            # -------------------------
            # Python interpreter
            # -------------------------

            python_path = data.get("python_interpreter_path", "")
            if python_path and os.path.isfile(python_path):
                self.app.python_interpreter_path = python_path
                self.app.python_path_var.set(python_path)

            last_dir = data.get("last_python_dir", "")
            if last_dir and os.path.isdir(last_dir):
                self.app.last_python_dir = last_dir
                
            script = data.get("last_script_path", "")
            script_cleared = data.get("script_user_cleared", False)

            if not script_cleared and script and os.path.isfile(script):
                self.app.script_path_var.set(script)
            else:
                self.app.script_path_var.set("")

            # -------------------------
            # Rehydrate runtime state
            # -------------------------

            if script and os.path.isfile(script):
                self.app.entry_script = script
                self.app.project_root = os.path.dirname(script)
            else:
                self.app.entry_script = None
                self.app.project_root = None

        except Exception as e:
            print("State load error:", e)


    def save_state(self):
        data = {
            "last_script_path": self.app.script_path_var.get(),
            "last_icon_path": self.app.icon_path_var.get(),
            "last_output_folder": self.app.output_path_var.get(),
            "last_build_seconds": self.app.last_build_seconds,
            "build_counter": self.app.build_counter,
            "last_exe_name": self.app.exe_name_var.get(),
            "icon_user_cleared": getattr(self.app, "icon_user_cleared", False),
            "script_user_cleared": getattr(self.app, "script_user_cleared", False),
            "python_interpreter_path": getattr(self.app, "python_interpreter_path", ""),
            "tooltips_enabled": getattr(self.app, "tooltips_enabled", True),
            "recent_scripts": []
        }

        state_path = self._state_file_path()

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("State save error:", e)
            