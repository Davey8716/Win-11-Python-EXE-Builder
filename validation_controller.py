import os
import sys
import ast
from PySide6.QtCore import QTimer,Qt
from PySide6.QtCore import QThread
from PySide6.QtCore import QObject, Signal

class DependencyWorker(QObject):
    finished = Signal(dict)  # returns packages dict

    def __init__(self, controller, entry_file):
        super().__init__()
        self.controller = controller
        self.entry_file = entry_file

    def run(self):
        try:
            result = self.controller.run_dependency_advisory(self.entry_file)
        except Exception:
            result = {"external": [], "maybe": [], "uncertain": []}

        self.finished.emit(result)


class ValidationController:
    def __init__(self, app):
        """
        app = EXEBuilderApp instance
        """
        self.app = app

    def extract_imports_from_file(self, py_file: str) -> set[str]:
        imports = set()

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=py_file)
        except Exception:
            return imports  # advisory only

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        return imports

    def filter_external_imports(self, imports: set[str]) -> list[str]:
        stdlib = set(sys.stdlib_module_names)
        return sorted(i for i in imports if i not in stdlib)

    def run_dependency_advisory(self, entry_file: str) -> list[str]:
        root = os.path.dirname(os.path.normpath(entry_file))

        all_imports = set()
        local_modules = set()

        # -----------------------------
        # 1. collect local module names (recursive)
        # -----------------------------
        for root_dir, _, files in os.walk(root):
            for file in files:
                if file.endswith(".py"):
                    name = os.path.splitext(file)[0]
                    local_modules.add(name)

        # -----------------------------
        # 2. collect all imports (recursive)
        # -----------------------------
        for root_dir, _, files in os.walk(root):
            for file in files:
                if not file.endswith(".py"):
                    continue

                full_path = os.path.join(root_dir, file)

                if not os.path.isfile(full_path):
                    continue

                all_imports |= self.extract_imports_from_file(full_path)

        # -----------------------------
        # 3. classify imports
        # -----------------------------
        stdlib = set(sys.stdlib_module_names)

        external = []
        maybe = []
        uncertain = []

        for i in all_imports:
            if i in stdlib or i in local_modules:
                continue

            # simple heuristics
            if i.startswith("_"):
                uncertain.append(i)

            elif len(i) <= 3:
                uncertain.append(i)

            elif i in {"utils", "helpers", "common", "core"}:
                maybe.append(i)

            else:
                external.append(i)

        return {
            "external": sorted(external),
            "maybe": sorted(maybe),
            "uncertain": sorted(uncertain),
        }
            

    def set_build_error(self, message: str):
        self.app.build_error = message
        self.validation_status_message()
        self.app.validator.update_ui_state()

    
        
    # ==================================================
    # Can we build again?
    # =================================================
    
    def inputs_are_valid(self):
        script = self.app.script_path_input.text().strip()
        outdir = self.app.output_path_input.text().strip()
        exe_name = self.app.exe_name_input.text().strip()
        python = getattr(self.app, "python_interpreter_path", "").strip()
        
        # 🔑 NORMALIZE
        script = os.path.normpath(script) if script else ""
        outdir = os.path.normpath(outdir) if outdir else ""
        python = os.path.normpath(python) if python else ""

        if not python or not os.path.isfile(python):
            return False

        if not script or not os.path.isfile(script):
            return False

        if not outdir or not os.path.isdir(outdir):
            return False

        if not exe_name:
            return False

        return True
    
    def validation_status_message(self):

        script = os.path.normpath(self.app.script_path_input.text().strip() or "")
        outdir = os.path.normpath(self.app.output_path_input.text().strip() or "")
        exe_name = self.app.exe_name_input.text().strip()
        python = os.path.normpath(getattr(self.app, "python_interpreter_path", "") or "")
        icon_path = os.path.normpath(getattr(self.app, "icon_path", "").strip() or "")

        # -------------------------------
        # STATE
        # -------------------------------
        state = {}

        script_ok = bool(script and os.path.isfile(script))
        outdir_ok = bool(outdir and os.path.isdir(outdir))
        exe_ok = bool(exe_name)
        python_ok = bool(python and os.path.isfile(python))
        icon_ok = bool(icon_path and os.path.isfile(icon_path))

        state.update({
            "script_ok": script_ok,
            "outdir_ok": outdir_ok,
            "exe_ok": exe_ok,
            "python_ok": python_ok,
            "icon_ok": icon_ok,
            "output_ok": outdir_ok,
        })

        # -------------------------------
        # BUILD READINESS
        # -------------------------------
        is_ready = script_ok and outdir_ok and exe_ok and python_ok

        if getattr(self.app, "build_error", None):
            is_ready = False

        state["is_ready"] = is_ready

        # Reset popup eligibility when leaving READY state
        if not is_ready:
            self.app._dependency_popup_shown = False

        if not is_ready:
            self.app.status_label.setFixedSize(250,75)
        else:
            self.app.status_label.setFixedSize(250,75)

        # ==========================================================
        # Dependency advisory — fire ONCE when NOT READY → READY
        # ==========================================================
        if is_ready:
            current_script = script
            script_changed = current_script != self.app._last_advisory_script

            if script_changed:
                self.app._last_advisory_script = current_script

                if getattr(self.app, "dependency_notice_enabled", True):

                    # 🔑 HARD GUARD (prevents spam / freezing)
                    if current_script != getattr(self.app, "_dep_last_requested", None):
                        self.app._dep_last_requested = current_script

                        # 🔑 ASYNC ONLY (no blocking UI)
                        self.run_dependency_advisory_async(current_script)

                state["external_packages"] = []
            else:
                state["external_packages"] = []
        else:
            self.app._last_advisory_script = None

        # Track previous state
        self.app._was_build_ready = is_ready
                # Track previous state
        self.app._was_build_ready = is_ready
                
        # --------------------------------
        # STATUS TEXT
        # --------------------------------

        # Python version (Py 3.14)
        python_path = python
        python_version = "Unknown"
        if python_path:
            parent = os.path.basename(os.path.dirname(python_path))
            if parent.lower().startswith("python"):
                raw = parent.lower().replace("python", "")
                if raw.isdigit():
                    python_version = f"{raw[0]}.{raw[1:]}" if len(raw) > 1 else raw
                    
        # Icon (name or Default)
        icon_display = os.path.basename(icon_path) if icon_path else "Default - (No User Icon)"

        # Script (parent\file)
        script_display = "No script"
        if script:
            name = os.path.basename(script)
            parent = os.path.basename(os.path.dirname(script))
            script_display = f"{parent}\\{name}" if parent else name

        # EXE name
        exe_name_display = exe_name if exe_name else "No EXE name"

        # Output path
        outdir_display = outdir if outdir else "No output"
        error_msg = getattr(self.app, "build_error", None)
        
        if error_msg:
            state["status_text"] = error_msg
            is_ready = False  # 🔑 force red + stop READY logic
        state["status_text"] = (
            f"READY — Py {python_version} | {icon_display} |\n"
            f"{script_display} |\n"
            f"{outdir_display} |{exe_name_display}"
            
            if is_ready else
            (
                error_msg if error_msg else
                "NOT READY\n"
                "TO BUILD"
            )
        )
        
        return state

    def update_ui_state(self):
        app = self.app
        building = getattr(app, "building", False)

        # -------------------------------
        # INPUT STATES
        # -------------------------------
        script = getattr(app, "entry_script", "")
        script_ok = bool(script and os.path.isfile(script))

        outdir = app.output_path_input.text().strip()
        outdir = os.path.normpath(outdir) if outdir else ""

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")

        python_path = getattr(app, "python_interpreter_path", "").strip()
        python_ok = bool(python_path and os.path.isfile(python_path))

        icon_path = getattr(app, "icon_path", "").strip()
        icon_ok = bool(icon_path and os.path.isfile(icon_path))
        exe_name = app.exe_name_input.text().strip()

        python_path = getattr(app, "python_interpreter_path", "").strip()
        interpreter_ok = bool(python_path and os.path.isfile(python_path))

        is_ready = (
            script_ok and
            outdir and os.path.isdir(outdir) and
            python_ok and
            exe_name
        )

        # -------------------------------
        # BUTTON HELPER
        # -------------------------------
        def set_btn(btn, enabled, color=None):
            btn.setEnabled(enabled)

            # 🔑 skip styling for toggle button
            if btn is self.app.appened_py_version:
                return

            if color:
                btn.setStyleSheet(f"background-color: {color};")

            if color:
                btn.setStyleSheet(f"background-color: {color};")
            else:
                btn.setStyleSheet("")

        # -------------------------------
        # VALUE STATE (TEXT-BASED)
        # -------------------------------
        icon_has_value = bool(getattr(app, "icon_path", "").strip())
        script_has_value = bool(getattr(app, "script_path", "").strip())
        interpreter_has_value = bool(getattr(app, "python_interpreter_path", "").strip())

        # -------------------------------
        # RECENTS STATE (JSON-backed)
        # -------------------------------
        recent_scripts = app.state_data.get("recent_scripts", [])
        recent_icons = app.state_data.get("recent_icons", [])
        recent_interpreters = app.state_data.get("recent_interpreters", [])

        has_recent_scripts = bool(recent_scripts)
        has_recent_icons = bool(recent_icons)
        has_recent_interpreters = bool(recent_interpreters)

        # -------------------------------
        # DELETE + DELETE ALL BUTTONS
        # -------------------------------

        # ICON
        icon_enabled = not building and icon_has_value
        set_btn(app.delete_recent_icons, icon_enabled)
        app.delete_recent_icons.setText("❌" if icon_enabled else "")

        # SCRIPT
        script_enabled = not building and script_has_value
        set_btn(app.delete_recent_folder, script_enabled)
        app.delete_recent_folder.setText("❌" if script_enabled else "")

        # INTERPRETER
        interpreter_enabled = not building and interpreter_has_value

        set_btn(app.python_delete_interpreter, interpreter_enabled)
        app.python_delete_interpreter.setText("❌" if interpreter_enabled else "")

        set_btn(app.delete_all_icons, not building and has_recent_icons)
        set_btn(app.delete_all_folders, not building and has_recent_scripts)
        set_btn(app.python_delete_all_interpreter, not building and has_recent_interpreters)
                        
        # Tooltips
        set_btn(app.tooltips_checkbox, not building)
        set_btn(app.dependency_notice, not building)
        # 🔑 mutual exclusion + build lock
        min_checked = app.minimize_after_build.isChecked()
        close_checked = app.close_after_build.isChecked()

        set_btn(
            app.minimize_after_build,
            not building and not close_checked
        )

        set_btn(
            app.close_after_build,
            not building and not min_checked
        )

        # Apps
        set_btn(app.open_python_site_btn, not building)
        set_btn(app.interpreter_btn, not building)
        set_btn(app.interpreter_refresh_btn, not building and python_ok)
        app.select_interpreter.setEnabled(not building)

        # -------------------------------
        # ICON SECTION
        # -------------------------------
        set_btn(app.icon_btn, not building)
        set_btn(app.icon_clear_btn, not building and icon_has_value)
        set_btn(app.ico_convert_btn, not building)
        app.select_recent_icons.setEnabled(not building)

        # -------------------------------
        # FILE SECTION
        # -------------------------------
        set_btn(app.folder_btn, not building)
        set_btn(app.script_clear_btn, not building and script_has_value)
        app.recent_folder_dropdown.setEnabled(not building)

        # -------------------------------
        # OUTPUT SECTION
        # -------------------------------
        set_btn(app.appened_py_version, not building)
        set_btn(app.output_btn, not building)
        app.date_time_dropdown.setEnabled(not building)

        is_desktop = outdir and os.path.normpath(outdir) == os.path.normpath(desktop)
        set_btn(app.output_refresh_btn, not building and not is_desktop)

        
        
        # -------------------------------
        # EXE NAME REFRESH (revert to script name)
        # -------------------------------
        derived_name = ""

        if script_ok:
            derived_name = os.path.splitext(os.path.basename(script))[0].strip().lower()

        current_name = app.exe_name_input.text().strip().lower()

        can_revert_name = bool(
            derived_name and
            current_name and
            current_name != derived_name
        )

        set_btn(app.refresh_btn, not building and can_revert_name)

        app.exe_name_input.setReadOnly(building)

        # -------------------------------
        # BUTTON COLOR: Python Interpreter
        # -------------------------------

        if building:
            app.interpreter_btn.setStyleSheet("background-color: #8a8a8a;")
        else:
            if python_ok:
                app.interpreter_btn.setStyleSheet("background-color: #3bbf3b;")
            else:
                app.interpreter_btn.setStyleSheet("background-color: #be1a1a;")

        # -------------------------------
        # BUTTON COLOR: Script Folder
        # -------------------------------
        folder_ok = bool(script_ok)

        if building:
            app.folder_btn.setStyleSheet("background-color: #8a8a8a;")
        else:
            if folder_ok:
                app.folder_btn.setStyleSheet("background-color: #3bbf3b;")
            else:
                app.folder_btn.setStyleSheet("background-color: #be1a1a;")

        # -------------------------------
        # BUTTON COLOR: Output Folder
        # -------------------------------
        
        output_ok = bool(outdir and os.path.isdir(outdir))

        if building:
            app.output_btn.setStyleSheet("background-color: #8a8a8a;")
        else:
            if output_ok:
                app.output_btn.setStyleSheet("background-color: #3bbf3b;")
            else:
                app.output_btn.setStyleSheet("background-color: #be1a1a;")

        # -------------------------------
        # STATUS ONLY (lock applies here ONLY)
        # -------------------------------
        if getattr(app, "_status_lock", False):
            return

        if building:
            status_text = "Building..."

        elif is_ready:
            status_text = "Ready to build."

        else:
            status_text = "Missing required inputs."

        app.status_label.setText(status_text)
        app.status_label.setAlignment(Qt.AlignCenter)

        if building:
            color = "#000000"
        elif status_text.startswith("Building..."):
            color = "#000000" if "complete" in status_text.lower() else "#be1a1a"
        elif is_ready:
            color = "#3bbf3b"
        else:
            color = "#be1a1a"

        app.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: #FFFFFF;
                color: {color};
                border: 1px solid #3a3a3a;
            }}
        """)

        if building:
            app.status_label.setStyleSheet("""
                QLabel {
                    background-color: #FFFFFF;
                    color: #3bbf3b;
                    border: 1px solid #3a3a3a;
                }
            """)

        # -------------------------------
        # ICON BUTTON TEXT (match grey state)
        # -------------------------------
        icon_buttons = [
            app.delete_recent_icons,
            app.delete_recent_folder,
            app.delete_all_icons,
            app.delete_all_folders,
            app.python_delete_all_interpreter,
            app.python_delete_interpreter,
            app.refresh_btn,
            app.output_refresh_btn,
            app.icon_clear_btn,
            app.script_clear_btn,
            app.interpreter_refresh_btn,
        ]

        for btn in icon_buttons:
            if building:
                btn.setText("")
            else:
                # DELETE BUTTONS → respect actual state
                if btn == app.delete_recent_icons:
                    btn.setText("❌" if icon_has_value else "")
                elif btn == app.delete_recent_folder:
                    btn.setText("❌" if script_has_value else "")
                elif btn == app.python_delete_interpreter:
                    btn.setText("❌" if interpreter_has_value else "")

                elif btn == app.delete_all_icons:
                    btn.setText("💥" if has_recent_icons else "")
                elif btn == app.delete_all_folders:
                    btn.setText("💥" if has_recent_scripts else "")
                elif btn == app.python_delete_all_interpreter:
                    btn.setText("💥" if has_recent_interpreters else "")

                # REFRESH / CLEAR (state-driven)
                elif btn == app.interpreter_refresh_btn:
                    btn.setText("🔃" if interpreter_has_value else "")
                elif btn == app.script_clear_btn:
                    btn.setText("🔃" if script_has_value else "")
                elif btn == app.icon_clear_btn:
                    btn.setText("🔃" if icon_has_value else "")
                elif btn == app.output_refresh_btn:
                    btn.setText("🔃" if not is_desktop else "")
                elif btn == app.refresh_btn:
                    btn.setText("🔃" if can_revert_name else "")
                            
        # -------------------------------
        # LOCK + GREY INPUTS DURING BUILD
        # -------------------------------

        script = app.script_path_input.text().strip()
        outdir = app.output_path_input.text().strip()
        python_path = getattr(app, "python_interpreter_path", "").strip()
        exe_name = app.exe_name_input.text().strip()
        icon_path = getattr(app, "icon_path", "").strip()

        script_ok = bool(script and os.path.isfile(os.path.normpath(script)))
        outdir_ok = bool(outdir and os.path.isdir(os.path.normpath(outdir)))
        python_ok = bool(python_path and os.path.isfile(os.path.normpath(python_path)))
        exe_ok = bool(exe_name)
        icon_ok = bool(icon_path and os.path.isfile(os.path.normpath(icon_path)))

        # -------------------------------
        # LOCK + GREY (respect validation)
        # -------------------------------
        state = self.validation_status_message()

        mapping = [
        (app.python_entry_input, state["python_ok"]),
        (app.script_path_input, state["script_ok"]),
        (app.output_path_input, state["outdir_ok"]),
        (app.exe_name_input, state["exe_ok"]),
        (app.icon_path_input, state["icon_ok"]),
        ]

        # -------------------------------
        # BUILD MODE → force grey
        # -------------------------------
        if building:
            for widget, _ in mapping:

                widget.setStyleSheet("""
                    QLineEdit {
                        background-color: #d3d3d3;
                        color: #7a7a7a;
                        border: 2px solid #8a8a8a;
                    }
                """)

        else:
            for widget, ok in mapping:


                # 🔑 FORCE FULL RESET FIRST (this is what you're missing)
                widget.setStyleSheet("")

                

            # 🔑 THEN reapply validation styling
            self.validation_status_message()
        self.update_build_button()

    def update_build_button(self):
        app = self.app

        if not hasattr(app, "build_btn"):
            return

        state = self.validation_status_message()
        building = getattr(app, "building", False)
        is_ready = state["is_ready"]

        def set_btn(btn, enabled, color=None):
            btn.setEnabled(enabled)
            if color:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: black;
                        border: 2px solid #000000;
                    }}
                """)
        try:
            app.build_btn.clicked.disconnect()
        except:
            pass

        if building:
            set_btn(app.build_btn, True, "#FF0000")
            app.build_btn.setText("Cancel EXE")
            app.build_btn.clicked.connect(app.build_cancellation.cancel_build)

        else:
            if is_ready:
                set_btn(app.build_btn, True, "#3bbf3b")
            else:
                set_btn(app.build_btn, False, "#be1a1a")

            app.build_btn.setText("Build EXE")
            app.build_btn.clicked.connect(app.build_controller.build_exe)

    def run_dependency_advisory_async(self, entry_file: str):
        app = self.app

        # stop duplicate runs
        if getattr(app, "_dep_thread_running", False):
            return

        app._dep_thread_running = True

        self.dep_thread = QThread()
        self.dep_worker = DependencyWorker(self, entry_file)

        self.dep_worker.moveToThread(self.dep_thread)

        self.dep_thread.started.connect(self.dep_worker.run)

        self.dep_worker.finished.connect(self._on_dependency_result)

        # cleanup
        self.dep_worker.finished.connect(self.dep_thread.quit)
        self.dep_worker.finished.connect(self.dep_worker.deleteLater)
        self.dep_thread.finished.connect(self.dep_thread.deleteLater)

        self.dep_thread.start()

    def _on_dependency_result(self, packages: dict):
        app = self.app

        app._dep_thread_running = False

        if (
            packages
            and getattr(app, "dependency_notice_enabled", True)
            and not getattr(app, "_dependency_popup_shown", False)
        ):
            QTimer.singleShot(
                0,
                self.app,
                lambda: self.app.ui_dependency_popup.show_dependency_warning_popup(packages)
            )
            app._dependency_popup_shown = True