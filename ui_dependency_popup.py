
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton,QFrame,QTextEdit,QScrollArea
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
        popup.setFixedSize(600,800)
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

        # 🔑 SCROLL AREA
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(popup_frame)

        layout.addWidget(scroll)

        # -------------------------------
        # LEGEND FRAME
        # -------------------------------
        legend_frame = QFrame()
        legend_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #3a3a3a;
                background-color: #F3F2F2;
                border-radius: 4px;
            }
        """)
        legend_frame.setFixedSize(260,160)

        legend_layout = QVBoxLayout(legend_frame)
        legend_layout.setContentsMargins(6, 6, 6, 6)
        legend_layout.setSpacing(2)

        legend_title = QLabel("Legend")
        legend_title.setFont(QFont("Rubik UI", 11, QFont.Bold))
        legend_layout.addWidget(legend_title)

        legend_items = [
            ("✔ External dependency", "#3bbf3b"),
            ("⚠ May be required (check)", "#e6a23c"),
            ("? Uncertain / optional", "#8a8a8a"),
        ]

        for text, color in legend_items:
            lbl = QLabel(text)
            lbl.setFont(QFont("Rubik UI", 12, QFont.Bold))
            lbl.setStyleSheet(f"color: {color};")
            legend_layout.addWidget(lbl)

        frame_layout.addWidget(legend_frame)

        # -------------------------------
        # CONTENT (INSIDE FRAME)
        # -------------------------------

        label1 = QLabel(
            "This script references the following external packages:"
        )
        label1.setWordWrap(True)
        label1.setFont(QFont("Rubik UI", 12, QFont.Bold))
        label1.setContentsMargins(5,5,5,5)
        label1.setFixedSize(400,60)
        frame_layout.addWidget(label1)

        def make_section(title, items, color):
            if not items:
                return None

            text = "\n".join(items)

            box = QTextEdit()
            box.setReadOnly(True)
            box.setText(f"{title}:\n{text}")
            box.setFont(QFont("Rubik UI", 12, QFont.Bold))
            box.setStyleSheet(f"""
                QTextEdit {{
                    color: {color};
                    background-color: #F3F2F2;
                    border: 1px solid #8a8a8a;
                }}
            """)
            box.setMinimumHeight(80)

            return box

        sections = [
            ("✔ External", packages.get("external", []), "#3bbf3b"),
            ("⚠ Check", packages.get("maybe", []), "#e6a23c"),
            ("? Uncertain", packages.get("uncertain", []), "#8a8a8a"),
        ]

        for title, items, color in sections:
            section = make_section(title, items, color)
            if section:
                frame_layout.addWidget(section)

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