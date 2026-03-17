import ctypes
from PySide6.QtCore import QObject, Signal


class ActivationController(QObject):
    activate_signal = Signal()

    def __init__(self, app):
        """
        app = EXEBuilderApp instance
        """
        super().__init__()
        self.app = app

        # Connect signal → UI-safe slot
        self.activate_signal.connect(self.bring_to_front)

    # ============================================================
    # Listen for activation + bring window to front
    # ============================================================

    def listen_for_activation(self):
        while True:
            ctypes.windll.kernel32.WaitForSingleObject(
                self.app.activate_event, -1
            )

            # Emit signal instead of Tk .after()
            self.activate_signal.emit()

    def bring_to_front(self):
        try:
            window = self.app

            window.show()
            window.raise_()
            window.activateWindow()

        except Exception:
            pass