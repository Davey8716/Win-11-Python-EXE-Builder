import ctypes

class ActivationController:
    def __init__(self, app):
        """
        app = EXEBuilderApp instance
        """
        self.app = app

    # ============================================================
    # Listen for activation + bring window to front
    # ============================================================

    def listen_for_activation(self):
        while True:
            ctypes.windll.kernel32.WaitForSingleObject(
                self.app.activate_event, -1
            )
            self.app.after(0, self.bring_to_front)

    def bring_to_front(self):
        try:
            self.app.deiconify()
            self.app.lift()
            self.app.focus_force()
        except Exception:
            pass
