import os
import warnings
from datetime import datetime as real_datetime
from pathlib import Path
from types import SimpleNamespace

import build_controller
from build_controller import BuildController
from datetime_build_options import (
    MASS_DATETIME_BUILD_SENTINEL,
    NO_DATETIME_LABEL,
)


class DummyInput:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value

    def setText(self, value):
        self._value = value


def make_app(**overrides):
    app = SimpleNamespace(
        exe_name_input=DummyInput("Builder"),
        append_py_version=False,
        python_interpreter_path="",
        entry_script="",
        project_root="",
    )

    for name, value in overrides.items():
        setattr(app, name, value)

    return app


def test_initialize_debug_log_uses_selected_output_folder(tmp_path):
    script = tmp_path / "project" / "main.py"
    script.parent.mkdir()
    script.write_text("print('hello')\n", encoding="utf-8")

    app = make_app(
        entry_script=str(script),
        project_root=str(script.parent),
    )
    controller = BuildController(app)

    controller._initialize_debug_log(str(script), str(tmp_path))

    log_path = Path(app.debug_log_path)

    assert log_path.parent == tmp_path
    assert log_path.name.startswith("EXE_BUILDER_DEBUG_Builder_project_")
    assert log_path.suffix == ".log"
    assert log_path.exists()

    contents = log_path.read_text(encoding="utf-8")
    assert f"OUTPUT_DIR={repr(str(tmp_path))}" in contents
    assert f"ENTRY_SCRIPT={repr(str(script))}" in contents


def test_build_debug_log_name_appends_python_version_when_enabled(tmp_path):
    app = make_app(
        append_py_version=True,
        python_interpreter_path=str(tmp_path / "Python314" / "python.exe"),
    )
    controller = BuildController(app)

    log_name = controller._build_debug_log_name(str(tmp_path / "project" / "main.py"))

    assert "py3.14" in log_name


def test_mass_datetime_debug_log_reuses_single_txt_file(tmp_path, monkeypatch):
    monkeypatch.setattr(build_controller, "datetime", FixedDateTime)

    script = tmp_path / "project" / "main.py"
    script.parent.mkdir()
    script.write_text("print('hello')\n", encoding="utf-8")

    app = make_app(
        entry_script=str(script),
        project_root=str(script.parent),
        python_interpreter_path=str(tmp_path / "Python314" / "python.exe"),
    )
    controller = BuildController(app)
    controller._mass_datetime_active = True
    controller._mass_datetime_total = 7
    controller._mass_datetime_index = 1
    controller._mass_datetime_current_label = NO_DATETIME_LABEL

    controller._initialize_debug_log(str(script), str(tmp_path))

    first_log_path = Path(app.debug_log_path)
    assert first_log_path.parent == tmp_path
    assert first_log_path.name.startswith("EXE_BUILDER_BUILD_ALL_DEBUG_Builder_project_")
    assert first_log_path.suffix == ".txt"
    assert first_log_path.exists()

    controller._mass_datetime_index = 2
    controller._mass_datetime_current_label = "ISO | YYYY-MM-DD"
    controller._initialize_debug_log(str(script), str(tmp_path))

    assert Path(app.debug_log_path) == first_log_path

    contents = first_log_path.read_text(encoding="utf-8")
    assert contents.count("BUILD ALL DATE/TIME OUTPUTS STARTED") == 1
    assert f"BUILD ALL DATE/TIME OUTPUT 1/7: {NO_DATETIME_LABEL}" in contents
    assert "BUILD ALL DATE/TIME OUTPUT 2/7: ISO | YYYY-MM-DD" in contents
    assert contents.count(f"ENTRY_SCRIPT={repr(str(script))}") == 2
    assert f"OUTPUT_DIR={repr(str(tmp_path))}" in contents


class DummySignal:
    def connect(self, *_args, **_kwargs):
        pass

    def disconnect(self, *_args, **_kwargs):
        pass


class DummyButton:
    def __init__(self):
        self.clicked = DummySignal()
        self.text = ""

    def setText(self, value):
        self.text = value


class WarningSignal(DummySignal):
    def disconnect(self, *_args, **_kwargs):
        warnings.warn(
            'Failed to disconnect (None) from signal "clicked()".',
            RuntimeWarning,
            stacklevel=2,
        )


class WarningButton(DummyButton):
    def __init__(self):
        super().__init__()
        self.clicked = WarningSignal()


