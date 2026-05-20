import json
import os
from types import SimpleNamespace

from datetime_build_options import (
    ISO_MASS_DATETIME_BUILD_SENTINEL,
    MASS_DATETIME_BUILD_SENTINEL,
    UK_MASS_DATETIME_BUILD_SENTINEL,
    USA_MASS_DATETIME_BUILD_SENTINEL,
)
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


class DummyEnvironmentSyncController:
    def __init__(self, profiles=None):
        self.profiles = profiles if profiles is not None else []
        self.loaded_profiles = None
        self.update_ui = None

    def serialize_profiles(self):
        return self.profiles

    def load_serialized_profiles(self, profiles, update_ui=True):
        self.loaded_profiles = profiles
        self.update_ui = update_ui


class DummyDropdownItem:
    def __init__(self, enabled=True):
        self.enabled = enabled

    def isEnabled(self):
        return self.enabled


class DummyDropdownModel:
    def __init__(self, items):
        self.items = items

    def item(self, index):
        return self.items[index]


class DummyDropdown:
    def __init__(self, options):
        self.options = list(options)
        self.current_index = None

    def count(self):
        return len(self.options)

    def itemText(self, index):
        return self.options[index]["text"]

    def findData(self, value):
        for index, option in enumerate(self.options):
            if option["data"] == value:
                return index
        return -1

    def setCurrentIndex(self, index):
        self.current_index = index

    def currentText(self):
        if self.current_index is None:
            return ""
        return self.itemText(self.current_index)

    def model(self):
        return DummyDropdownModel(
            [DummyDropdownItem(enabled=option.get("enabled", True)) for option in self.options]
        )


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


