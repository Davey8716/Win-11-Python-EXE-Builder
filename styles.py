from PySide6.QtGui import QColor


class Colors:
    WHITE = QColor(255, 255, 255)
    BLACK = QColor(0, 0, 0)
    WINDOW = QColor(40, 40, 50)
    TITLE_BG = QColor(74, 111, 168)
    PANEL_BG = QColor(58, 72, 96)
    POPUP_BG = QColor(58, 72, 96)
    BORDER_MID = QColor(0, 0, 0)
    BORDER_DARK = QColor(0, 0, 0)
    SCRIPT_POPUP_BORDER = QColor(0, 0, 0)
    SUCCESS = QColor(17, 189, 39)
    SUCCESS_PRESSED = QColor(22, 212, 46)
    ERROR = QColor(255, 0, 0)
    CANCEL = QColor(255, 0, 0)
    MUTED_TEXT = QColor(255, 255, 255)
    MUTED_BORDER = QColor(0, 0, 0)
    DISABLED_BG = QColor(60, 60, 60)
    COMBO_DISABLED_BG = QColor(60, 60, 60)
    COMBO_DISABLED_TEXT = QColor(255, 255, 255)
    SELECTION_BG = QColor(74, 111, 168)
    INFO = QColor(45, 125, 210)
    WARNING = QColor(230, 162, 60)
    DISABLED_TEXT = QColor(255, 255, 255)
    TOOLTIP_BG = QColor(40, 40, 50)
    TOOLTIP_BORDER = QColor(0, 0, 0)

    TEXT_LIGHT = QColor(255, 255, 255)
    TEXT_DARK = QColor(255, 255, 255)
    SURFACE_HOVER = QColor(93, 107, 131)
    SURFACE_SELECTED_HOVER = QColor(96, 133, 190)
    DANGER_HOVER = QColor(255, 25, 25)
    DELETE_HIGHLIGHT_GLOW = QColor(255, 82, 82)
    ADD_HIGHLIGHT_GLOW = QColor(82, 255, 82)


def qcolor_name(color: QColor) -> str:
    return color.name(QColor.HexRgb)


def button_base(border_width: int = 3) -> str:
    return f"""
        QPushButton {{
            background-color: {qcolor_name(Colors.TITLE_BG)};
            color: {qcolor_name(Colors.TEXT_LIGHT)};
            border: {border_width}px solid {qcolor_name(Colors.BORDER_DARK)};
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {qcolor_name(Colors.SURFACE_SELECTED_HOVER)};
        }}
    """


def button_with_border(border_color: QColor, border_width: int = 4) -> str:
    return f"""
        QPushButton {{
            background-color: {qcolor_name(Colors.TITLE_BG)};
            color: {qcolor_name(Colors.TEXT_LIGHT)};
            border: {border_width}px solid {qcolor_name(border_color)};
            border-radius: 4px;
        }}
        QPushButton:hover {{
            background-color: {qcolor_name(Colors.SURFACE_SELECTED_HOVER)};
        }}
    """


def filled_button(background_color: QColor, border_width: int = 4, radius: int = 4) -> str:
    return f"""
        QPushButton {{
            background-color: {qcolor_name(background_color)};
            color: {qcolor_name(Colors.TEXT_LIGHT)};
            border: {border_width}px solid {qcolor_name(Colors.BORDER_DARK)};
            border-radius: {radius}px;
        }}
        QPushButton:hover {{
            background-color: {qcolor_name(Colors.SURFACE_SELECTED_HOVER)};
        }}
    """


APPEND_PY_VERSION_STYLE = f"""
    QPushButton {{
        background-color: {qcolor_name(Colors.TITLE_BG)};
        color: {qcolor_name(Colors.TEXT_LIGHT)};
        border: 3px solid {qcolor_name(Colors.BORDER_DARK)};
    }}

    QPushButton:checked {{
        background-color: {qcolor_name(Colors.SUCCESS)};
        color: {qcolor_name(Colors.TEXT_LIGHT)};
        border: 3px solid {qcolor_name(Colors.BORDER_DARK)};
    }}

    QPushButton:pressed {{
        background-color: {qcolor_name(Colors.SUCCESS_PRESSED)};
    }}

    QPushButton:disabled {{
        color: {qcolor_name(Colors.MUTED_TEXT)};
        background-color: {qcolor_name(Colors.DISABLED_BG)};
    }}
"""

APPEND_PY_VERSION_INITIAL_STYLE = APPEND_PY_VERSION_STYLE.replace("3px", "1px")

