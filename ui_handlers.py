# def clear_script_path():
#             self.script_path_input.clear()
#             self.entry_script = None
#             self.project_root = None
#             self.script_path = ""
#             self.state_ctrl.save_state()
#             self.validator.update_build_button_state()
            
# def clear_icon():
#             self.icon_path_input.clear()
#             self.icon_path = ""
#             self.state_ctrl.save_state()
#             self.validator.update_build_button_state()
            
# def reset_output_to_desktop():
#             desktop = get_desktop_path()
#             self.output_path_input.setText(desktop)
#             self.output_path = desktop
#             self.state_ctrl.save_state()
#             self.validator.update_build_button_state()
            
# def reset_exe_name_from_script():
#             script = self.entry_script
#             if not script or not os.path.isfile(script):
#                 return

#             derived = os.path.splitext(os.path.basename(script))[0]

#             self.exe_name_user_modified = False
#             self.exe_name_input.setText(derived)

#             self.state_ctrl.save_state()
#             self.validator.update_build_button_state()
            
# def on_dependency_toggle(state):
#             self.dependency_notice_enabled = bool(state)

#             # -------------------------
#             # ON → show popup
#             # -------------------------
#             if self.dependency_notice_enabled:
#                 script = self.script_path

#                 if script and os.path.isfile(script):
#                     packages = self.validator.run_dependency_advisory(script)

#                     if packages:
#                         self.show_dependency_warning_popup(packages)

#             # -------------------------
#             # OFF → close popup
#             # -------------------------
#             else:
#                 if hasattr(self, "popup") and self.popup:
#                     self.popup.close()

#             self.state_ctrl.save_state()

# def on_tooltips_toggle(state):
#             self.tooltips_enabled = bool(state)
#             self.state_ctrl.save_state()


# def on_script_path_change(text):
#     if getattr(self, "_loading_state", False):
#         return

#     value = text.strip()

#     if not value:
#         self.entry_script = None
#         self.project_root = None

#         # ✅ clear dependent fields
#         if hasattr(self, "output_path_input"):
#             self.output_path_input.clear()
#         self.output_path = ""

#         if hasattr(self, "exe_name_input"):
#             self.exe_name_input.clear()
#         self.exe_name = ""

#         self.state_ctrl.save_state()

#     self.validator.update_build_button_state()
    
# # =============================================================
# # EXE name cleared by USER
# # =============================================================

# def on_exe_name_change(text):
#     if self._loading_state:
#         return

#     value = text.strip()
#     if not value:
#         self.state_ctrl.save_state()

#     self.validator.update_build_button_state()
    
# def _on_exe_name_user_edit(text):
#     if self._loading_state:
#         return
#     self.exe_name_user_modified = True


# def open_python_site():
#     webbrowser.open("https://www.python.org")

# def open_icon_sites():
#             urls = [
#                 "https://convertico.com/",
#                 "https://cloudconvert.com/png-to-ico",
#                 "https://www.icoconverter.com/"
#             ]
#             for url in urls:
#                 webbrowser.open(url)


import os,webbrowser
from utils import *

class UIHandlers:
    def __init__(self, app):
        self.app = app

    def clear_script_path(self):
        app = self.app
        app.script_path_input.clear()
        app.entry_script = None
        app.project_root = None
        app.script_path = ""
        app.state_ctrl.save_state()
        app.validator.update_build_button_state()
            
    def clear_icon(self):
        app = self.app
        app.icon_path_input.clear()
        app.icon_path = ""
        app.state_ctrl.save_state()
        app.validator.update_build_button_state()
            
    def reset_output_to_desktop(self):
        app = self.app
        desktop = get_desktop_path()
        app.output_path_input.setText(desktop)
        app.output_path = desktop
        app.state_ctrl.save_state()
        app.validator.update_build_button_state()
            
    def reset_exe_name_from_script(self):
        app = self.app
        script = app.entry_script
        if not script or not os.path.isfile(script):
            return

        derived = os.path.splitext(os.path.basename(script))[0]

        app.exe_name_user_modified = False
        app.exe_name_input.setText(derived)

        app.state_ctrl.save_state()
        app.validator.update_build_button_state()
            
    def on_dependency_toggle(self, state):
        app = self.app
        app.dependency_notice_enabled = bool(state)

        # -------------------------
        # ON → show popup
        # -------------------------
        if app.dependency_notice_enabled:
            script = app.script_path

            if script and os.path.isfile(script):
                packages = app.validator.run_dependency_advisory(script)

                if packages:
                    self.app.ui_dependency_popup.show_dependency_warning_popup(packages)

        # -------------------------
        # OFF → close popup
        # -------------------------
        else:
            if hasattr(app, "popup") and app.popup:
                app.popup.close()

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

        app.validator.update_build_button_state()
    
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

        app.validator.update_build_button_state()
    
    def _on_exe_name_user_edit(self, text):
        app = self.app
        if app._loading_state:
            return
        app.exe_name_user_modified = True


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
