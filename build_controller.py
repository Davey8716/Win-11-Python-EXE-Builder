import datetime,os,sys,subprocess,time,threading
from PySide6.QtCore import  QTimer
from PySide6.QtGui import QFont
from bundle_validation import validate_bundle_inputs
from datetime import datetime

CREATE_NO_WINDOW = 0x08000000

class BuildController:
    def __init__(self, app):
        self.app = app

    # -------------------------------------------------------------
    # Build EXE
    # -------------------------------------------------------------

    def build_exe(self, app):
        app = self.app
        app.building = False
        app._eta_running = True


        # ==================================================
        # Debug log (Desktop, user-visible)
        # ==================================================

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        app.debug_log_path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            f"EXE_BUILDER_DEBUG_{timestamp}.log"
        )

        with open(app.debug_log_path, "w", encoding="utf-8") as f:
            f.write("BUILD STARTED\n")

        IS_FROZEN = getattr(sys, "frozen", False)

        with open(app.debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"IS_FROZEN={IS_FROZEN}\n")
            f.write(f"ENTRY_SCRIPT={repr(app.entry_script)}\n")
            f.write(f"PROJECT_ROOT={repr(app.project_root)}\n")
            f.write(f"PYTHON_INTERPRETER_PATH={repr(app.python_interpreter_path)}\n")

        # ==================================================
        # CANCEL MODE
        # ==================================================

        if app.build_process:
            app.build_cancellation.cancel_build()
            return

        import build_cancellation
        app.build_cancellation = build_cancellation.BuildCancellation(
            app=app, ui=app
        )

        # ==================================================
        # READ UI VALUES
        # ==================================================
        
        script = app.script_path_input.text().strip()
        outdir = app.output_path_input.text().strip()
        icon = app.icon_path_input.text().strip()

        script = os.path.normpath(script) if script else ""
        outdir = os.path.normpath(outdir) if outdir else ""
        icon = os.path.normpath(icon) if icon else ""

        entry_point = app.entry_script
        project_root = app.project_root

        if not entry_point and script and os.path.isfile(script):
            entry_point = script
            project_root = os.path.dirname(script)

        app.entry_script = entry_point
        app.project_root = project_root

        # ==================================================
        # Bundle validation
        # ==================================================

        ok, error = validate_bundle_inputs(app)

        if not ok:
            app.build_cancellation.abort_build(error)
            return

        # ==================================================
        # ENTER BUILD MODE
        # ==================================================

        app.building = True
        if hasattr(app, "script_clear_btn"):
            app.script_clear_btn.setDisabled(True)
        app.build_btn.setText("Cancel EXE")
        app.build_btn.clicked.disconnect()
        app.build_btn.clicked.connect(self.build_exe)
        app.status_label.setFixedWidth(425)
        
       
        
        app.build_start_time = time.time()
        app.state_ctrl.update_eta_loop()
        
        # ==================================================
        # Final validation
        # ==================================================

        if not entry_point or not os.path.isfile(entry_point):
            app.build_cancellation.abort_build("Invalid or missing entry script.")
            return

        if not project_root or not os.path.isdir(project_root):
            app.build_cancellation.abort_build("Invalid project folder.")
            return

        exe_name = app.exe_name_input.text().strip()
        if not exe_name:
            app.build_cancellation.abort_build("Please enter an EXE name.")
            return

        # ==================================================
        # Resolve PyInstaller (ALWAYS via Python interpreter)
        # ==================================================

        python = app.python_interpreter_path
        if not python or not os.path.isfile(python):
            app.build_cancellation.abort_build(
                "Python interpreter not found.\n"
                "Please select a Python interpreter before building."
            )
            return  

        result = subprocess.run(
            [python, "-m", "PyInstaller", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            app.build_cancellation.abort_build(
                "PyInstaller is not available in the selected Python interpreter.\n\n"
                "Install it with:\n\npip install pyinstaller"
            )
            return

        cmd_prefix = [python, "-m", "PyInstaller"]

        app.status_label.setText("Using PyInstaller (python -m)")
        app.repaint()
        
        # --------------------------------------------------
        # OUTPUT FOLDER SAFETY CHECK (exists + writable)
        # --------------------------------------------------

        if not outdir or not os.path.isdir(outdir):
            app.set_status("Output folder does not exist.")
            app.building = False
            app.build_ui_controller.restore_build_ui()
            app.validator.validation_status_message()  # 🔑 force red
            return

        # 🔑 Test write access (handles protected folders)
        try:
            test_file = os.path.join(outdir, "__write_test.tmp")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception:
            app.validator.set_build_error(
                f"ERROR — Cannot write to this folder\n{outdir}\n"
                "This location is read-only. Choose another."
            )

            app.building = False
            app.build_ui_controller.restore_build_ui()
            return
        
        # ==================================================
        # Build paths
        # ==================================================

        app.last_build_counter += 1
        timestamp = ""
        if getattr(app, "append_datetime", False):
            fmt = getattr(app, "datetime_format", "")
            if fmt:
                timestamp = datetime.now().strftime(fmt)
        parts = [exe_name]

        # date/time (existing)
        if getattr(app, "append_datetime", False):
            parts.append(timestamp)

        # python version
        if getattr(app, "append_py_version", False):
            python_path = getattr(app, "python_interpreter_path", "")
            version = "py"

            if python_path:
                parent = os.path.basename(os.path.dirname(python_path)).lower()
                if parent.startswith("python"):
                    raw = parent.replace("python", "")
                    if raw.isdigit():
                        version = f"py{raw[0]}.{raw[1:]}" if len(raw) > 1 else f"py{raw}"

            parts.append(version)

        final_exe_name = "_".join(parts)

        build_path = os.path.join(outdir, "build", final_exe_name)
        spec_path = os.path.join(outdir, "spec", final_exe_name)

        os.makedirs(build_path, exist_ok=True)
        os.makedirs(spec_path, exist_ok=True)

        cmd = [
            *cmd_prefix,
            "--onedir",
            "--clean",
            "--noconfirm",
            "--collect-all=tkinter",
            "--collect-all=tk",
            "--collect-all=qt_material",
            "--windowed",
            "--noconsole",
            "--hidden-import=pynput",
            "--hidden-import=win32gui",
            "--hidden-import=win32con",
            "--hidden-import=win32api",
            "--hidden-import=win32process",
            "--hidden-import=pygetwindow",
            "--hidden-import=pystray",
            f"--distpath={outdir}",
            f"--workpath={build_path}",
            f"--specpath={spec_path}",
            f"--name={final_exe_name}",
            entry_point
        ]

        if project_root:
            cmd.append(f"--add-data={project_root}{os.pathsep}.")

        data_file = os.path.join(project_root, "screen_mover_state.json")
        if os.path.isfile(data_file):
            cmd.append(f"--add-data={data_file}{os.pathsep}.")

        if icon:
            cmd += ["--icon", icon]

        app.current_build_paths = [
            os.path.join(outdir, final_exe_name + ".exe"),
            os.path.join(outdir, "build", final_exe_name),
            os.path.join(outdir, "spec", final_exe_name),
        ]   

        # ==================================================
        # Run PyInstaller (threaded)
        # ==================================================

        app.status_label.setText("Building...")
        # ⛔ move this OUT of thread (safe here)
        app.build_ui_controller.set_controls_enabled(False)
        
        def run_build(cmd):
            app.recent_folder_dropdown.setEnabled(False)
            app.refresh_btn.setEnabled(False)
            app.exe_name_input.setReadOnly(False)
            app.icon_clear_btn.setEnabled(False)
            

            try:
                with open(app.debug_log_path, "a", encoding="utf-8") as f:
                    f.write("ENTERED run_build\n")
                    f.write("CMD: " + " ".join(cmd) + "\n")

                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=CREATE_NO_WINDOW
                )

                app.build_process = proc

                out, err = proc.communicate()
                ret = proc.returncode

                with open(app.debug_log_path, "a", encoding="utf-8") as f:
                    f.write(f"RETURN CODE: {ret}\n")
                    f.write("STDERR:\n" + (err or "<empty>") + "\n")

                # ✅ SAFE HANDOFF TO UI THREAD
                def on_complete():
                    if not app.building:
                        return

                    if ret == 0:
                        app.last_build_seconds = int(time.time() - app.build_start_time)
                        app.state_ctrl.save_state()

                        app.set_status("Build complete.")
                        QTimer.singleShot(5000, app.showMinimized)
                    else:
                        app.set_status("Build failed. See debug log.")
                    
                    app.building = False
                        
                app.icon_clear_btn.setEnabled(True)
                app.refresh_btn.setEnabled(True)
                app.exe_name_input.setReadOnly(True)
                app._eta_running = False
                app.recent_folder_dropdown.setEnabled(True)
                app.build_btn.setText("Build EXE")
                self.app.build_btn.setStyleSheet("background-color:#3bbf3b;")
                app.set_status("Build complete." if ret == 0 else "Build failed. See debug log.")
            
                app.status_label.setFont(QFont("Rubik UI", 11, QFont.Bold))

                try:
                    app.build_btn.clicked.disconnect()
                except:
                    pass

                app.build_btn.clicked.connect(self.build_exe)
                QTimer.singleShot(0, lambda: on_complete())  # ← SAFE

            finally:
                # ✅ SAFE UI CLEANUP
                def finalize_ui():
                    app.build_process = None
                    app.restore_build_ui()
                    
                QTimer.singleShot(0, lambda: finalize_ui())  # ← SAFE

        # ✅ THIS MUST BE RIGHT AFTER THE FUNCTION
        threading.Thread(
            target=run_build,
            args=(cmd,),
            daemon=True
        ).start()
        
        app.build_ui_controller.set_controls_enabled(True)
        app.validator.update_build_button_state()