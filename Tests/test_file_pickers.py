import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

import file_pickers
from file_pickers import ScriptPickerPopup
from styles import Colors


def _qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_script_picker_popup_styles_native_title_bar(monkeypatch, tmp_path):
    _qapp()
    style_calls = []

    def record_native_title_style(dialog, caption=None, text=None, border=None):
        style_calls.append(
            {
                "dialog": dialog,
                "caption": caption,
                "text": text,
                "border": border,
            }
        )

    monkeypatch.setattr(
        file_pickers,
        "apply_native_title_bar_style",
        record_native_title_style,
    )

    parent = QWidget()
    parent.setGeometry(10, 20, 100, 80)
    selected_paths = []

    popup = ScriptPickerPopup(
        parent=parent,
        folder_path=str(tmp_path),
        py_files=["app.py", "main.py"],
        callback=selected_paths.append,
    )

    try:
        flags = popup.windowFlags()

        assert popup.windowTitle() == "Select Entry Script"
        assert popup.width() == 300
        assert popup.height() == 200
        assert popup.dropdown.count() == 2
        assert bool(flags & Qt.WindowMinimizeButtonHint)
        assert bool(flags & Qt.WindowCloseButtonHint)
        assert not bool(flags & Qt.WindowContextHelpButtonHint)
        assert style_calls == [
            {
                "dialog": popup,
                "caption": Colors.PANEL_BG,
                "text": None,
                "border": Colors.PANEL_BG,
            }
        ]
    finally:
        popup.close()
        parent.close()


def test_script_picker_popup_confirm_returns_selected_script(monkeypatch, tmp_path):
    _qapp()
    monkeypatch.setattr(file_pickers, "apply_native_title_bar_style", lambda *args, **kwargs: None)

    parent = QWidget()
    selected_paths = []
    popup = ScriptPickerPopup(
        parent=parent,
        folder_path=str(tmp_path),
        py_files=["app.py", "main.py"],
        callback=selected_paths.append,
    )

    try:
        popup.dropdown.setCurrentText("main.py")
        popup.confirm()

        assert selected_paths == [os.path.normpath(str(tmp_path / "main.py"))]
    finally:
        popup.close()
        parent.close()