def test_save_state_writes_environment_sync_profiles(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    env_sync_profiles = [
        {
            "version": "3.13",
            "executable": "C:/Python313/python.exe",
            "packages": {"numpy": {"name": "numpy", "version": "2.3.0"}},
            "error": "",
        }
    ]
    app = make_app(
        environment_sync_controller=DummyEnvironmentSyncController(env_sync_profiles)
    )

    controller = StateController(app)
    controller.save_state()

    with open(controller._state_file_path(), "r", encoding="utf-8") as state_file:
        data = json.load(state_file)

    assert data["env_sync_profiles"] == env_sync_profiles


def test_save_state_persists_open_output_directory_toggle(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(open_output_dir_after_build_enabled=True)

    controller = StateController(app)
    controller.save_state()

    with open(controller._state_file_path(), "r", encoding="utf-8") as state_file:
        data = json.load(state_file)

    assert data["open_output_dir_after_build_enabled"] is True


def test_save_state_does_not_persist_mass_datetime_sentinel(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        append_datetime=True,
        datetime_format=MASS_DATETIME_BUILD_SENTINEL,
    )

    controller = StateController(app)
    controller.save_state()

    with open(controller._state_file_path(), "r", encoding="utf-8") as state_file:
        data = json.load(state_file)

    assert data["append_datetime"] is False
    assert data["datetime_format"] is None


def test_save_state_does_not_persist_iso_mass_datetime_sentinel(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        append_datetime=True,
        datetime_format=ISO_MASS_DATETIME_BUILD_SENTINEL,
    )

    controller = StateController(app)
    controller.save_state()

    with open(controller._state_file_path(), "r", encoding="utf-8") as state_file:
        data = json.load(state_file)

    assert data["append_datetime"] is False
    assert data["datetime_format"] is None


def test_save_state_does_not_persist_uk_mass_datetime_sentinel(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        append_datetime=True,
        datetime_format=UK_MASS_DATETIME_BUILD_SENTINEL,
    )

    controller = StateController(app)
    controller.save_state()

    with open(controller._state_file_path(), "r", encoding="utf-8") as state_file:
        data = json.load(state_file)

    assert data["append_datetime"] is False
    assert data["datetime_format"] is None


def test_save_state_does_not_persist_usa_mass_datetime_sentinel(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        append_datetime=True,
        datetime_format=USA_MASS_DATETIME_BUILD_SENTINEL,
    )

    controller = StateController(app)
    controller.save_state()

    with open(controller._state_file_path(), "r", encoding="utf-8") as state_file:
        data = json.load(state_file)

    assert data["append_datetime"] is False
    assert data["datetime_format"] is None


def test_load_state_restores_open_output_directory_toggle(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        tooltips_checkbox=DummyCheckbox(),
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


def test_load_state_restores_environment_sync_profiles(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    env_sync_profiles = [
        {
            "version": "3.13",
            "executable": "C:/Python313/python.exe",
            "packages": {"numpy": {"name": "numpy", "version": "2.3.0"}},
            "error": "",
        }
    ]
    env_sync_controller = DummyEnvironmentSyncController()
    app = make_app(
        tooltips_checkbox=DummyCheckbox(),
        close_after_build=DummyCheckbox(),
        minimize_after_build=DummyCheckbox(),
        open_output_dir_after_build=DummyCheckbox(),
        script_path_input=DummyInput(),
        icon_path_input=DummyInput(),
        output_path_input=DummyInput(),
        exe_name_input=DummyInput(),
        python_entry_input=DummyInput(),
        validator=DummyValidator(),
        environment_sync_controller=env_sync_controller,
    )
    controller = StateController(app)

    state_path = controller._state_file_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as state_file:
        json.dump({"env_sync_profiles": env_sync_profiles}, state_file)

    controller.load_state()

    assert env_sync_controller.loaded_profiles == env_sync_profiles
    assert env_sync_controller.update_ui is True


def test_load_state_restores_no_datetime_appended_selection(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        tooltips_checkbox=DummyCheckbox(),
        close_after_build=DummyCheckbox(),
        minimize_after_build=DummyCheckbox(),
        open_output_dir_after_build=DummyCheckbox(),
        script_path_input=DummyInput(),
        icon_path_input=DummyInput(),
        output_path_input=DummyInput(),
        exe_name_input=DummyInput(),
        python_entry_input=DummyInput(),
        validator=DummyValidator(),
        date_time_dropdown=DummyDropdown(
            [
                {"text": "Append Date/Time", "data": None, "enabled": False},
                {"text": "──────────", "data": None, "enabled": False},
                {"text": "No Date Time Appended", "data": None, "enabled": True},
                {"text": "ISO | YYYY-MM-DD", "data": "%Y-%m-%d", "enabled": True},
            ]
        ),
    )
    controller = StateController(app)

    state_path = controller._state_file_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as state_file:
        json.dump({"append_datetime": False, "datetime_format": ""}, state_file)

    controller.load_state()

    assert app.append_datetime is False
    assert app.date_time_dropdown.currentText() == "No Date Time Appended"


def test_load_state_restores_saved_datetime_format_selection(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    app = make_app(
        tooltips_checkbox=DummyCheckbox(),
        close_after_build=DummyCheckbox(),
        minimize_after_build=DummyCheckbox(),
        open_output_dir_after_build=DummyCheckbox(),
        script_path_input=DummyInput(),
        icon_path_input=DummyInput(),
        output_path_input=DummyInput(),
        exe_name_input=DummyInput(),
        python_entry_input=DummyInput(),
        validator=DummyValidator(),
        date_time_dropdown=DummyDropdown(
            [
                {"text": "Append Date/Time", "data": None, "enabled": False},
                {"text": "──────────", "data": None, "enabled": False},
                {"text": "No Date Time Appended", "data": None, "enabled": True},
                {"text": "ISO | YYYY-MM-DD", "data": "%Y-%m-%d", "enabled": True},
            ]
        ),
    )
    controller = StateController(app)

    state_path = controller._state_file_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as state_file:
        json.dump({"append_datetime": True, "datetime_format": "%Y-%m-%d"}, state_file)

    controller.load_state()

    assert app.append_datetime is True
    assert app.date_time_dropdown.currentText() == "ISO | YYYY-MM-DD"
