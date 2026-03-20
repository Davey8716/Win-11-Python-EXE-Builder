
from PySide6.QtCore import QTimer


class BuildUIController:
    def __init__(self, app):
        self.app = app

    def set_controls_enabled(self, enabled: bool):

        # 🔒 LOCK DURING BUILD
        locked_controls = [
            self.app.script_clear_btn,
            self.app.icon_clear_btn,
            self.app.output_refresh_btn,
            self.app.refresh_btn,   # exe name reset
        ]

        for btn in locked_controls:
            btn.setEnabled(enabled)

    # ==================================================
    # UI RESTORE: Build finished / aborted / cancelled
    # ==================================================

    def restore_build_ui(self):
        self.app.building = False
        self.set_controls_enabled(True)
        self.app._eta_running = False

        # -------------------------------
        # Restore Build buttonet_controls_enable
        # -------------------------------

        try:
            self.app.build_btn.clicked.disconnect()
        except:
            pass

        self.app.build_btn.setText("Build EXE")
        self.app.build_btn.setStyleSheet("background-color: #3bbf3b;")
        self.app.build_btn.clicked.connect(self.app.build_controller.build_exe)

        # -------------------------------
        # Re-enable recovery buttons
        # -------------------------------

        if hasattr(self.app, "output_refresh_btn"):
            self.app.output_refresh_btn.setEnabled(True)

        if hasattr(self.app, "icon_clear_btn"):
            self.app.icon_clear_btn.setEnabled(True)

        # -------------------------------
        # Re-apply validation policy
        # -------------------------------
        # 🔑 FORCE validation AFTER unlock
        QTimer.singleShot(0, self.app.validator.update_build_button_state)