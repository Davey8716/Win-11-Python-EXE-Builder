from pathlib import Path
from types import SimpleNamespace

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
