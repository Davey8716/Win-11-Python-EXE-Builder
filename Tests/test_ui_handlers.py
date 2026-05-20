from types import SimpleNamespace
import os
import sys

import ui_handlers
from datetime_build_options import (
    ISO_MASS_DATETIME_BUILD_SENTINEL,
    MASS_DATETIME_BUILD_SENTINEL,
    UK_MASS_DATETIME_BUILD_SENTINEL,
    USA_MASS_DATETIME_BUILD_SENTINEL,
)
from ui_handlers import UIHandlers


class DummyDropdown:
    def __init__(self, data=MASS_DATETIME_BUILD_SENTINEL):
        self.data = data

    def currentData(self):
        return self.data


class DummyStateController:
    def __init__(self, state_file=None):
        self.saved = False
        self.state_file = state_file

    def save_state(self):
        self.saved = True

    def _state_file_path(self):
        return str(self.state_file)


class DummyValidator:
    def __init__(self):
        self.status_updated = False
        self.ui_updated = False

    def validation_status_message(self):
        self.status_updated = True

    def update_ui_state(self):
        self.ui_updated = True


class DummyPathInput:
    def __init__(self):
        self.value = ""

    def set_display_path(self, value):
        self.value = value


def test_mass_datetime_selection_saves_sentinel_and_keeps_restore_state():
    state_ctrl = DummyStateController()
    validator = DummyValidator()
    app = SimpleNamespace(
        date_time_dropdown=DummyDropdown(),
        append_datetime=True,
        datetime_format="%Y-%m-%d",
        state_ctrl=state_ctrl,
        validator=validator,
    )

    UIHandlers(app).on_datetime_format_changed(0)

    assert app.mass_datetime_build_selected is True
    assert app.append_datetime is False
    assert app.datetime_format == MASS_DATETIME_BUILD_SENTINEL
    assert app._mass_datetime_restore_state == {
        "append_datetime": True,
        "datetime_format": "%Y-%m-%d",
    }
    assert state_ctrl.saved is True
    assert validator.status_updated is True
    assert validator.ui_updated is True


def test_iso_mass_datetime_selection_saves_sentinel_and_keeps_restore_state():
    state_ctrl = DummyStateController()
    validator = DummyValidator()
    app = SimpleNamespace(
        date_time_dropdown=DummyDropdown(ISO_MASS_DATETIME_BUILD_SENTINEL),
        append_datetime=True,
        datetime_format="%Y-%m-%d_%H-%M",
        state_ctrl=state_ctrl,
        validator=validator,
    )

    UIHandlers(app).on_datetime_format_changed(0)

    assert app.mass_datetime_build_selected is True
    assert app.append_datetime is False
    assert app.datetime_format == ISO_MASS_DATETIME_BUILD_SENTINEL
    assert app._mass_datetime_restore_state == {
        "append_datetime": True,
        "datetime_format": "%Y-%m-%d_%H-%M",
    }
    assert state_ctrl.saved is True
    assert validator.status_updated is True
    assert validator.ui_updated is True


def test_uk_mass_datetime_selection_saves_sentinel_and_keeps_restore_state():
    state_ctrl = DummyStateController()
    validator = DummyValidator()
    app = SimpleNamespace(
        date_time_dropdown=DummyDropdown(UK_MASS_DATETIME_BUILD_SENTINEL),
        append_datetime=True,
        datetime_format="%d-%m-%Y_%H-%M",
        state_ctrl=state_ctrl,
        validator=validator,
    )

    UIHandlers(app).on_datetime_format_changed(0)

    assert app.mass_datetime_build_selected is True
    assert app.append_datetime is False
    assert app.datetime_format == UK_MASS_DATETIME_BUILD_SENTINEL
    assert app._mass_datetime_restore_state == {
        "append_datetime": True,
        "datetime_format": "%d-%m-%Y_%H-%M",
    }
    assert state_ctrl.saved is True
    assert validator.status_updated is True
    assert validator.ui_updated is True


def test_usa_mass_datetime_selection_saves_sentinel_and_keeps_restore_state():
    state_ctrl = DummyStateController()
    validator = DummyValidator()
    app = SimpleNamespace(
        date_time_dropdown=DummyDropdown(USA_MASS_DATETIME_BUILD_SENTINEL),
        append_datetime=True,
        datetime_format="%m-%d-%Y_%H-%M",
        state_ctrl=state_ctrl,
        validator=validator,
    )

    UIHandlers(app).on_datetime_format_changed(0)

    assert app.mass_datetime_build_selected is True
    assert app.append_datetime is False
    assert app.datetime_format == USA_MASS_DATETIME_BUILD_SENTINEL
    assert app._mass_datetime_restore_state == {
        "append_datetime": True,
        "datetime_format": "%m-%d-%Y_%H-%M",
    }
    assert state_ctrl.saved is True
    assert validator.status_updated is True
    assert validator.ui_updated is True


