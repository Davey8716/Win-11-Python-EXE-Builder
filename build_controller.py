import datetime,os,sys,subprocess,time
from PySide6.QtGui import QFont
from bundle_validation import validate_bundle_inputs
from datetime import datetime
from PySide6.QtCore import QObject, Signal,QTimer
from PySide6.QtCore import QThread
from pathlib import Path

CREATE_NO_WINDOW = 0x08000000

class BuildController(QObject):
    build_complete_signal = Signal(int, str, str)

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.build_complete_signal.connect(self._on_build_complete_ui)

    # ============================================================
    # ETA LOOP
    # ============================================================
    def start_eta(self):
        self.app._eta_running = True
        self._tick_eta()

    def stop_eta(self):
        self.app._eta_running = False

    def _tick_eta(self):
        app = self.app

        if not getattr(app, "_eta_running", False):
            return

        if not getattr(app, "building", False):
            return

        elapsed = int(time.time() - app.build_start_time)
        est_total = app.last_build_seconds
        remaining = max(est_total - elapsed, 0)

        app.status_label.setFont(QFont("Rubik UI", 13, QFont.Bold))
        app.status_label.setText(
            f"Building... {elapsed}s elapsed\n — approx {remaining}s remaining"
        )

        

        QTimer.singleShot(300, self._tick_eta)

    

    # -------------------------------------------------------------
    # Build EXE
    # -------------------------------------------------------------

    def build_exe(self, app):
        app = self.app
        app.building = True
        app._eta_running = True

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

        # 🔑 match build naming logic
        script = app.entry_script or ""
        script = os.path.normpath(script) if script else ""

        script_name = os.path.splitext(os.path.basename(script))[0].lower() if script else ""
        parent = os.path.basename(os.path.dirname(script)) if script else ""

        parts = ["EXE_BUILDER_DEBUG"]

        if script:
            parts.append(app.exe_name_input.text().strip() or "exe")

            # parent (main/app/run case)
            if script_name in {"main", "app", "run"} and parent:
                parts.append(parent)

        # 🔑 python version append (match build logic)
        if getattr(app, "append_py_version", False):
            python_path = getattr(app, "python_interpreter_path", "")
            version = "py"

            if python_path:
                try:
                    parent = os.path.basename(os.path.dirname(python_path)).lower()
                    if parent.startswith("python"):
                        raw = parent.replace("python", "")
                        if raw.isdigit():
                            version = f"py{raw[0]}.{raw[1:]}" if len(raw) > 1 else f"py{raw}"
                except:
                    pass

            parts.append(version)

        parts.append(timestamp)

        log_name = "_".join(parts) + ".log"

        app.debug_log_path = os.path.join(
            os.path.expanduser("~"),
            "Desktop",
            log_name
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

        import build_cancellation
        app.build_cancellation = build_cancellation.BuildCancellation(
            app=app, ui=app
        )


        if app.build_process:
            app.build_cancellation.cancel_build()
            return

      
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

        app.build_btn.setText("Cancel EXE")
        app.build_btn.clicked.disconnect()
        app.build_btn.clicked.connect(self.build_exe)
        app.status_label.setFixedWidth(250)
        app.validation_controller.update_ui_state()
        
        app.build_start_time = time.time()
        self.start_eta()
        
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
            app.build_ui_controller.restore_build_ui()
            app.validation_controller.validation_status_message()  # 🔑 force red
            return

        # 🔑 Test write access (handles protected folders)
        try:
            test_file = os.path.join(outdir, "__write_test.tmp")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception:
            app.validation_controller.set_build_error(
                f"ERROR — Cannot write to this folder\n{outdir}\n"
                "This location is read-only. Choose another."
            )


            app.validation_controller.update_ui_state()
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
        

        script_path = Path(script)
        script_name = script_path.stem.lower()

        parts = [exe_name]

        # 🔑 prevent overwrite for common entry files
        if script_name in {"main", "app", "run"}:
            parent_name = script_path.parent.name
            if parent_name:
                parts.append(parent_name)

        # date/time
        if getattr(app, "append_datetime", False):
            parts.append(timestamp)

        # python version
        if getattr(app, "append_py_version", False):
            python_path = getattr(app, "python_interpreter_path", "")
            version = "py"

            if python_path:
                try:
                    parent = os.path.basename(os.path.dirname(python_path)).lower()
                    if parent.startswith("python"):
                        raw = parent.replace("python", "")
                        if raw.isdigit():
                            version = f"py{raw[0]}.{raw[1:]}" if len(raw) > 1 else f"py{raw}"
                except:
                    pass

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


        self.build_thread = QThread()
        self.worker = BuildWorker(app, cmd)

        self.worker.moveToThread(self.build_thread)

        self.build_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_build_complete)

        # cleanup
        self.worker.finished.connect(self.build_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.build_thread.finished.connect(self.build_thread.deleteLater)

        self.build_thread.start()

    def on_build_complete(self, ret, out, err):
        # 🔑 ONLY emit — NO UI CODE HERE
        self.build_complete_signal.emit(ret, out, err)

    def _on_build_complete_ui(self, ret, out, err):
        app = self.app

        if ret == 0:
            app.last_build_seconds = int(time.time() - app.build_start_time)
            msg = "Build complete."
            app.status_label.setStyleSheet("""
                QLabel {
                    background-color: #FFFFFF;
                    color: #3bbf3b;
                    border: 1px solid #3a3a3a;
                }
            """)
            if getattr(app, "minimize_after_build_enabled", False):
                app.showMinimized()
            if getattr(app, "close_after_build_enabled", False):
                app.close_app()
            app.state_ctrl.save_state()

        else:
            msg = "Build failed. See debug log."
            app.status_label.setStyleSheet("""
                QLabel {
                    background-color: #FFFFFF;
                    color: #be1a1a;
                    border: 1px solid #3a3a3a;
                }
            """)

        self.stop_eta()
        app.building = False
        app.build_process = None

        app._status_lock = True
        app.status_label.setText(msg)
        app.validation_controller.update_build_button()
        
            
        QTimer.singleShot(5000, self._unlock_status)

    def _unlock_status(self):
        app = self.app
        app._status_lock = False
        app.validation_controller.update_ui_state()

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
        self.app.status_label.setFixedSize(200,100)

        QTimer.singleShot(1, self.update_eta_loop)


class BuildWorker(QObject):
    finished = Signal(int, str, str)  # ret, stdout, stderr

    def __init__(self, app, cmd):
        super().__init__()
        self.app = app
        self.cmd = cmd

    def run(self):
        try:
            with open(self.app.debug_log_path, "a", encoding="utf-8") as f:
                f.write("ENTERED run_build\n")
                f.write("CMD: " + " ".join(self.cmd) + "\n")

            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=CREATE_NO_WINDOW
            )

            self.app.build_process = proc

            out, err = proc.communicate()
            ret = proc.returncode

            with open(self.app.debug_log_path, "a", encoding="utf-8") as f:
                f.write(f"RETURN CODE: {ret}\n")
                f.write("STDERR:\n" + (err or "<empty>") + "\n")

        except Exception as e:
            ret = -1
            out = ""
            err = str(e)

        self.finished.emit(ret, out, err)