import os
import sys
import ast



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

        if is_ready and not self.app._was_build_ready:
            external_packages = self.run_dependency_advisory(script)

            if external_packages and not self.app._dependency_popup_shown:
                self.app._dependency_popup_shown = True
                state["external_packages"] = external_packages
            else:
                state["external_packages"] = []
        else:
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
        # APPLY STATUS TO UI
        # --------------------------------

        if hasattr(self.app, "status_label"):
            self.app.status_label.setText(state["status_text"])

        return state
    
        


    def update_build_button_state(self):
        # Handled in Qt layer
        pass

        # -------------------------------
        # Enable / disable output revert button
        # -------------------------------
        if hasattr(self.app, "output_refresh_btn"):
            outdir = self.app.output_path_input.text().strip()
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")

            can_revert_output = not outdir or os.path.normpath(outdir) != os.path.normpath(desktop)

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
                        background-color: #2a2a2a;
                    }
                """)
                
        if hasattr(self.app, "script_clear_btn"):
            has_script = bool(self.app.script_path_input.text().strip())

            if has_script:
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
                        background-color: #2a2a2a;
                    }
                """)
                
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

            exe_name = self.app.exe_name_input.text().strip()
            # --------------------------------
            # INLINE: EXE name status
            # --------------------------------

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




