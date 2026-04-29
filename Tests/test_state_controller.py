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
