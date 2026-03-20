
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class DependencyPopup:
    def __init__(self, app):
        self.app = app
        self.popup = None

    # =============================================================
    # Dependency Popup (PySide6)
    # =============================================================

    def build_dependency_popup(self, packages: list[str]):
        if not packages:
            return None

        # close existing popup
        if hasattr(self, "popup") and self.popup:
            self.popup.close()

        popup = QDialog(self.app)
        popup.setFixedSize(300, 300)
        popup.setWindowTitle("Dependency Notice")
        popup.setModal(False)
        popup.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        layout = QVBoxLayout(popup)

        label1 = QLabel(
            "This script references the following external packages:"
        )
        label1.setWordWrap(True)
        label1.setFont(QFont("Rubik UI", 11, QFont.Bold))
        layout.addWidget(label1)

        pkg_text = ", ".join(packages)

        label2 = QLabel(pkg_text)
        label2.setWordWrap(True)
        label2.setFont(QFont("Rubik UI", 11, QFont.Bold))
        layout.addWidget(label2)

        label3 = QLabel(
            "Ensure they are installed in the selected Python environment. "
            "E.g. py -3.13 -m pip install <package-name>."
        )
        label3.setWordWrap(True)
        label3.setFont(QFont("Rubik UI", 11, QFont.Bold))
        layout.addWidget(label3)

        ok_btn = QPushButton("OK")
        ok_btn.setFixedWidth(80)
        ok_btn.clicked.connect(popup.close)
        layout.addWidget(ok_btn, alignment=Qt.AlignHCenter)

        # Position
        popup.adjustSize()
        x = self.app.x() + self.app.width() + 10
        y = self.app.y() + 50
        popup.move(x, y)

        self.popup = popup
        return popup

    def show_dependency_warning_popup(self, packages: list[str]):
        if not getattr(self.app, "dependency_notice_enabled", True):
            if hasattr(self, "popup") and self.popup:
                self.popup.close()
            return

        popup = self.build_dependency_popup(packages)

        if popup:
            popup.show()