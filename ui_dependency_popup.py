
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton,QFrame
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
        popup.setFixedSize(500,500)
        popup.setWindowTitle("Dependency Notice")
        popup.setModal(False)
        popup.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        # 🔑 main layout
        layout = QVBoxLayout(popup)

        # 🔑 frame
        popup_frame = QFrame()
        popup_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #3a3a3a;
                border-radius: 6px;
                background-color: #DCDBDB;
            }
        """)

        frame_layout = QVBoxLayout(popup_frame)
        frame_layout.setContentsMargins(10, 10, 10, 10)
        frame_layout.setSpacing(8)

        layout.addWidget(popup_frame)

        # -------------------------------
        # CONTENT (INSIDE FRAME)
        # -------------------------------

        label1 = QLabel(
            "This script references the following external packages:"
        )
        label1.setWordWrap(True)
        label1.setFont(QFont("Rubik UI", 11, QFont.Bold))
        label1.setContentsMargins(5,5,5,5)
        frame_layout.addWidget(label1)

        pkg_text = ", ".join(packages)

        label2 = QLabel(pkg_text)
        label2.setWordWrap(True)
        label2.setFont(QFont("Rubik UI", 11, QFont.Bold))
        label2.setContentsMargins(5,5,5,5)
        frame_layout.addWidget(label2)

        label3 = QLabel(
            "Ensure they are installed in the selected Python environment. "
            "E.g. py -3.13 -m pip install <package-name>."
        )
        label3.setWordWrap(True)
        label3.setFont(QFont("Rubik UI", 11, QFont.Bold))
        label3.setContentsMargins(5,5,5,5)
        frame_layout.addWidget(label3)

        ok_btn = QPushButton("OK")
        ok_btn.setFont(QFont("Rubik UI", 13, QFont.Bold))
        ok_btn.setFixedSize(80, 30)

        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #3bbf3b;
                color: #000000;
                border: 1px solid #000000;
            }
            QPushButton:hover {
                background-color: #2e9e2e;
            }
            QPushButton:disabled {
                background-color: #8a8a8a;
                color: #444;
            }
        """)

        ok_btn.clicked.connect(popup.close)
        frame_layout.addWidget(ok_btn, alignment=Qt.AlignHCenter)

        # Position
        popup.adjustSize()
        x = self.app.x() + self.app.width() + 10
        y = self.app.y() + 50
        popup.move(x, y)

        self.popup = popup
        return popup

    def show_dependency_warning_popup(self, packages: list[str]):
    # 🔒 If disabled → force close
        if not getattr(self.app, "dependency_notice_enabled", True):
            if hasattr(self, "popup") and self.popup:
                self.popup.close()
                self.popup = None
            return

        # 🔑 Always replace existing popup
        if hasattr(self, "popup") and self.popup:
            self.popup.close()
            self.popup = None

        self.popup = self.build_dependency_popup(packages)

        if self.popup:
            self.popup.show()