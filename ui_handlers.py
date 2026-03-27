
import os,webbrowser
from utils import *

class UIHandlers:
    def __init__(self, app):
        self.app = app

    def clear_interpreter_path(self):
        app = self.app

        # clear UI
        if hasattr(app, "python_entry_input"):
            app.python_entry_input.clear()

        # 🔑 reset dropdown to header (match other dropdown behaviour)
        if hasattr(app, "select_interpreter"):
            app.select_interpreter.blockSignals(True)
            app.select_interpreter.setCurrentIndex(0)
            app.select_interpreter.blockSignals(False)

        # clear state (single source of truth)
        app.python_interpreter_path = ""
        app.python_path = ""

        app.state_ctrl.save_state()

        # 🔑 force full UI + validation refresh
        app.validator.validation_status_message()
        app.validator.update_ui_state()

    def clear_script_path(self):
        app = self.app
        app.script_path_input.clear()
        app.entry_script = None
        app.project_root = None
        app.script_path = ""
        app.state_ctrl.save_state()

    def clear_icon(self):
        app = self.app
        app.icon_path_input.clear()
        app.icon_path = ""
        app.state_ctrl.save_state()
    
    def reset_output_to_desktop(self):
        app = self.app
        app.build_error = None
        desktop = get_desktop_path()
        app.output_path_input.setText(desktop)
        app.output_path = desktop
        app.state_ctrl.save_state()
    
    def reset_exe_name_from_script(self):
        app = self.app
        script = app.entry_script
        if not script or not os.path.isfile(script):
            return

        derived = os.path.splitext(os.path.basename(script))[0]
        app.exe_name_user_modified = False
        app.exe_name_input.setText(derived)
        app.state_ctrl.save_state()
        

    def on_dependency_toggle(self, state):
        app = self.app
        app.dependency_notice_enabled = bool(state)

        if app.dependency_notice_enabled:
            script = app.script_path
            if script and os.path.isfile(script):
                packages = app.validator.run_dependency_advisory(script)
                if packages:
                    self.app.ui_dependency_popup.show_dependency_warning_popup(packages)

        else:
            popup_ctrl = getattr(app, "ui_dependency_popup", None)

            if popup_ctrl and popup_ctrl.popup:
                popup_ctrl.popup.close()
                popup_ctrl.popup = None
        # 🔑 block re-trigger while disabled
        app._dependency_popup_shown = True
        app.state_ctrl.save_state()

    def on_tooltips_toggle(self, state):
        app = self.app
        app.tooltips_enabled = bool(state)
        app.state_ctrl.save_state()

    def on_script_path_change(self, text):
        app = self.app
        if getattr(app, "_loading_state", False):
            return

        value = text.strip()

        if not value:
            app.entry_script = None
            app.project_root = None

            # ✅ clear dependent fields
            if hasattr(app, "output_path_input"):
                app.output_path_input.clear()
            app.output_path = ""
            if hasattr(app, "exe_name_input"):
                app.exe_name_input.clear()
            app.exe_name = ""
            app.state_ctrl.save_state()

    # =============================================================
    # EXE name cleared by USER
    # =============================================================

    def on_exe_name_change(self, text):
        app = self.app
        if app._loading_state:
            return

        value = text.strip()
        if not value:
            app.state_ctrl.save_state()

            
        if hasattr(app, "validator"):
            app.validator.validation_status_message()
            app.validator.update_ui_state()

    def on_datetime_format_changed(self, index):
        app = self.app

        if index == 0:
            # 🔴 OFF
            app.append_datetime = False
            app.datetime_format = ""

            # visually clear selection
            app.date_time_dropdown.setCurrentIndex(0)

        else:
            # 🟢 ON
            app.append_datetime = True
            app.datetime_format = app.date_time_dropdown.currentData()

        if hasattr(app, "state_ctrl"):
            app.state_ctrl.save_state()

        if hasattr(app, "validator"):
            app.validator.validation_status_message()
            self.app.validator.update_ui_state()

    def on_append_py_version_toggle(self, checked):
        app = self.app

        app.append_py_version = checked

        if hasattr(app, "state_ctrl"):
            app.state_ctrl.save_state()

        if hasattr(app, "validator"):
            app.validator.validation_status_message()
            self.app.validator.update_ui_state()
    
    def _on_exe_name_user_edit(self, text):
        app = self.app
        if app._loading_state:
            return
        app.exe_name_user_modified = True
        if hasattr(app, "validator"):
            app.validator.validation_status_message()
            app.validator.update_ui_state()


    def open_python_site(self):
        app = self.app
        webbrowser.open("https://www.python.org")

    def open_icon_sites(self):
        app = self.app
        urls = [
            "https://convertico.com/",
            "https://cloudconvert.com/png-to-ico",
            "https://www.icoconverter.com/"
        ]
        for url in urls:
            webbrowser.open(url)
