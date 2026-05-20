import json
import os
from types import SimpleNamespace

from PySide6.QtCore import Qt

from recent_controller import RecentController


class DummyDropdownItem:
    def __init__(self):
        self._flags = Qt.ItemIsEnabled

    def flags(self):
        return self._flags

    def setFlags(self, flags):
        self._flags = flags


class DummyDropdownModel:
    def __init__(self, dropdown):
        self.dropdown = dropdown

    def item(self, index):
        return self.dropdown.model_items[index]


class DummyDropdown:
    def __init__(self):
        self.items = []
        self.model_items = []
        self.signals_blocked = False

    def blockSignals(self, blocked):
        self.signals_blocked = blocked

    def clear(self):
        self.items.clear()
        self.model_items.clear()

    def addItem(self, text, data=None):
        self.items.append((text, data))
        self.model_items.append(DummyDropdownItem())

    def model(self):
        return DummyDropdownModel(self)


class DummyStateController:
    def __init__(self, state_file):
        self.state_file = state_file

    def _state_file_path(self):
        return str(self.state_file)


class DummyValidator:
    def update_ui_state(self):
        pass

    def validation_status_message(self):
        pass


def make_app(tmp_path, state_data):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps(state_data), encoding="utf-8")

    return SimpleNamespace(
        select_interpreter=DummyDropdown(),
        recent_folder_dropdown=DummyDropdown(),
        select_recent_icons=DummyDropdown(),
        state_ctrl=DummyStateController(state_file),
        validator=DummyValidator(),
        python_interpreter_path="",
        entry_script="",
        icon_path="",
    )


def test_recent_dropdown_items_are_title_case_display_only(tmp_path):
    interpreter = tmp_path / "python runtime" / "python.exe"
    script = tmp_path / "sample project" / "build_script.py"
    icon = tmp_path / "icon assets" / "app_icon.ico"

    for path in (interpreter, script, icon):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")

    interpreter_path = os.path.abspath(os.path.normpath(str(interpreter)))
    script_path = os.path.abspath(os.path.normpath(str(script)))
    icon_path = os.path.abspath(os.path.normpath(str(icon)))

    app = make_app(
        tmp_path,
        {
            "recent_interpreters": [interpreter_path],
            "recent_scripts": [script_path],
            "recent_icons": [icon_path],
        },
    )

    controller = RecentController(app)
    controller.populate_recent_interpreters_dropdown()
    controller.populate_recent_dropdown()
    controller.populate_recent_icons_dropdown()

    assert app.select_interpreter.items[0] == ("Select Recent Interpreter", None)
    assert app.select_interpreter.items[1] == (
        "1. Python Runtime\\Python.exe",
        interpreter_path,
    )

    assert app.recent_folder_dropdown.items[0] == ("Select Recent File", None)
    assert app.recent_folder_dropdown.items[1] == (
        "1. Sample Project\\Build_Script.py",
        script_path,
    )

    assert app.select_recent_icons.items[0] == ("Select Recent Icon", None)
    assert app.select_recent_icons.items[1] == ("No Icon", "")
    assert app.select_recent_icons.items[2] == (
        "1. Icon Assets\\App_Icon.ico",
        icon_path,
    )

