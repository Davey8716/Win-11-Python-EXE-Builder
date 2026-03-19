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
        # INLINE PYTHON STATUS (button row)
        # --------------------------------

        if hasattr(self.app, "python_status_label"):
            if python and os.path.isfile(python):
                self.app.python_status_label.setText("PYTHON INTERPRETER SET")
                self.app.python_status_label.setStyleSheet("color: #3bbf3b;")
            else:
                self.app.python_status_label.setText("PYTHON INTERPRETER NOT SET")
                self.app.python_status_label.setStyleSheet("color: #be1a1a;")
                
        # --------------------------------
        # INLINE: Python folder
        # --------------------------------

        if hasattr(self.app, "script_folder_status_label"):
            if folder_ok:
                self.app.script_folder_status_label.setText("PYTHON FOLDER SET")
                self.app.script_folder_status_label.setStyleSheet("color: #3bbf3b;")
            else:
                self.app.script_folder_status_label.setText("PYTHON FOLDER NOT SET")
                self.app.script_folder_status_label.setStyleSheet("color: #be1a1a;")
                
        # --------------------------------
        # INLINE: Output path
        # --------------------------------
        
        state = {}

        state["output_ok"] = bool(outdir and os.path.isdir(outdir))

        # --------------------------------
        # INLINE: EXE name
        # --------------------------------

        state["exe_ok"] = bool(exe_name)

        # --------------------------------
        # BUILD READINESS
        # --------------------------------

        script_ok = script and os.path.isfile(script)
        outdir_ok = outdir and os.path.isdir(outdir)
        exe_ok = bool(exe_name)
        python_ok = python and os.path.isfile(python)

        is_ready = bool(script_ok and outdir_ok and exe_ok and python_ok)

        state["is_ready"] = is_ready
        state["script_ok"] = script_ok
        state["outdir_ok"] = outdir_ok
        state["exe_ok"] = exe_ok
        state["python_ok"] = python_ok

        # Reset popup eligibility when leaving READY state
        if not is_ready:
            self.app._dependency_popup_shown = False

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
                ):
                    QTimer.singleShot(
                        0,
                        lambda: self.app.show_dependency_warning_popup(external_packages)
                    )

                self.app._last_advisory_script = current_script
                state["external_packages"] = external_packages
            else:
                state["external_packages"] = []
        else:
            self.app._last_advisory_script = None
            state["external_packages"] = []

        # Track previous state
        self.app._was_build_ready = is_ready
        
        # --------------------------------
        # STATUS TEXT
        # --------------------------------

        state["status_text"] = (
            f"READY TO BUILD — {os.path.basename(script)}"
            if is_ready else
            "NOT READY TO BUILD"
        )

        # --------------------------------
        # APPLY STATUS TO UI (MATCH QLINEEDIT STYLE)
        # --------------------------------

        if hasattr(self.app, "status_label"):
            self.app.status_label.setText(state["status_text"])

            if is_ready:
                self.app.status_label.setStyleSheet("""
                    QLineEdit {
                        background-color: #202020;
                        color: #3bbf3b;
                        border: 1px solid #3a3a3a;
                    }
                """)
            else:
                self.app.status_label.setStyleSheet("""
                    QLineEdit {
                        background-color: #202020;
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
        
        # 🔑 FORCE sync icon from UI (single source of truth)
        if hasattr(self.app, "icon_path_input"):
            ui_icon = self.app.icon_path_input.text().strip()
            self.app.icon_path = os.path.normpath(ui_icon) if ui_icon else ""

        
        # -------------------------------
        # ICON CLEAR BUTTON STATE
        # -------------------------------

        if hasattr(self.app, "icon_clear_btn"):
            icon_path = getattr(self.app, "icon_path", "").strip()

            # 🔑 fallback to QLineEdit text if state is empty
            if not icon_path and hasattr(self.app, "icon_path_input"):
                icon_path = self.app.icon_path_input.text().strip()

            if icon_path:
                # ACTIVE (icon exists → can clear)
                self.app.icon_clear_btn.setEnabled(True)
                self.app.icon_clear_btn.setText("🔃")
                self.app.icon_clear_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #444444;
                    }
                    QPushButton:hover {
                        background-color: #555555;
                    }
                """)
            else:
                # DISABLED (no icon → nothing to clear)
                self.app.icon_clear_btn.setEnabled(False)
                self.app.icon_clear_btn.setStyleSheet("""
                    QPushButton {
                        background-color:#1F1F1F;
                        color: #777777;
                    }
                """)

       
        # --------------------------------
        # EXE name refresh button
        # --------------------------------
        if hasattr(self.app, "refresh_btn"):
            exe_name = self.app.exe_name_input.text().strip()

            can_refresh = (
                script_ok and
                exe_name and
                exe_name != "main"
            )

            if can_refresh:
                self.app.refresh_btn.setEnabled(True)
                self.app.refresh_btn.setText("🔃")
                self.app.refresh_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #444444;
                    }
                    QPushButton:hover {
                        background-color: #555555;
                    }
                """)
            else:
                self.app.refresh_btn.setEnabled(False)
                self.app.refresh_btn.setStyleSheet("""
                    QPushButton {
                        background-color:#1F1F1F;
                        color: #777777;
                    }
                """)
                
      
        # --------------------------------
        # OUTPUT refresh button
        # --------------------------------
        if hasattr(self.app, "output_refresh_btn"):
            can_revert_output = (
                script_ok and
                bool(outdir) and
                os.path.normpath(outdir) != os.path.normpath(desktop)
            )

            if can_revert_output:
                self.app.output_refresh_btn.setEnabled(True)
                self.app.output_refresh_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #444444;
                    }
                    QPushButton:hover {
                        background-color: #555555;
                    }
                """)
            else:
                self.app.output_refresh_btn.setEnabled(False)
                self.app.output_refresh_btn.setStyleSheet("""
                    QPushButton {
                        background-color:#1F1F1F;
                        color: #777777;
                    }
                """)

        # --------------------------------
        # SCRIPT CLEAR button
        # --------------------------------
        if hasattr(self.app, "script_clear_btn"):
            if getattr(self.app, "building", False):
                # 🔒 HARD LOCK during build
                self.app.script_clear_btn.setEnabled(False)
                self.app.script_clear_btn.setStyleSheet("""
                    QPushButton {
                        background-color:#1F1F1F;
                        color: #777777;
                    }
                """)
            elif script_ok:
                self.app.script_clear_btn.setEnabled(True)
                self.app.script_clear_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #444444;
                    }
                    QPushButton:hover {
                        background-color: #555555;
                    }
                """)
            else:
                self.app.script_clear_btn.setEnabled(False)
                self.app.script_clear_btn.setStyleSheet("""
                    QPushButton {
                        background-color:#1F1F1F;
                        color: #777777;
                    }
                """)
                
        # --------------------------------
        # BUILD BUTTON
        # --------------------------------
        if hasattr(self.app, "build_btn"):
            self.app.build_btn.setEnabled(is_ready)

            if is_ready:
                self.app.build_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3bbf3b;
                    }
                    QPushButton:hover {
                        background-color: #2e9e2e;
                    }
                """)
            else:
                self.app.build_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #be1a1a;
                        color: #777777;
                    }
                """)

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
            else:
                self.app.output_path_status_label.setText("OUTPUT PATH NOT SET")
                self.app.output_path_status_label.setStyleSheet("color: #be1a1a;")

        # --------------------------------
        # INLINE: EXE name status
        # --------------------------------
        exe_name = self.app.exe_name_input.text().strip()

        if hasattr(self.app, "exe_name_status_label"):
            if exe_name:
                self.app.exe_name_status_label.setText("EXE NAME SET")
                self.app.exe_name_status_label.setStyleSheet("color: #3bbf3b;")
            else:
                self.app.exe_name_status_label.setText("EXE NAME NOT SET")
                self.app.exe_name_status_label.setStyleSheet("color: #be1a1a;")
                


   
                                    
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




