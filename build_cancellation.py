

import os
import psutil
import send2trash

class BuildCancellation:
    def __init__(self, app, ui):
        """
        app = core application state (processes, paths, flags)
        ui  = UI interface (restore_build_ui, set_status)
        """
        self.app = app
        self.ui = ui

    def cleanup_spec_file(self):
        path = getattr(self.app, "current_spec_path", None)
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except Exception as e:
                print("Spec cleanup failed:", e)
                
    def cancel_build(self):
        self.ui.set_status("Cancelling build...")

        # Kill PyInstaller and children
        if self.app.build_process and self.app.build_process.poll() is None:
            try:
                parent = psutil.Process(self.app.build_process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except Exception as e:
                print("Kill process error:", e)

        # Trash known build outputs
        for path in self.app.current_build_paths:
            try:
                if not path:
                    continue

                clean = os.path.normpath(path)
                if os.path.exists(clean):
                    send2trash.send2trash(clean)

            except Exception as e:
                print(f"Failed to trash {path}: {e}")

        # Trash PyInstaller build folder
        build_root = os.path.join(
            self.app.output_path_var.get(), "build"
        )

        if os.path.exists(build_root):
            for name in os.listdir(build_root):
                full = os.path.join(build_root, name)
                try:
                    send2trash.send2trash(os.path.normpath(full))
                except Exception as e:
                    print("Failed to remove:", full, e)

        # Reset build state
        self.app.build_process = None
        self.app.building = False

        # Restore UI baseline
        self.ui.restore_build_ui()
        self.ui.set_status("Build cancelled.")
        
    def abort_build(self, message):
        try:
            with open(self.app.debug_log_path, "a", encoding="utf-8") as f:
                f.write("ABORT_BUILD:\n")
                f.write(message + "\n")
        except Exception:
            pass

        self.ui.set_status(message)
        self.ui.restore_build_ui()
