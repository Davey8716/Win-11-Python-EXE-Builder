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
        self.update_build_button_state()
        self.validation_status_message()
        
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
        
        script = self.app.script_path_input.text().strip()
        outdir = self.app.output_path_input.text().strip()
        exe_name = self.app.exe_name_input.text().strip()
    
        python = getattr(self.app, "python_interpreter_path", "")
        
        # 🔑 NORMALIZE
        script = os.path.normpath(script) if script else ""
        outdir = os.path.normpath(outdir) if outdir else ""
        python = os.path.normpath(python) if python else ""

        # --------------------------------
        # Resolve script folder validity
        # --------------------------------

        if script and os.path.isfile(script):
            folder = os.path.dirname(script)
            py_files = [
                f for f in os.listdir(folder)
                if f.endswith(".py") and os.path.isfile(os.path.join(folder, f))
            ]
            folder_ok = bool(py_files)
        else:
            folder_ok = False

                
        # --------------------------------
        # INLINE: Output path
        # --------------------------------
        
        state = {}

        state["output_ok"] = bool(outdir and os.path.isdir(outdir))

        # --------------------------------
        # INLINE: EXE name
        # --------------------------------

        state["exe_ok"] = bool(exe_name)

        icon_path = getattr(self.app, "icon_path", "").strip()
        icon_path = os.path.normpath(icon_path) if icon_path else ""

        icon_ok = bool(icon_path and os.path.isfile(icon_path))
        state["icon_ok"] = icon_ok

        # --------------------------------
        # BUILD READINESS
        # --------------------------------

        script_ok = script and os.path.isfile(script)
        outdir_ok = outdir and os.path.isdir(outdir)
        exe_ok = bool(exe_name)
        python_ok = python and os.path.isfile(python)

        is_ready = bool(script_ok and outdir_ok and exe_ok and python_ok)
        # 🔑 FORCE NOT READY if build error exists
        if getattr(self.app, "build_error", None):
            is_ready = False

        state["is_ready"] = is_ready
        state["script_ok"] = script_ok
        state["outdir_ok"] = outdir_ok
        state["exe_ok"] = exe_ok
        state["python_ok"] = python_ok
        state["icon_ok"] = icon_ok

        def _style_input(widget, ok):
            if not widget:
                return

            widget.setStyleSheet(f"""
                QLineEdit {{
                    background-color: #FFFFFF;
                    color: {"#3bbf3b" if ok else "#be1a1a"};
                    border: 2px solid #3a3a3a;
                }}
            """)

        # 🔑 strict mapping (each tied to its own validation)
        _style_input(self.app.python_entry_input, python_ok)
        _style_input(self.app.script_path_input, script_ok)
        _style_input(self.app.output_path_input, outdir_ok)
        _style_input(self.app.exe_name_input, exe_ok)
        _style_input(self.app.icon_path_input,icon_ok)

        # Reset popup eligibility when leaving READY state
        if not is_ready:
            self.app._dependency_popup_shown = False

        if not is_ready:
            self.app.status_label.setFixedSize(120,75)
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
            state["external_packages"] = []
            self.app._dependency_popup_shown = False  # 🔑 reset when leaving READY

        # Track previous state
        self.app._was_build_ready = is_ready
                
        # --------------------------------
        # STATUS TEXT
        # --------------------------------

        # Python version (Py 3.14)
        python_path = getattr(self.app, "python_interpreter_path", "").strip()
        python_version = "Unknown"
        if python_path:
            parent = os.path.basename(os.path.dirname(python_path))
            if parent.lower().startswith("python"):
                raw = parent.lower().replace("python", "")
                if raw.isdigit():
                    python_version = f"{raw[0]}.{raw[1:]}" if len(raw) > 1 else raw
                    
        # Icon (name or Default)
        icon_path = getattr(self.app, "icon_path", "").strip()
        icon_display = os.path.basename(icon_path) if icon_path else "Default - (No User Icon)"

        # Script (parent\file)
        script_display = "No script"
        if script:
            name = os.path.basename(script)
            parent = os.path.basename(os.path.dirname(script))
            script_display = f"{parent}\\{name}" if parent else name

        # EXE name
        exe_name_display = getattr(self.app, "exe_name", "").strip()
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
        
        # KEEP
        # --------------------------------
        # BUTTON COLOR: Python Interpreter
        # --------------------------------
        if hasattr(self.app, "interpreter_btn"):
            if python and os.path.isfile(python):
                self.app.interpreter_btn.setStyleSheet("background-color: #3bbf3b;")
            else:
                self.app.interpreter_btn.setStyleSheet("background-color: #be1a1a;")

        # --------------------------------
        # BUTTON COLOR: Python Folder
        # --------------------------------
        if hasattr(self.app, "folder_btn"):
            if folder_ok:
                self.app.folder_btn.setStyleSheet("background-color: #3bbf3b;")
            else:
                self.app.folder_btn.setStyleSheet("background-color: #be1a1a;")

        # --------------------------------
        # BUTTON COLOR: Output Folder
        # --------------------------------
        if hasattr(self.app, "output_btn"):
            if outdir and os.path.isdir(outdir):
                self.app.output_btn.setStyleSheet("background-color: #3bbf3b;")
            else:
                self.app.output_btn.setStyleSheet("background-color: #be1a1a;")

        # -------------------------------
        # Python delete buttons (force white like others)
        # -------------------------------
        for attr in ["python_delete_interpreter", "python_delete_all_interpreter"]:
            if hasattr(self.app, attr):
                btn = getattr(self.app, attr)

                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                        color: black;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                    }

                    QPushButton:hover {
                        background-color: #f0f0f0;
                    }

                    QPushButton:pressed {
                        background-color: #e0e0e0;
                    }

                    QPushButton:disabled {
                        background-color: #1a1a1a;
                        color: #555;
                    }
                """)


        # --------------------------------
        # APPLY STATUS TO UI (MATCH QLINEEDIT STYLE)
        # --------------------------------
        if hasattr(self.app, "status_label"):
            self.app.status_label.setText(state["status_text"])

            if is_ready:
                self.app.status_label.setStyleSheet("""
                    QLabel {
                        background-color: #FFFFFF;
                        color: #3bbf3b;
                        border: 1px solid #3a3a3a;
                    }
                """)
            else:
                self.app.status_label.setStyleSheet("""
                    QLabel {
                        background-color: #FFFFFF;
                        color: #be1a1a;
                        border: 1px solid #3a3a3a;
                    }
                """)

        return state
    
        # --------------------------------
    def update_build_button_state(self):
        state = self.validation_status_message()
        
        is_ready = state["is_ready"]

        script = self.app.script_path_input.text().strip()
        
        
        script_ok = bool(script and os.path.isfile(script))

        outdir = self.app.output_path_input.text().strip()
        
        script = os.path.normpath(script) if script else ""
        outdir = os.path.normpath(outdir) if outdir else ""
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")

        python_path = getattr(self.app, "python_interpreter_path", "").strip()
        python_path = os.path.normpath(python_path) if python_path else ""
        python_ok = bool(python_path and os.path.isfile(python_path))
        
        icon_path = getattr(self.app, "icon_path", "").strip()
        icon_path = os.path.normpath(icon_path) if icon_path else ""
        icon_ok = bool(icon_path and os.path.isfile(icon_path))
        
            
        # -------------------------------
        # UNIFIED BUTTON STATE HANDLER
        # -------------------------------

        def _set_btn(btn, enabled, active_style=True, text=None):
            if text is not None:
                btn.setText(text)

            btn.setEnabled(bool(enabled))

            if enabled and active_style:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FFFFFF;
                    }
                    QPushButton:hover {
                        background-color: #555555;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color:#FFFFFF;
                        color: #777777;
                    }
                """)

        building = getattr(self.app, "building", False)
        
        # -------------------------------
        # RECENT DELETE BUTTONS (scripts + icons)
        # -------------------------------
        for btn_name in [
            "delete_recent_folder",
            "delete_all_folders",
            "delete_recent_icons",
            "delete_all_icons",
            "python_delete_interpreter"
            "python_delete_all_interpreter"

        ]:
            if hasattr(self.app, btn_name):
                btn = getattr(self.app, btn_name)

                if building:
                    _set_btn(btn, False)  # disable during build
                else:
                    _set_btn(btn, True)   # re-enable after build

        # -------------------------------
        # PYTHON SELECT
        # -------------------------------
        if hasattr(self.app, "select_python_btn"):
            _set_btn(self.app.select_python_btn, not building and not python_ok)

        # -------------------------------
        # ICON SELECT
        # -------------------------------
        if hasattr(self.app, "select_icon_btn"):
            _set_btn(self.app.select_icon_btn, not building and not icon_ok)

        # -------------------------------
        # OPEN ICO CONVERTER
        # -------------------------------
        if hasattr(self.app, "open_ico_converter_btn"):
            _set_btn(self.app.open_ico_converter_btn, not building)

        # -------------------------------
        # PYTHON INTERPRETER CLEAR
        # -------------------------------
        if hasattr(self.app, "interpreter_refresh_btn"):
            _set_btn(self.app.interpreter_refresh_btn, not building and python_ok)

        # -------------------------------
        # INTERPRETER BUTTONS
        # -------------------------------
        if hasattr(self.app, "delete_recent_interpreter"):
            _set_btn(self.app.delete_recent_interpreter, not building and python_ok)

        if hasattr(self.app, "delete_all_interpreters"):
            _set_btn(self.app.delete_all_interpreters, not building and bool(self.app.recent_interpreters))

        # -------------------------------
        # ICON CLEAR
        # -------------------------------
        if hasattr(self.app, "icon_clear_btn"):
            if building:
                _set_btn(self.app.icon_clear_btn, False)
            else:
                icon_path = getattr(self.app, "icon_path", "").strip()
                if not icon_path and hasattr(self.app, "icon_path_input"):
                    icon_path = self.app.icon_path_input.text().strip()

                _set_btn(self.app.icon_clear_btn, bool(icon_path), text="🔃")

        # -------------------------------
        # EXE NAME REFRESH
        # -------------------------------
        if hasattr(self.app, "refresh_btn"):
            if building:
                _set_btn(self.app.refresh_btn, False)
            else:
                exe_name = self.app.exe_name_input.text().strip()
                can_refresh = script_ok and exe_name and exe_name != "main"

                _set_btn(self.app.refresh_btn, can_refresh, text="🔃")

        # -------------------------------
        # OUTPUT REFRESH
        # -------------------------------
        if hasattr(self.app, "output_refresh_btn"):
            if building:
                _set_btn(self.app.output_refresh_btn, False)
            else:
                python_path = getattr(self.app, "python_interpreter_path", "")
                python_ok = python_path and os.path.isfile(python_path)

                is_desktop = (
                    outdir and
                    os.path.normpath(outdir) == os.path.normpath(desktop)
                )

                can_revert_output = (
                    script_ok and
                    python_ok and
                    not is_desktop
                )

                _set_btn(self.app.output_refresh_btn, can_revert_output)

        # -------------------------------
        # SCRIPT CLEAR
        # -------------------------------
        if hasattr(self.app, "script_clear_btn"):
            if building:
                _set_btn(self.app.script_clear_btn, False)
            else:
                _set_btn(self.app.script_clear_btn, script_ok)

        # -------------------------------
        # BUILD BUTTON (separate styling)
        # -------------------------------
        if hasattr(self.app, "build_btn"):

            # 🔴 BUILDING → Cancel mode
            if building:
                self.app.build_btn.setEnabled(True)
                self.app.build_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #d43c3c;
                        color: white;
                    }
                    QPushButton:hover {
                        background-color: #d43c3c;
                    }
                """)

            # 🟢 READY → Build
            elif is_ready:
                self.app.build_btn.setEnabled(True)
                self.app.build_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3bbf3b;
                        color: white;
                    }
                    QPushButton:hover {
                        background-color: #2e9e2e;
                    }
                """)

            # 🔴 NOT READY → disabled (grey text)
            else:
                self.app.build_btn.setEnabled(False)
                self.app.build_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #be1a1a;
                        color: white;
                    }
                    QPushButton:disabled {
                        background-color: #be1a1a;
                        color: white;
                    }
                """)
                                        
        # -------------------------------
        # EXE NAME REFRESH (🔃)
        # -------------------------------
        if hasattr(self.app, "refresh_btn"):
            if building:
                _set_btn(self.app.refresh_btn, False)
            else:
                exe_name = self.app.exe_name_input.text().strip()
                can_refresh = (
                    script_ok and
                    exe_name and
                    exe_name != "main"
                )

                _set_btn(self.app.refresh_btn, can_refresh, text="🔃")
                
        # -------------------------------
        # EXE NAME FIELD (LOCK DURING BUILD)
        # -------------------------------
        if hasattr(self.app, "exe_name_input"):
            if getattr(self.app, "building", False):
                self.app.exe_name_input.setReadOnly(True)
            else:
                self.app.exe_name_input.setReadOnly(False)

        # Reset popup eligibility when leaving READY state
        if not is_ready:
            self.app._dependency_popup_shown = False

        if not is_ready:
            self.app.status_label.setFixedSize(120,75)
        else:
            self.app.status_label.setFixedSize(275,100)
        if building:
            self.app.status_label.setFixedSize(275,50)

        # --------------------------------
        # HARD RESET when script removed
        # --------------------------------
        if not script_ok:
            if hasattr(self.app, "output_path_input"):
                self.app.output_path_input.clear()

            if hasattr(self.app, "exe_name_input"):
                self.app.exe_name_input.clear()

        # --------------------------------
        # INLINE: Output path status
        # --------------------------------
        if hasattr(self.app, "output_path_status_label"):
            if outdir and os.path.isdir(outdir):
                self.app.output_path_status_label.setText("OUTPUT PATH SET")
                self.app.output_path_status_label.setStyleSheet("color: #3bbf3b;")
                self.app.output_path_status_label.setFixedSize(155,35)
            else:
                self.app.output_path_status_label.setText("OUTPUT PATH NOT SET")
                self.app.output_path_status_label.setStyleSheet("color: #be1a1a;")
                self.app.output_path_status_label.setFixedSize(185,35)

        # --------------------------------
        # INLINE: EXE name status
        # --------------------------------
        exe_name = self.app.exe_name_input.text().strip()

        if hasattr(self.app, "exe_name_status_label"):
            if exe_name:
                self.app.exe_name_status_label.setText("EXE NAME SET")
                self.app.exe_name_status_label.setStyleSheet("color: #3bbf3b;")
                self.app.exe_name_status_label.setFixedSize(125,35)
            else:
                self.app.exe_name_status_label.setText("EXE NAME NOT SET")
                self.app.exe_name_status_label.setStyleSheet("color: #be1a1a;")
                self.app.exe_name_status_label.setFixedSize(155,35)
                

        # -------------------------------
        # Icon clear state
        # -------------------------------
        
        state = {}

        icon_path = getattr(self.app, "icon_path", "").strip()
        state["has_icon"] = bool(icon_path)

        # -------------------------------
        # Validation state
        # -------------------------------


        validation = self.validation_status_message()
        state.update(validation)

        # Build button state
        state["can_build"] = self.inputs_are_valid()

        return state



