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

    # ----------------------------------------------------
    # Validation helpers
    # ----------------------------------------------------

    def inputs_are_valid(self):
        script = self.app.script_path_var.get().strip()
        outdir = self.app.output_path_var.get().strip()
        exe_name = self.app.exe_name_var.get().strip()
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

        script = self.app.script_path_var.get().strip()
        outdir = self.app.output_path_var.get().strip()
        exe_name = self.app.exe_name_var.get().strip()
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
                self.app.python_status_label.configure(
                    text="PYTHON INTERPRETER SET",
                    text_color="#3bbf3b"
                )
            else:
                self.app.python_status_label.configure(
                    text="PYTHON INTERPRETER NOT SET",
                    text_color="#be1a1a"
                )
                
        # --------------------------------
        # INLINE: Python folder
        # --------------------------------
        
        if hasattr(self.app, "script_folder_status_label"):
            if folder_ok:
                self.app.script_folder_status_label.configure(
                    text="PYTHON FOLDER SET",
                    text_color="#3bbf3b"
                )
            else:
                self.app.script_folder_status_label.configure(
                    text="PYTHON FOLDER NOT SET",
                    text_color="#be1a1a"
                )
                
        # --------------------------------
        # INLINE: Output path
        # --------------------------------

        if hasattr(self.app, "output_path_status_label"):
            outdir = self.app.output_path_var.get().strip()

            if outdir and os.path.isdir(outdir):
                self.app.output_path_status_label.configure(
                    text="EXE OUTPUT PATH SET",
                    text_color="#3bbf3b"
            )
            else:
                self.app.output_path_status_label.configure(
                    text="EXE OUTPUT PATH NOT SET",
                    text_color="#be1a1a"
            )

        # --------------------------------
        # INLINE: EXE name
        # --------------------------------

        if hasattr(self.app, "exe_name_status_label"):
            exe_name = self.app.exe_name_var.get().strip()

            if exe_name:
                self.app.exe_name_status_label.configure(
                    text="EXE NAME SET",
                    text_color="#3bbf3b"
                )
            else:
                self.app.exe_name_status_label.configure(
                    text="EXE NAME NOT SET",
                    text_color="#be1a1a"
                )

        # --------------------------------
        # BUILD READINESS
        # --------------------------------

        script_ok = script and os.path.isfile(script)
        outdir_ok = outdir and os.path.isdir(outdir)
        exe_ok = bool(exe_name)
        python_ok = python and os.path.isfile(python)
        
        is_ready = bool(script_ok and outdir_ok and exe_ok and python_ok)
        
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

                # MUST be scheduled on main thread
                self.app.after(
                    0,
                    lambda packages=external_packages:
                        self.app.show_dependency_warning_popup(packages)
                )

        # Track previous state
        self.app._was_build_ready = is_ready


        if script_ok and outdir_ok and exe_ok and python_ok:
            script_name = os.path.basename(script)
            return f"✅ READY TO BUILD — {script_name}"
        else:
            return "❌ NOT READY TO BUILD"


    def update_build_button_state(self):
        # UI not ready yet
        if not hasattr(self.app, "status_label") or not hasattr(self.app, "build_btn"):
            return

        if self.app.building:
            return

        # -------------------------------
        # Grey / un-grey EXE name entry
        # -------------------------------
        
        if hasattr(self.app, "exe_entry"):
            exe_name = self.app.exe_name_var.get().strip()

            if not exe_name:
                self.app.exe_entry.configure(
                    text_color="#888888",
                    border_color="#888888"
                )
            else:
                self.app.exe_entry.configure(
                    text_color="white",
                    border_color=self.app.exe_entry_default_border
                )
                
        # -------------------------------
        # Enable / disable revert button
        # -------------------------------

        if hasattr(self.app, "refresh_btn"):
            script = self.app.entry_script or self.app.script_path_var.get().strip()
            exe_name = self.app.exe_name_var.get().strip()

            can_revert = False
            if script and os.path.isfile(script):
                derived = os.path.splitext(os.path.basename(script))[0]
                can_revert = (exe_name != derived)

            self.app.refresh_btn.configure(
                state="normal" if can_revert else "disabled",
                fg_color="#444444" if can_revert else "#2a2a2a",
                hover_color="#555555" if can_revert else "#2a2a2a"
            )

        # -------------------------------
        # Enable / disable output revert button
        # -------------------------------

        if hasattr(self.app, "output_refresh_btn"):
            outdir = self.app.output_path_var.get().strip()
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")

            can_revert_output = not outdir or os.path.normpath(outdir) != os.path.normpath(desktop)

            if can_revert_output:
                self.app.output_refresh_btn.configure(
                    state="normal",
                    fg_color="#444444",
                    hover_color="#555555"
                )
            else:
                self.app.output_refresh_btn.configure(
                    state="disabled",
                    fg_color="#2a2a2a",
                    hover_color="#2a2a2a"
                )
                
        # -------------------------------
        # Enable / disable script clear button
        # -------------------------------

        if hasattr(self.app, "script_clear_btn"):
            has_script = bool(self.app.script_path_var.get().strip())

        if has_script:
            self.app.script_clear_btn.configure(
                state="normal",
                fg_color="#444444",
                hover_color="#555555"
            )
        else:
            self.app.script_clear_btn.configure(
                state="disabled",
                fg_color="#2a2a2a",
                hover_color="#2a2a2a"
            )

        # -------------------------------
        # Enable / disable icon clear button
        # -------------------------------

        if hasattr(self.app, "icon_clear_btn"):
            has_icon = bool(self.app.icon_path_var.get().strip())

            if has_icon:
                self.app.icon_clear_btn.configure(
                    state="normal",
                    fg_color="#444444",
                    hover_color="#555555"
                )   
            else:
                self.app.icon_clear_btn.configure(
                    state="disabled",
                    fg_color="#2a2a2a",
                    hover_color="#2a2a2a"
                )

        # -------------------------------
        # Existing logic (unchanged)
        # -------------------------------
        
        message = self.validation_status_message()
        self.app.status_label.configure(text=message)

        if self.inputs_are_valid():

            self.app.build_btn.configure(
                state="normal",
                fg_color="#3bbf3b",
                hover_color="#2e9e2e"
            )
        else:
            self.app.build_btn.configure(
                state="disabled",
                fg_color="#555555",
                hover_color="#555555"
            )
            
    
    def extract_imports_from_file(self,py_file: str) -> set[str]:
        imports = set()

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=py_file)
        except Exception:
            return imports  # fail silently, advisory only

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        return imports
    
    def filter_external_imports(self,imports: set[str]) -> list[str]:
        stdlib = set(sys.stdlib_module_names)
        return sorted(i for i in imports if i not in stdlib)

    
    def run_dependency_advisory(self, entry_file: str) -> list[str]:
        imports = self.extract_imports_from_file(entry_file)
        external = self.filter_external_imports(imports)
        return external





