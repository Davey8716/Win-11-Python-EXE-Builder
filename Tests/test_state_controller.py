import json
import os
from types import SimpleNamespace

from state_controller import StateController


def make_app(**overrides):
    app = SimpleNamespace(
        script_path="",
        icon_path="",
        output_path="",
        python_interpreter_path="",
        exe_name="",
        last_build_seconds=45,
        state_data={},
    )

    for name, value in overrides.items():
        setattr(app, name, value)

    return app


class DummyCheckbox:
    def __init__(self):
        self.checked = None

    def blockSignals(self, _value):
        pass

    def setChecked(self, value):
        self.checked = value


class DummyInput:
    def __init__(self):
        self.value = ""

    def blockSignals(self, _value):
        pass

    def setText(self, value):
        self.value = value

    def set_display_path(self, value):
        self.value = value


class DummyValidator:
    def update_ui_state(self):
        pass


def test_state_file_path_uses_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    controller = StateController(make_app())

    state_path = controller._state_file_path()

    assert state_path == os.path.join(str(tmp_path), "EXEBuilder", "exe_builder_state.json")
    assert os.path.isdir(os.path.dirname(state_path))


def test_save_state_writes_current_values_and_preserves_recents(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        script_path=str(tmp_path / "project" / ".." / "project" / "main.py"),
        icon_path=str(tmp_path / "icon.ico"),
        output_path=str(tmp_path / "dist"),
        python_interpreter_path=str(tmp_path / "Python314" / "python.exe"),
        exe_name="Builder",
        state_data={
            "recent_scripts": ["one.py"],
            "recent_icons": ["icon.ico"],
            "recent_interpreters": ["python.exe"],
        },
    )

    controller = StateController(app)
    controller.save_state()

    with open(controller._state_file_path(), "r", encoding="utf-8") as state_file:
        data = json.load(state_file)

    assert data["last_script_path"] == os.path.normpath(app.script_path)
    assert data["python_interpreter_path"] == os.path.normpath(app.python_interpreter_path)
    assert data["last_exe_name"] == "Builder"
    assert data["recent_scripts"] == ["one.py"]
    assert data["recent_icons"] == ["icon.ico"]
    assert data["recent_interpreters"] == ["python.exe"]
    assert data["open_output_dir_after_build_enabled"] is False


def test_save_state_persists_open_output_directory_toggle(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(open_output_dir_after_build_enabled=True)

    controller = StateController(app)
    controller.save_state()

    with open(controller._state_file_path(), "r", encoding="utf-8") as state_file:
        data = json.load(state_file)

    assert data["open_output_dir_after_build_enabled"] is True


def test_load_state_restores_open_output_directory_toggle(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        tooltips_checkbox=DummyCheckbox(),
        dependency_notice=DummyCheckbox(),
        close_after_build=DummyCheckbox(),
        minimize_after_build=DummyCheckbox(),
        open_output_dir_after_build=DummyCheckbox(),
        script_path_input=DummyInput(),
        icon_path_input=DummyInput(),
        output_path_input=DummyInput(),
        exe_name_input=DummyInput(),
        python_entry_input=DummyInput(),
        validator=DummyValidator(),
    )
    controller = StateController(app)

    state_path = controller._state_file_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as state_file:
        json.dump({"open_output_dir_after_build_enabled": True}, state_file)

    controller.load_state()

    assert app.open_output_dir_after_build_enabled is True
    assert app.open_output_dir_after_build.checked is True
