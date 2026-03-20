from PySide6.QtCore import QObject, QEvent, QTimer, QPoint
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import Qt

# -------------------------------------------------------------
#  Simple tooltip class for Qt widgets (qt_material compatible)
# -------------------------------------------------------------
class QtTooltip(QObject):
    def __init__(self, widget, text, delay=500):
        super().__init__(widget)

        self.widget = widget
        self.text = text
        self.delay = delay

        self.tip_window = None
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show)

        # Install event filter instead of Tk bindings
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.widget:
            if event.type() == QEvent.Enter:
                self.schedule()
            elif event.type() == QEvent.Leave:
                self.hide()
            elif event.type() == QEvent.MouseButtonPress:
                self.hide()
        return super().eventFilter(obj, event)

    def schedule(self):
        self.timer.stop()
        self.timer.start(self.delay)

    def show(self):
        # Global toggle (match your existing pattern)
        root = self.widget.window()
        if hasattr(root, "tooltips_enabled"):
            if not root.tooltips_enabled:
                return

        if self.tip_window:
            return

        self.tip_window = QLabel(self.text, None)
        self.tip_window.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )

        # Styling (qt_material-friendly)
        self.tip_window.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                color: white;
                border: 1px solid #444;
                padding: 6px;
                border-radius: 4px;
                font-family: "Rubik";
                font-size: 13px;
            }
        """)

        self.tip_window.adjustSize()

        # Position relative to widget (same offsets as before)
        pos = self.widget.mapToGlobal(QPoint(40, 25))
        self.tip_window.move(pos)

        self.tip_window.show()

    def hide(self):
        self.timer.stop()

        if self.tip_window:
            self.tip_window.close()
            self.tip_window = None


# -------------------------------------------------------------
#  Tooltip wiring (UI → text mapping) [Qt version]
# -------------------------------------------------------------

def attach_tooltips(app):
    """
    Attach all tooltips to the EXEBuilderApp instance.
    Assumes widgets already exist on `app`.
    """

    # -----------------------------
    # Title / global controls
    # -----------------------------

    QtTooltip(
        app.tooltips_checkbox,
        "Toggle all tooltips on or off.\n"
        "Turn this off once you’re familiar with the interface."
    )

    # -----------------------------
    # Script picker
    # -----------------------------

    QtTooltip(
        app.script_path_input,
        "File path to python script folder and file."
    )

    QtTooltip(
        app.apps_btn,
        "Opens Windows Installed Apps.\n"
        "Check or remove Python versions.\n"
        "If builds fail due to environment issues,\n"
        "Go to python.org for downloading specific releases."
    )
    
    QtTooltip(
        app.open_python_site_btn,
        "Direct link to python.org."
    )

    QtTooltip(
        app.folder_btn,
        "Select a folder containing one or more Python files.\n"
        "If the folder contains only one .py file, it will be used automatically.\n"
        "If multiple .py files are found, a popup will appear.\n"
        "allowing you to choose the main entry script."
    )
    
    QtTooltip(
        app.recent_folder_dropdown,
        "Select a recent python main file from this drop down list."
    )

    # -----------------------------
    # Python interpreter
    # -----------------------------

    QtTooltip(
        app.interpreter_btn,
        "Select the Python interpreter used to build EXEs.\n"
        "This determines which Python installation PyInstaller runs under."
    )

    QtTooltip(
        app.python_entry_input,
        "Displays the full path to the Python interpreter.\n"
        "That will be used for building EXEs.\n"
        "This is read only.\n"
        "Once a path has been set the navigation is locked to where pyton interpreters are.\n"
    )

    # -----------------------------
    # Icon picker
    # -----------------------------

    QtTooltip(
        app.icon_btn,
        "Choose a .ico file to use as your EXE’s icon.\n"
        "Optional — PyInstaller uses a default icon otherwise."
    )

    QtTooltip(
        app.ico_convert_btn,
        "Opens 3 websites that convert PNG/JPG images into .ico files\n"
        "for use as custom EXE icons."
    )

    QtTooltip(
        app.icon_path_input,
        "File path to Icon if used."
    )
    
    QtTooltip(
        app.script_clear_btn,
        "Clear selected script/folder."
    ) 

    QtTooltip(
        app.icon_clear_btn,
        "Clear icon (build without an icon)."
    )

    # -----------------------------
    # Output / EXE name
    # -----------------------------

    QtTooltip(
        app.output_btn,
        "The file path to the folder the EXE is to be built in."
    )

    QtTooltip(
        app.output_path_input,
        "File path to the EXE output folder."
    )

    QtTooltip(
        app.output_refresh_btn,
        "Reset output folder to Desktop."
    )

    QtTooltip(
        app.exe_name_input,
        "Name of the generated EXE folder and file.\n"
        "Do not include .exe."
    )

    QtTooltip(
        app.refresh_btn,
        "Reset EXE name to match the entry script name.\n"
        "A python folder must be selected to for this to be ungreyed and resetable.\n"
    )

    # -----------------------------
    # Build
    # -----------------------------

    QtTooltip(
        app.build_btn,
        "Builds your Python project into a standalone Windows EXE using PyInstaller."
    )