class DummyLabel:
    def __init__(self):
        self.text = ""
        self.stylesheet = ""

    def setFixedWidth(self, _value):
        pass

    def setText(self, value):
        self.text = value

    def setStyleSheet(self, value):
        self.stylesheet = value


class DummyToggle:
    def __init__(self):
        self.checked = None

    def setChecked(self, value):
        self.checked = value


class DummyDropdown:
    def __init__(self, options, current_index=0):
        self.options = list(options)
        self.current_index = current_index
        self.signals_blocked = False

    def currentData(self):
        return self.options[self.current_index]["data"]

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

    def blockSignals(self, value):
        self.signals_blocked = value

    def currentText(self):
        return self.options[self.current_index]["text"]


class DummyValidationController:
    def update_ui_state(self):
        pass

    def set_build_error(self, _message):
        pass

    def update_build_button(self):
        pass


class DummyThread:
    def __init__(self):
        self.started = DummySignal()
        self.finished = DummySignal()

    def start(self):
        pass

    def quit(self):
        pass

    def deleteLater(self):
        pass


class ShutdownThread(DummyThread):
    def __init__(self, running=True):
        super().__init__()
        self.running = running
        self.quit_called = False
        self.wait_timeout = None

    def isRunning(self):
        return self.running

    def quit(self):
        self.quit_called = True

    def wait(self, timeout):
        self.wait_timeout = timeout
        self.running = False
        return True


class FakeWorker:
    def __init__(self, app, cmd):
        app.captured_cmd = cmd
        self.finished = DummySignal()

    def moveToThread(self, _thread):
        pass

    def run(self):
        pass

    def deleteLater(self):
        pass


class CapturingWorker:
    def __init__(self, app, cmd):
        app.captured_cmds.append(cmd)
        self.finished = DummySignal()

    def moveToThread(self, _thread):
        pass

    def run(self):
        pass

    def deleteLater(self):
        pass


class FixedDateTime:
    @classmethod
    def now(cls):
        return real_datetime(2026, 5, 19, 12, 34, 56)


def make_buildable_app(tmp_path, date_time_dropdown=None, **overrides):
    project_root = tmp_path / "project"
    project_root.mkdir()
    script = project_root / "launcher.py"
    script.write_text("print('hello')\n", encoding="utf-8")

    output_dir = tmp_path / "dist"
    output_dir.mkdir()

    python_dir = tmp_path / "Python314"
    python_dir.mkdir()
    python_exe = python_dir / "python.exe"
    python_exe.write_text("", encoding="utf-8")

    app = make_app(
        script_path_input=DummyInput(str(script)),
        output_path_input=DummyInput(str(output_dir)),
        build_process=None,
        icon_path="",
        output_path="",
        build_btn=DummyButton(),
        status_label=DummyLabel(),
        validation_controller=DummyValidationController(),
        last_build_counter=0,
        append_datetime=False,
        datetime_format="",
        append_py_version=False,
        repaint=lambda: None,
        set_status=lambda message: setattr(app, "last_status", message),
        python_interpreter_path=str(python_exe),
        entry_script=str(script),
        project_root=str(project_root),
        captured_cmds=[],
        date_time_dropdown=date_time_dropdown,
        state_ctrl=SimpleNamespace(save_state=lambda: setattr(app, "saved_state", True)),
        open_output_dir_after_build_enabled=False,
        minimize_after_build_enabled=False,
        close_after_build_enabled=False,
        showMinimized=lambda: setattr(app, "minimized", True),
        close_app=lambda: setattr(app, "closed", True),
    )

    for name, value in overrides.items():
        setattr(app, name, value)

    return app


def mass_datetime_dropdown():
    return DummyDropdown(
        [
            {"text": NO_DATETIME_LABEL, "data": None},
            {"text": "Build All Date/Time Outputs", "data": MASS_DATETIME_BUILD_SENTINEL},
            {"text": "ISO | YYYY-MM-DD", "data": "%Y-%m-%d"},
            {"text": "ISO | YYYY-MM-DD_HH-MM", "data": "%Y-%m-%d_%H-%M"},
            {"text": "UK | DD-MM-YYYY", "data": "%d-%m-%Y"},
            {"text": "UK | DD-MM-YYYY_HH-MM", "data": "%d-%m-%Y_%H-%M"},
            {"text": "USA | MM-DD-YYYY", "data": "%m-%d-%Y"},
            {"text": "USA | MM-DD-YYYY_HH-MM", "data": "%m-%d-%Y_%H-%M"},
        ],
        current_index=1,
    )