def test_open_app_data_selects_existing_state_file(tmp_path):
    state_file = tmp_path / "EXEBuilder" / "exe_builder_state.json"
    state_file.parent.mkdir()
    state_file.write_text("{}", encoding="utf-8")
    app = SimpleNamespace(state_ctrl=DummyStateController(state_file))
    handler = UIHandlers(app)
    opened = []
    focused = []

    handler._select_file_in_explorer = lambda path: opened.append(("select", path))
    handler._open_folder = lambda path: opened.append(("folder", path))
    handler._force_app_data_folder_on_top = lambda path: focused.append(path)

    handler.open_app_data()

    assert opened == [("select", str(state_file))]
    assert focused == [str(state_file.parent)]


def test_open_app_data_opens_state_folder_when_file_missing(tmp_path):
    state_file = tmp_path / "EXEBuilder" / "exe_builder_state.json"
    app = SimpleNamespace(state_ctrl=DummyStateController(state_file))
    handler = UIHandlers(app)
    opened = []
    focused = []

    handler._select_file_in_explorer = lambda path: opened.append(("select", path))
    handler._open_folder = lambda path: opened.append(("folder", path))
    handler._force_app_data_folder_on_top = lambda path: focused.append(path)

    handler.open_app_data()

    assert opened == [("folder", str(state_file.parent))]
    assert focused == [str(state_file.parent)]
    assert state_file.parent.is_dir()


def test_reset_output_to_desktop_keeps_remembered_non_desktop_output(monkeypatch, tmp_path):
    remembered_output = os.path.normpath(str(tmp_path / "dist"))
    state_ctrl = DummyStateController()
    validation_controller = DummyValidator()
    app = SimpleNamespace(
        output_refresh_btn=None,
        output_path_input=DummyPathInput(),
        output_path=remembered_output,
        last_output_dir=remembered_output,
        last_non_desktop_output_dir=remembered_output,
        state_ctrl=state_ctrl,
        validation_controller=validation_controller,
    )

    monkeypatch.setattr(ui_handlers, "flash_delete_highlight", lambda *args, **kwargs: None)

    handler = UIHandlers(app)
    desktop = os.path.normpath(handler.get_desktop_path())
    handler.reset_output_to_desktop()

    assert app.output_path == desktop
    assert app.output_path_input.value == desktop
    assert app.last_output_dir == remembered_output
    assert app.last_non_desktop_output_dir == remembered_output
    assert state_ctrl.saved is True
    assert validation_controller.ui_updated is True


def test_force_app_data_folder_on_top_activates_matching_window(monkeypatch, tmp_path):
    events = []

    class FakeWindow:
        title = "EXEBuilder"
        _hWnd = 123
        isMinimized = True

        def restore(self):
            events.append("restore")
            self.isMinimized = False

        def activate(self):
            events.append("activate")

    fake_window = FakeWindow()
    fake_pygetwindow = SimpleNamespace(
        getWindowsWithTitle=lambda title: [fake_window]
    )
    fake_win32con = SimpleNamespace(
        SW_RESTORE=9,
        SWP_NOMOVE=1,
        SWP_NOSIZE=2,
        SWP_SHOWWINDOW=4,
        HWND_TOPMOST=-1,
        HWND_NOTOPMOST=-2,
    )
    fake_win32gui = SimpleNamespace(
        ShowWindow=lambda hwnd, command: events.append(("show", hwnd, command)),
        SetForegroundWindow=lambda hwnd: events.append(("foreground", hwnd)),
        SetWindowPos=lambda hwnd, after, x, y, cx, cy, flags: events.append(
            ("position", hwnd, after, flags)
        ),
    )

    monkeypatch.setitem(sys.modules, "pygetwindow", fake_pygetwindow)
    monkeypatch.setitem(sys.modules, "win32con", fake_win32con)
    monkeypatch.setitem(sys.modules, "win32gui", fake_win32gui)

    handler = UIHandlers(SimpleNamespace())

    assert handler._force_app_data_folder_on_top(str(tmp_path / "EXEBuilder")) is True
    assert "restore" in events
    assert "activate" in events
    assert ("position", 123, fake_win32con.HWND_TOPMOST, 7) in events
    assert ("position", 123, fake_win32con.HWND_NOTOPMOST, 7) in events
