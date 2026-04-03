
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

    def _close_and_disable(self):
        app = self.app

        # close popup safely
        if self.popup:
            self.popup.close()
            self.popup = None

        # 🔑 sync toggle + state
        app.dependency_notice.setChecked(False)
        app.dependency_notice_enabled = False

        if hasattr(app, "state_ctrl"):
            app.state_ctrl.save_state()

    def build_dependency_popup(self, packages: list[str]):
        if not packages:
            return None

        # close existing popup
        if hasattr(self, "popup") and self.popup:
            self.popup.close()

        popup = QDialog(self.app)
        popup.setFixedSize(420,800)
        popup.setWindowTitle("Dependency Notice")
        popup.setModal(False)
        popup.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        # 🔑 main layout
        layout = QVBoxLayout(popup)

        # 🔑 frame
        popup_frame = QFrame()
        popup_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #3a3a3a;
                border-radius: 4px;
                background-color: #8A8A8A;
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
        # BUILD REQUIREMENTS (NEW)
        # -------------------------------

        build_frame = QFrame()
        build_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #000000;
                background-color: #F3F2F2;
                border-radius: 4px;
            }
        """)
        build_frame.setFixedSize(230,90)

        build_layout = QVBoxLayout(build_frame)
        build_layout.setContentsMargins(6, 6, 6, 6)
        build_layout.setSpacing(2)

        build_title = QLabel("Build Requirements")
        build_title.setFont(QFont("Rubik UI", 12, QFont.Bold))
        build_layout.addWidget(build_title)

        build_text = QLabel("PyInstaller\n(required to build the .exe)")
        build_text.setFont(QFont("Rubik UI", 11, QFont.Bold))
        build_text.setStyleSheet("color: #2a7fff;")
        build_layout.addWidget(build_text)

        frame_layout.addWidget(build_frame)

        # -------------------------------
        # LEGEND FRAME
        # -------------------------------
        legend_frame = QFrame()
        legend_frame.setStyleSheet("""
            QFrame {
                border: 3px solid #000000;
                background-color: #F3F2F2;
                border-radius: 4px;
            }
        """)
        legend_frame.setFixedSize(240,160)

        legend_layout = QVBoxLayout(legend_frame)
        legend_layout.setContentsMargins(6, 6, 6, 6)
        legend_layout.setSpacing(2)

        legend_title = QLabel("Legend")
        legend_title.setFont(QFont("Rubik UI", 12, QFont.Bold))
        legend_layout.addWidget(legend_title)

        legend_items = [
            ("✔ External dependency", "#2a7fff"),
            ("⚠ May be required (check)", "#e6a23c"),
            ("? Uncertain / optional", "#8a8a8a"),
        ]

        for text, color in legend_items:
            lbl = QLabel(text)
            lbl.setFont(QFont("Rubik UI", 11, QFont.Bold))
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
        label1.setFont(QFont("Rubik UI", 11, QFont.Bold))
        label1.setContentsMargins(5,5,5,5)
        label1.setFixedSize(360,50)
        label1.setStyleSheet("""
            QLabel {
                border: 3px solid #000000;
                border-radius: 4px;
                background-color: #FFFFFF;
            }

        """)
        frame_layout.addWidget(label1)

        def make_section(title, items, color):
            if not items:
                return None

            text = "\n".join(items)

            box = QTextEdit()
            box.setReadOnly(True)
            box.setText(f"{title}:\n{text}")
            box.setFont(QFont("Rubik UI", 11, QFont.Bold))
            box.setStyleSheet(f"""
                QTextEdit {{
                    color: {color};
                    background-color: #FFFFFF;
                    border: 1px solid #8a8a8a;
                }}
            """)
            box.setMinimumHeight(80)

            return box

        sections = [
            ("✔ External", packages.get("external", []), "#2a7fff"),
            ("⚠ Check", packages.get("maybe", []), "#e6a23c"),
            ("? Uncertain", packages.get("uncertain", []), "#8a8a8a"),
        ]

        for title, items, color in sections:
            section = make_section(title, items, color)
            if section:
                frame_layout.addWidget(section)

        label3 = QLabel(
            "Ensure they are installed in\nthe selected Python environment.\n "
            "E.g. py -3.13 -m pip install <package-name>."
        )
        label3.setWordWrap(True)
        label3.setFont(QFont("Rubik UI", 11, QFont.Bold))
        label3.setContentsMargins(5,5,5,5)
        label3.setFixedSize(285,85)
        label3.setStyleSheet("""
            QLabel {
                border: 3px solid #000000;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
        """)

        frame_layout.addWidget(label3)

        ok_btn = QPushButton("OK")
        ok_btn.setFont(QFont("Rubik UI", 12, QFont.Bold))
        ok_btn.setFixedSize(80, 30)

        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a7fff;
                color: #000000;
                border: 3px solid #000000;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #8a8a8a;
                color: #444;
            }
        """)

        ok_btn.clicked.connect(lambda: self._close_and_disable())
        popup.finished.connect(lambda: self._close_and_disable())
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