def build_names(app):
    names = []
    for cmd in app.captured_cmds:
        for part in cmd:
            if part.startswith("--name="):
                names.append(part.removeprefix("--name="))
                break
    return names


def test_shutdown_stops_running_build_thread_and_clears_state():
    app = make_app(
        _eta_running=True,
        building=True,
        build_process=None,
    )
    controller = BuildController(app)
    thread = ShutdownThread()
    controller.build_thread = thread
    controller.worker = object()

    controller.shutdown(timeout_ms=1234)

    assert app._eta_running is False
    assert app.building is False
    assert app.build_process is None
    assert thread.quit_called is True
    assert thread.wait_timeout == 1234
    assert controller.build_thread is None
    assert controller.worker is None


def test_shutdown_cancels_active_build_process(monkeypatch):
    import build_cancellation

    cancelled = []
    app = make_app(
        _eta_running=True,
        building=True,
        build_process=object(),
        _is_closing=True,
    )
    controller = BuildController(app)

    def fake_cancel(self):
        cancelled.append(self.app.build_process)
        self.app.build_process = None
        self.app.building = False

    monkeypatch.setattr(build_cancellation.BuildCancellation, "cancel_build", fake_cancel)

    controller.shutdown()

    assert cancelled
    assert app._eta_running is False
    assert app.building is False
    assert app.build_process is None


