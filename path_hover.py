import os

from PySide6.QtCore import QObject, QEvent, QTimer, QPoint
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QLabel

from styles import TOOLTIP_STYLE


class PathHover(QObject):
    def __init__(self, widget, delay=350):
        super().__init__(widget)
        self.widget = widget
        self.delay = delay
        self.tip_window = None

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show)

        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.widget:
            if event.type() == QEvent.Enter:
                self.schedule()
            elif event.type() in {
                QEvent.Leave,
                QEvent.MouseButtonPress,
                QEvent.FocusOut,
                QEvent.Hide,
                QEvent.WindowDeactivate,
            }:
                self.hide()
        return super().eventFilter(obj, event)

    def schedule(self):
        self.timer.stop()
        self.timer.start(self.delay)

    def show(self):
        text_getter = getattr(self.widget, "text", None)
        if not callable(text_getter):
            return

        raw_text = text_getter().strip()
        if not raw_text:
            return

        full_path = os.path.normpath(raw_text)

        if self.tip_window is not None:
            if self.tip_window.text() == full_path:
                return
            self.hide()

        self.tip_window = QLabel(full_path, None)
        self.tip_window.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.tip_window.setStyleSheet(TOOLTIP_STYLE)
        self.tip_window.adjustSize()

        pos = self.widget.mapToGlobal(QPoint(40, 25))
        self.tip_window.move(pos)
        self.tip_window.show()

    def hide(self):
        self.timer.stop()
        if self.tip_window:
            self.tip_window.close()
            self.tip_window = None


def attach_path_hovers(app):
    app._path_hovers = [
        PathHover(app.python_entry_input),
        PathHover(app.icon_path_input),
        PathHover(app.script_path_input),
        PathHover(app.output_path_input),
    ]
