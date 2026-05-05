import os
from pathlib import Path

from tray_icon_support import (
    TRAY_ICON_BUNDLE_NAME,
    get_tray_icon_hook_path,
    get_tray_icon_pyinstaller_args,
)


def test_get_tray_icon_pyinstaller_args_returns_empty_without_icon():
    assert get_tray_icon_pyinstaller_args("") == []


def test_get_tray_icon_pyinstaller_args_includes_runtime_hook_and_icon(tmp_path):
    icon = tmp_path / "sample.ico"
    icon.write_text("", encoding="utf-8")

    args = get_tray_icon_pyinstaller_args(str(icon))

    assert args == [
        "--runtime-hook",
        get_tray_icon_hook_path(),
        "--add-data",
        f"{os.path.normpath(str(icon))}{os.pathsep}{TRAY_ICON_BUNDLE_NAME}",
    ]


def test_tray_icon_hook_file_exists():
    assert Path(get_tray_icon_hook_path()).is_file()