COMBO_BOX_STYLE = f"""
    QComboBox {{
        background-color: {qcolor_name(Colors.TITLE_BG)};
        color: {qcolor_name(Colors.TEXT_LIGHT)};
        border: 3px solid {qcolor_name(Colors.BORDER_DARK)};
        padding: 3px;
        font-weight:bold;
        font-size: 15px;
        qproperty-alignment: AlignCenter;
    }}

    QComboBox::drop-down {{
        border: none;
        background: {qcolor_name(Colors.WINDOW)};
        padding: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {qcolor_name(Colors.PANEL_BG)};
        color: {qcolor_name(Colors.TEXT_LIGHT)};
        selection-background-color: {qcolor_name(Colors.SELECTION_BG)};
        font-family: "Rubik UI";
        font-size: 15px;
        font-weight: bold;
        border-radius: 4px;
    }}

    QComboBox QAbstractItemView::item {{
        text-align: center;
    }}

    QComboBox:disabled {{
        background-color: {qcolor_name(Colors.COMBO_DISABLED_BG)};
        color: {qcolor_name(Colors.COMBO_DISABLED_TEXT)};
    }}
"""

MAIN_FRAME_STYLE = f"""
    QFrame {{
        border: 4px solid {qcolor_name(Colors.BORDER_DARK)};
        border-radius: 6px;
        background-color: {qcolor_name(Colors.PANEL_BG)};
        color: {qcolor_name(Colors.TEXT_LIGHT)};
    }}
    QLabel {{
        color: {qcolor_name(Colors.TEXT_LIGHT)};
    }}
"""

TITLE_FRAME_STYLE = f"""
    QFrame {{
        border-radius: 4px;
        background-color: {qcolor_name(Colors.TITLE_BG)};
        color: {qcolor_name(Colors.TEXT_LIGHT)};
    }}
    QLabel {{
        color: {qcolor_name(Colors.TEXT_LIGHT)};
    }}
"""


def status_text_style(text_color: QColor, border_width: int = 3) -> str:
    return f"""
        QTextEdit {{
            background-color: {qcolor_name(Colors.PANEL_BG)};
            color: {qcolor_name(text_color)};
            border: {border_width}px solid {qcolor_name(Colors.BORDER_MID)};
        }}
    """


def line_edit_style(text_color: QColor, border_color: QColor = Colors.WINDOW) -> str:
    return f"""
        QLineEdit {{
            background-color: {qcolor_name(Colors.PANEL_BG)};
            color: {qcolor_name(text_color)};
            border: 2px solid {qcolor_name(border_color)};
        }}
    """


SCRIPT_PICKER_FRAME_STYLE = f"""
    QFrame {{
        border: 2px solid {qcolor_name(Colors.SCRIPT_POPUP_BORDER)};
        border-radius: 6px;
        background-color: {qcolor_name(Colors.POPUP_BG)};
    }}
"""

SCRIPT_PICKER_LABEL_STYLE = """
    font-family: "Rubik";
    font-size: 13px;
    font-weight: bold;
"""

SCRIPT_PICKER_DROPDOWN_STYLE = """
    font-family: "Rubik";
    font-size: 13px;
"""

SCRIPT_PICKER_CONFIRM_STYLE = """
    font-family: "Rubik";
    font-size: 13px;
    font-weight: bold;
"""

DEPENDENCY_POPUP_FRAME_STYLE = f"""
    QFrame {{
        border: 3px solid {qcolor_name(Colors.BORDER_MID)};
        border-radius: 4px;
        background-color: {qcolor_name(Colors.PANEL_BG)};
    }}
"""

DEPENDENCY_INNER_FRAME_STYLE = f"""
    QFrame {{
        border: 3px solid {qcolor_name(Colors.BORDER_DARK)};
        background-color: {qcolor_name(Colors.TITLE_BG)};
        border-radius: 4px;
        color: {qcolor_name(Colors.TEXT_LIGHT)};
    }}
    QLabel {{
        color: {qcolor_name(Colors.TEXT_LIGHT)};
    }}
"""

DEPENDENCY_LABEL_BOX_STYLE = f"""
    QLabel {{
        border: 3px solid {qcolor_name(Colors.BORDER_DARK)};
        border-radius: 4px;
        background-color: {qcolor_name(Colors.PANEL_BG)};
        color: {qcolor_name(Colors.TEXT_LIGHT)};
    }}
"""


def label_color_style(text_color: QColor) -> str:
    return f"color: {qcolor_name(text_color)};"


def dependency_text_box_style(text_color: QColor) -> str:
    return f"""
    QTextEdit {{
        color: {qcolor_name(text_color)};
        background-color: {qcolor_name(Colors.PANEL_BG)};
        border: 1px solid {qcolor_name(Colors.MUTED_BORDER)};
        }}
    """


DEPENDENCY_OK_BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {qcolor_name(Colors.INFO)};
        color: {qcolor_name(Colors.TEXT_LIGHT)};
        border: 3px solid {qcolor_name(Colors.BORDER_DARK)};
        border-radius: 4px;
    }}
    QPushButton:disabled {{
        background-color: {qcolor_name(Colors.MUTED_BORDER)};
        color: {qcolor_name(Colors.DISABLED_TEXT)};
    }}
"""

TOOLTIP_STYLE = f"""
    QLabel {{
        background-color: {qcolor_name(Colors.TOOLTIP_BG)};
        color: {qcolor_name(Colors.WHITE)};
        border: 1px solid {qcolor_name(Colors.TOOLTIP_BORDER)};
        padding: 6px;
        border-radius: 6px;
        font-family: "Rubik";
        font-size: 15px;
    }}
"""
