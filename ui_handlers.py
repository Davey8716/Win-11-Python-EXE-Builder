
import os,webbrowser
from ui_highlights import flash_delete_highlight

class UIHandlers:
    def __init__(self, app):
        self.app = app


    def get_desktop_path(self):
        return os.path.join(os.path.expanduser("~"), "Desktop")

    def clear_interpreter_path(self):
        app = self.app
        flash_delete_highlight(
            getattr(app, "interpreter_refresh_btn", None),
            getattr(app, "python_entry_input", None),
        )

        # -------------------------------
        # CLEAR STATE (source of truth FIRST)
        # -------------------------------
        app.python_interpreter_path = ""
        app.python_path = ""
        app.interpreter_user_cleared = True

        # -------------------------------
        # CLEAR UI
        # -------------------------------
        if hasattr(app, "python_entry_input"):
            app.python_entry_input.clear()

        # reset dropdown safely
        if hasattr(app, "select_interpreter"):
            app.select_interpreter.blockSignals(True)
            app.select_interpreter.setCurrentIndex(0)
            app.select_interpreter.blockSignals(False)

        # -------------------------------
        # SAVE STATE
        # -------------------------------
        app.state_ctrl.save_state()

        # -------------------------------
        # FORCE UI UPDATE (ORDER MATTERS)
        # -------------------------------
        app.validator.validation_status_message()
        app.validator.update_ui_state()

    def clear_script_path(self):
        app = self.app
        flash_delete_highlight(
            getattr(app, "script_clear_btn", None),
            getattr(app, "script_path_input", None),
        )

        # -------------------------------
        # CLEAR STATE FIRST
        # -------------------------------
        app.entry_script = None
        app.project_root = None
        app.script_path = ""
        app.script_user_cleared = True

        # -------------------------------
        # CLEAR UI
        # -------------------------------
        if hasattr(app, "script_path_input"):
            app.script_path_input.clear()

        # -------------------------------
        # SAVE STATE
        # -------------------------------
        app.state_ctrl.save_state()

        # -------------------------------
        # FORCE UI UPDATE
        # -------------------------------
        app.validator.validation_status_message()
        app.validator.update_ui_state()

    def clear_icon(self):
        app = self.app
        flash_delete_highlight(
            getattr(app, "icon_clear_btn", None),
            getattr(app, "icon_path_input", None),
        )

        # -------------------------------
        # CLEAR STATE FIRST
        # -------------------------------
        app.icon_path = ""
        app.icon_user_cleared = True

        # 🔑 prevent signal loop
        if hasattr(app, "select_recent_icons"):
            app.select_recent_icons.blockSignals(True)
            app.select_recent_icons.setCurrentIndex(1)  # "No Icon"
            app.select_recent_icons.blockSignals(False)

        # -------------------------------
        # CLEAR UI
        # -------------------------------
        if hasattr(app, "icon_path_input"):
            app.icon_path_input.clear()

        # -------------------------------
        # SAVE STATE
        # -------------------------------
        app.state_ctrl.save_state()

        # -------------------------------
        # FORCE UI UPDATE
        # -------------------------------
        app.validator.validation_status_message()
        app.validator.update_ui_state()
        
    def reset_output_to_desktop(self):
        app = self.app
        flash_delete_highlight(
            getattr(app, "output_refresh_btn", None),
            getattr(app, "output_path_input", None),
        )
        app.build_error = None
        desktop = self.get_desktop_path()
        app.output_path_input.setText(desktop)
        app.output_path = desktop
        app.state_ctrl.save_state()
        app.validation_controller.update_ui_state()
    
    def reset_exe_name_from_script(self):
        app = self.app
        script = app.entry_script
        if not script or not os.path.isfile(script):
            return

        flash_delete_highlight(
            getattr(app, "refresh_btn", None),
            getattr(app, "exe_name_input", None),
        )
        derived = os.path.splitext(os.path.basename(script))[0]
        app.exe_name_user_modified = False
        app.exe_name_input.setText(derived)
        app.state_ctrl.save_state()
        
    def on_dependency_toggle(self, state):
        app = self.app
        app.dependency_notice_enabled = bool(state)

        script = app.entry_script

        # 🔒 TURN OFF → close popup immediately
        if not app.dependency_notice_enabled:
            popup_ctrl = getattr(app, "ui_dependency_popup", None)

            if popup_ctrl and popup_ctrl.popup:
                popup_ctrl.popup.close()
                popup_ctrl.popup = None

            app._dependency_popup_shown = True  # block further triggers
            app.state_ctrl.save_state()
            return

        # 🔑 TURN ON → re-run advisory
        if script and os.path.isfile(script):
            app._dependency_popup_shown = False  # allow popup again
            app._dep_last_requested = None   # 🔑 REQUIRED RESET
            app.validation_controller.run_dependency_advisory_async(script)

        app.state_ctrl.save_state()
    
    def on_tooltips_toggle(self, state):
        app = self.app
        app.tooltips_enabled = bool(state)
        app.state_ctrl.save_state()

    def on_minimize_toggle(self, state):
        app = self.app
        app.minimize_after_build_enabled = bool(state)

        # 🔑 enforce mutual exclusion immediately
        if state:
            app.close_after_build.setChecked(False)
            app.close_after_build_enabled = False

        app.state_ctrl.save_state()
        app.validator.update_ui_state()   # 🔑 THIS WAS MISSING

    def on_close_toggle(self, state):
        app = self.app
        app.close_after_build_enabled = bool(state)

        # 🔑 enforce mutual exclusion immediately
        if state:
            app.minimize_after_build.setChecked(False)
            app.minimize_after_build_enabled = False

        app.state_ctrl.save_state()
        app.validator.update_ui_state()   
        
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

        app.exe_name = value  # 🔑 ensure source of truth is updated
        app.state_ctrl.save_state()

    def on_datetime_format_changed(self, index):
        app = self.app

        data = app.date_time_dropdown.currentData()

        if data is None:
            # 🔴 OFF (None selected)
            app.append_datetime = False
            app.datetime_format = ""

            # visually set to "None" (index 2 in your setup)
            if app.date_time_dropdown.currentIndex() != 2:
                app.date_time_dropdown.blockSignals(True)
                app.date_time_dropdown.setCurrentIndex(2)
                app.date_time_dropdown.blockSignals(False)

        else:
            # 🟢 ON
            app.append_datetime = True
            app.datetime_format = data

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
