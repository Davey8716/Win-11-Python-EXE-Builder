import os
from pathlib import Path
from types import SimpleNamespace

import build_controller
from build_controller import BuildController


class DummyInput:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value


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
