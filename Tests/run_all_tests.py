import importlib.util
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if importlib.util.find_spec("pytest") is None:
        print(
            "pytest is not installed. Install test dependencies with: "
            "python -m pip install -r requirements-dev.txt"
        )
        return 1

    tests_dir = Path(__file__).resolve().parent
    command = [sys.executable, "-m", "pytest", str(tests_dir)]

    if importlib.util.find_spec("xdist") is not None:
        command.extend(["-n", "auto"])

    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