def patch_build_runtime(monkeypatch):
    monkeypatch.setattr(build_controller, "validate_bundle_inputs", lambda app: (True, ""))
    monkeypatch.setattr(build_controller, "QThread", DummyThread)
    monkeypatch.setattr(build_controller, "BuildWorker", CapturingWorker)
    monkeypatch.setattr(build_controller, "get_tray_icon_pyinstaller_args", lambda _icon: [])
    monkeypatch.setattr(BuildController, "start_eta", lambda self: None)
    monkeypatch.setattr(BuildController, "stop_eta", lambda self: None)
    monkeypatch.setattr(build_controller, "datetime", FixedDateTime)
    monkeypatch.setattr(
        build_controller.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(build_controller.QTimer, "singleShot", lambda _ms, callback: callback())


def test_mass_datetime_build_runs_all_outputs_in_sequence(tmp_path, monkeypatch):
    patch_build_runtime(monkeypatch)
    app = make_buildable_app(tmp_path, date_time_dropdown=mass_datetime_dropdown())
    controller = BuildController(app)

    controller.build_exe(None)
    for _ in range(6):
        controller._on_build_complete_ui(0, "", "")

    assert build_names(app) == [
        "Builder",
        "Builder_2026-05-19",
        "Builder_2026-05-19_12-34",
        "Builder_19-05-2026",
        "Builder_19-05-2026_12-34",
        "Builder_05-19-2026",
        "Builder_05-19-2026_12-34",
    ]
    assert controller._mass_datetime_active is True

    controller._on_build_complete_ui(0, "", "")

    assert controller._mass_datetime_active is False
    assert app.append_datetime is False
    assert app.datetime_format == ""
    assert app.date_time_dropdown.currentText() == NO_DATETIME_LABEL


def test_mass_datetime_build_waits_for_success_before_next_output(tmp_path, monkeypatch):
    patch_build_runtime(monkeypatch)
    app = make_buildable_app(tmp_path, date_time_dropdown=mass_datetime_dropdown())
    controller = BuildController(app)

    controller.build_exe(None)

    assert build_names(app) == ["Builder"]

    controller._on_build_complete_ui(0, "", "")

    assert build_names(app) == ["Builder", "Builder_2026-05-19"]


def test_mass_datetime_build_stops_on_failure_and_restores_state(tmp_path, monkeypatch):
    patch_build_runtime(monkeypatch)
    dropdown = mass_datetime_dropdown()
    app = make_buildable_app(
        tmp_path,
        date_time_dropdown=dropdown,
        append_datetime=True,
        datetime_format="%Y-%m-%d",
        _mass_datetime_restore_state={
            "append_datetime": True,
            "datetime_format": "%Y-%m-%d",
        },
    )
    controller = BuildController(app)

    controller.build_exe(None)
    controller._on_build_complete_ui(1, "", "failed")

    assert build_names(app) == ["Builder"]
    assert controller._mass_datetime_active is False
    assert app.append_datetime is True
    assert app.datetime_format == "%Y-%m-%d"
    assert app.date_time_dropdown.currentText() == "ISO | YYYY-MM-DD"
    assert app.status_label.stylesheet == build_controller.status_text_style(
        build_controller.Colors.ERROR,
        border_width=1,
    )


def test_mass_datetime_build_cancel_restores_state(tmp_path, monkeypatch):
    patch_build_runtime(monkeypatch)
    import build_cancellation

    dropdown = mass_datetime_dropdown()
    app = make_buildable_app(
        tmp_path,
        date_time_dropdown=dropdown,
        append_datetime=True,
        datetime_format="%d-%m-%Y",
        _mass_datetime_restore_state={
            "append_datetime": True,
            "datetime_format": "%d-%m-%Y",
        },
    )
    controller = BuildController(app)

    controller.build_exe(None)
    app.build_process = object()

    def fake_cancel(self):
        self.app.build_process = None
        self.app.building = False
        self.app.cancelled = True

    monkeypatch.setattr(build_cancellation.BuildCancellation, "cancel_build", fake_cancel)

    controller.build_exe(None)

    assert app.cancelled is True
    assert controller._mass_datetime_active is False
    assert app.append_datetime is True
    assert app.datetime_format == "%d-%m-%Y"
    assert app.date_time_dropdown.currentText() == "UK | DD-MM-YYYY"


def test_build_exe_suppresses_empty_clicked_disconnect_warning(tmp_path, monkeypatch):
    patch_build_runtime(monkeypatch)
    app = make_buildable_app(tmp_path, build_btn=WarningButton())
    controller = BuildController(app)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        controller.build_exe(None)

    assert not [
        warning
        for warning in caught
        if issubclass(warning.category, RuntimeWarning)
        and "Failed to disconnect" in str(warning.message)
    ]


def test_build_exe_adds_project_root_to_paths_and_data(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    script = project_root / "main.py"
    script.write_text("print('hello')\n", encoding="utf-8")

    output_dir = tmp_path / "dist"
    output_dir.mkdir()

    python_dir = tmp_path / "Python314"
    python_dir.mkdir()
    python_exe = python_dir / "python.exe"
    python_exe.write_text("", encoding="utf-8")

    monkeypatch.setattr(build_controller, "validate_bundle_inputs", lambda app: (True, ""))
    monkeypatch.setattr(build_controller, "QThread", DummyThread)
    monkeypatch.setattr(build_controller, "BuildWorker", FakeWorker)
    monkeypatch.setattr(build_controller, "get_tray_icon_pyinstaller_args", lambda _icon: [])
    monkeypatch.setattr(BuildController, "start_eta", lambda self: None)

    monkeypatch.setattr(
        build_controller.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    app = make_app(
        script_path_input=DummyInput(str(script)),
        output_path_input=DummyInput(str(output_dir)),
        build_process=None,
        icon_path="",
        output_path="",
        build_btn=DummyButton(),
        status_label=DummyLabel(),
        validation_controller=DummyValidationController(),
        last_build_counter=0,
        append_datetime=False,
        repaint=lambda: None,
        set_status=lambda _message: None,
        python_interpreter_path=str(python_exe),
        entry_script=str(script),
        project_root=str(project_root),
    )
    controller = BuildController(app)

    controller.build_exe(app)

    assert f"--paths={project_root}" in app.captured_cmd
    assert f"--add-data={project_root}{os.pathsep}." in app.captured_cmd
    assert app.captured_cmd.index(f"--paths={project_root}") < app.captured_cmd.index(str(script))


def test_build_exe_adds_parent_search_path_for_sibling_packages(tmp_path, monkeypatch):
    workspace_root = tmp_path / "workspace"
    project_root = workspace_root / "Code Workspace Builder"
    shared_root = workspace_root / "Shared"
    project_root.mkdir(parents=True)
    shared_root.mkdir()

    script = project_root / "main.py"
    script.write_text("print('hello')\n", encoding="utf-8")

    output_dir = tmp_path / "dist"
    output_dir.mkdir()

    python_dir = tmp_path / "Python314"
    python_dir.mkdir()
    python_exe = python_dir / "python.exe"
    python_exe.write_text("", encoding="utf-8")

    monkeypatch.setattr(build_controller, "validate_bundle_inputs", lambda app: (True, ""))
    monkeypatch.setattr(build_controller, "QThread", DummyThread)
    monkeypatch.setattr(build_controller, "BuildWorker", FakeWorker)
    monkeypatch.setattr(build_controller, "get_tray_icon_pyinstaller_args", lambda _icon: [])
    monkeypatch.setattr(BuildController, "start_eta", lambda self: None)
    monkeypatch.setattr(
        build_controller.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    app = make_app(
        script_path_input=DummyInput(str(script)),
        output_path_input=DummyInput(str(output_dir)),
        build_process=None,
        icon_path="",
        output_path="",
        build_btn=DummyButton(),
        status_label=DummyLabel(),
        validation_controller=DummyValidationController(),
        last_build_counter=0,
        append_datetime=False,
        repaint=lambda: None,
        set_status=lambda _message: None,
        python_interpreter_path=str(python_exe),
        entry_script=str(script),
        project_root=str(project_root),
    )
    controller = BuildController(app)

    controller.build_exe(app)

    assert f"--paths={project_root}" in app.captured_cmd
    assert f"--paths={workspace_root}" in app.captured_cmd
    assert f"--add-data={project_root}{os.pathsep}." in app.captured_cmd


def test_build_complete_opens_output_directory_for_non_desktop_path(tmp_path, monkeypatch):
    output_dir = tmp_path / "dist"
    output_dir.mkdir()
    opened_paths = []

    monkeypatch.setattr(build_controller.os, "startfile", lambda path: opened_paths.append(path), raising=False)

    app = make_app(
        build_start_time=0,
        last_build_seconds=45,
        status_label=DummyLabel(),
        output_path=str(output_dir),
        open_output_dir_after_build_enabled=True,
        minimize_after_build_enabled=False,
        close_after_build_enabled=False,
        state_ctrl=SimpleNamespace(save_state=lambda: None),
        validation_controller=DummyValidationController(),
        set_status=lambda _message: None,
        build_process=None,
    )
    controller = BuildController(app)
    monkeypatch.setattr(build_controller.time, "time", lambda: 5)
    monkeypatch.setattr(controller, "stop_eta", lambda: None)
    monkeypatch.setattr(build_controller.QTimer, "singleShot", lambda *_args, **_kwargs: None)

    controller._on_build_complete_ui(0, "", "")

    assert opened_paths == [os.path.normpath(str(output_dir))]


def test_build_complete_skips_opening_output_directory_for_desktop(monkeypatch):
    desktop_path = os.path.normpath(os.path.join(os.path.expanduser("~"), "Desktop"))
    opened_paths = []

    monkeypatch.setattr(build_controller.os, "startfile", lambda path: opened_paths.append(path), raising=False)

    app = make_app(
        build_start_time=0,
        last_build_seconds=45,
        status_label=DummyLabel(),
        output_path=desktop_path,
        open_output_dir_after_build_enabled=True,
        minimize_after_build_enabled=False,
        close_after_build_enabled=False,
        state_ctrl=SimpleNamespace(save_state=lambda: None),
        validation_controller=DummyValidationController(),
        set_status=lambda _message: None,
        build_process=None,
    )
    controller = BuildController(app)
    monkeypatch.setattr(build_controller.time, "time", lambda: 5)
    monkeypatch.setattr(controller, "stop_eta", lambda: None)
    monkeypatch.setattr(build_controller.QTimer, "singleShot", lambda *_args, **_kwargs: None)

    controller._on_build_complete_ui(0, "", "")

    assert opened_paths == []


def test_build_complete_opens_output_directory_before_closing(tmp_path, monkeypatch):
    output_dir = tmp_path / "dist"
    output_dir.mkdir()
    events = []

    monkeypatch.setattr(
        build_controller.os,
        "startfile",
        lambda path: events.append(("open", path)),
        raising=False,
    )

    app = make_app(
        build_start_time=0,
        last_build_seconds=45,
        status_label=DummyLabel(),
        output_path=str(output_dir),
        open_output_dir_after_build_enabled=True,
        minimize_after_build_enabled=False,
        close_after_build_enabled=True,
        close_app=lambda: events.append(("close", None)),
        state_ctrl=SimpleNamespace(save_state=lambda: None),
        validation_controller=DummyValidationController(),
        set_status=lambda _message: None,
        build_process=None,
    )
    controller = BuildController(app)
    monkeypatch.setattr(build_controller.time, "time", lambda: 5)
    monkeypatch.setattr(controller, "stop_eta", lambda: None)
    monkeypatch.setattr(build_controller.QTimer, "singleShot", lambda *_args, **_kwargs: None)

    controller._on_build_complete_ui(0, "", "")

    assert events == [
        ("open", os.path.normpath(str(output_dir))),
        ("close", None),
    ]
