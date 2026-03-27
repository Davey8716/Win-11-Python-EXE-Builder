import os
import sys
import ast
from PySide6.QtCore import QTimer

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
        imports = self.extract_imports_from_file(entry_file)
        external = self.filter_external_imports(imports)
        return external

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
            self.app.status_label.setFixedSize(200,75)
        else:
            self.app.status_label.setFixedSize(350,75)

        # ==========================================================
        # Dependency advisory — fire ONCE when NOT READY → READY
        # ==========================================================
        if is_ready:
            current_script = script

            script_changed = current_script != self.app._last_advisory_script

            if script_changed:
                external_packages = self.run_dependency_advisory(current_script)

                if (
                    external_packages
                    and getattr(self.app, "dependency_notice_enabled", True)
                    and not getattr(self.app, "_dependency_popup_shown", False)
                ):
                    QTimer.singleShot(
                        0,
                        lambda: self.app.ui_dependency_popup.show_dependency_warning_popup(external_packages)
                    )

                    # 🔑 prevent re-trigger spam
                    self.app._dependency_popup_shown = True

                self.app._last_advisory_script = current_script
                state["external_packages"] = external_packages
            else:
                state["external_packages"] = []
        else:
            self.app._last_advisory_script = None

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

            if color:
                btn.setStyleSheet(f"background-color: {color};")

            if color:
                btn.setStyleSheet(f"background-color: {color};")
            else:
                btn.setStyleSheet("")

        # Tooltips
        set_btn(app.tooltips_checkbox, not building)
        set_btn(app.dependency_notice, not building)

        # Apps
        set_btn(app.open_python_site_btn, not building)
        set_btn(app.interpreter_btn, not building)
        set_btn(app.interpreter_refresh_btn, not building and python_ok)
        set_btn(app.python_delete_interpreter, not building and python_ok)
        set_btn(app.python_delete_all_interpreter, not building)
        app.select_interpreter.setEnabled(not building)
        
        set_btn(app.icon_btn, not building)
        set_btn(app.ico_convert_btn, not building)
        set_btn(app.delete_all_icons, not building)
        set_btn(app.delete_recent_icons, not building)
        set_btn(app.icon_clear_btn,not building)
        app.select_recent_icons.setEnabled(not building)

        # File
        set_btn(app.folder_btn, not building)
        set_btn(app.script_clear_btn, not building)
        set_btn(app.delete_recent_folder, not building)
        set_btn(app.delete_all_folders, not building)
        app.recent_folder_dropdown.setEnabled(not building)

        # Output
        set_btn(app.appened_py_version, not building)
        set_btn(app.output_btn, not building)
        app.date_time_dropdown.setEnabled(not building)
        is_desktop = outdir and os.path.normpath(outdir) == os.path.normpath(desktop)

        set_btn(app.output_refresh_btn,not building and not is_desktop)

        # -------------------------------
        # EXE NAME REFRESH (revert to script name)
        # -------------------------------
        derived_name = ""

        if script_ok:
            derived_name = os.path.splitext(os.path.basename(script))[0]

        current_name = app.exe_name_input.text().strip()

        can_revert_name = bool(
            derived_name and
            current_name != derived_name
        )

        set_btn(app.refresh_btn,not building and can_revert_name)

        app.exe_name_input.setReadOnly(building)

        # -------------------------------
        # BUILD BUTTON (authoritative)
        # -------------------------------
        if hasattr(app, "build_btn"):

            try:
                app.build_btn.clicked.disconnect()
            except:
                pass

            if building:
                set_btn(app.build_btn, True, "#d43c3c")
                app.build_btn.setText("Cancel")

                app.build_btn.clicked.connect(app.build_cancellation.cancel_build)

            else:
                if is_ready:
                    set_btn(app.build_btn, True, "#3bbf3b")
                else:
                    set_btn(app.build_btn, False, "#be1a1a")

                app.build_btn.setText("Build EXE")

                app.build_btn.clicked.connect(app.build_controller.build_exe)

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
        # STATUS LABEL
        # -------------------------------
        current_text = app.status_label.text()

        if building:
            status_text = "Building..."
        elif current_text.startswith("Build"):
            status_text = current_text  # 🔑 preserve "Build complete / failed"
        elif is_ready:
            status_text = "Ready to build"
        else:
            status_text = "Missing required inputs"

        app.status_label.setText(status_text)

        if building:
            color = "#3bbf3b"
        elif current_text.startswith("Build"):
            color = "#3bbf3b" if "complete" in current_text.lower() else "#be1a1a"
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
                btn.setText("")  # 🔑 remove symbol during build
            else:
                # restore symbols
                if btn in [
                    app.delete_recent_icons,
                    app.delete_recent_folder,
                    app.python_delete_interpreter,
                ]:
                    btn.setText("❌")
                elif btn in [
                    app.delete_all_icons,
                    app.delete_all_folders,
                    app.python_delete_all_interpreter,
                ]:
                    btn.setText("💥")
                else:
                    btn.setText("🔃")

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

        for widget, ok in mapping:
            widget.setReadOnly(building)

            if building and ok:
                # grey ONLY valid ones
                widget.setStyleSheet("""
                    QLineEdit {
                        background-color: #d3d3d3;
                        color: #7a7a7a;
                        border: 2px solid #8a8a8a;
                    }
                """)
            else:
                # normal mode → let validation handle everything
                # 🔑 restore validation styling
                self.validation_status_message()
