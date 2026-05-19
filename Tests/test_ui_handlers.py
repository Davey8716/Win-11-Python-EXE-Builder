from types import SimpleNamespace

from datetime_build_options import MASS_DATETIME_BUILD_SENTINEL
from ui_handlers import UIHandlers


class DummyDropdown:
    def currentData(self):
        return MASS_DATETIME_BUILD_SENTINEL


class DummyStateController:
    def __init__(self):
        self.saved = False

    def save_state(self):
        self.saved = True


class DummyValidator:
    def __init__(self):
        self.status_updated = False
        self.ui_updated = False

    def validation_status_message(self):
        self.status_updated = True

    def update_ui_state(self):
        self.ui_updated = True


def test_mass_datetime_selection_is_transient_and_keeps_saved_format():
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
    assert app.append_datetime is True
    assert app.datetime_format == "%Y-%m-%d"
    assert app._mass_datetime_restore_state == {
        "append_datetime": True,
        "datetime_format": "%Y-%m-%d",
    }
    assert state_ctrl.saved is True
    assert validator.status_updated is True
    assert validator.ui_updated is True
