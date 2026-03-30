
import os, json
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt, QTimer


class RecentController:
    def __init__(self, app):
        self.app = app

    def on_recent_interpreter_selected(self, index):
        app = self.app
        if index <= 0:
            return

        path = app.select_interpreter.currentData()

        if not path:
            return

        path = os.path.abspath(os.path.normpath(path))

        print("Selected:", path)

        # 🔑 APPLY DIRECTLY (same pattern as script/icon)
        app.python_interpreter_path = path
        app.python_path = path

        self.app.validator.update_ui_state()
        self.app.validator.validation_status_message()

        self.app.python_entry_input.setText(self.app.python_interpreter_path)
        QTimer.singleShot(0, lambda: self.app.python_entry_input.setCursorPosition(0))
        self.app.select_interpreter.setCurrentIndex(0)
        
    def add_recent_interpreter(self, path):
        app = self.app
        ap = os.path.abspath(os.path.normpath(path)) if path else ""
        if not ap:
            return

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        lst = data.get("recent_interpreters", [])

        if ap in lst:
            lst.remove(ap)

        lst.insert(0, ap)
        lst = lst[:10]

        data["recent_interpreters"] = lst

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Recent interpreters save error:", e)

        app.state_data = data
        self.app.validator.update_ui_state()
        self.app.validator.validation_status_message()

    def populate_recent_interpreters_dropdown(self):
        app = self.app

        def _abs(p):
            return os.path.abspath(os.path.normpath(p)) if p else ""

        app.select_interpreter.blockSignals(True)
        app.select_interpreter.clear()
        
        app.select_interpreter.addItem("Select Recent Interpreter")
        model = app.select_interpreter.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
    
        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        paths = sorted(
            data.get("recent_interpreters", []),
            key=lambda p: (
                os.path.basename(os.path.dirname(p)).lower(),
                os.path.basename(p).lower()
            )
        )

        seen = set()

        for p in paths:
            ap = _abs(p)

            if not ap:
                continue
            if not os.path.isfile(ap):
                continue
            if ap in seen:
                continue

            seen.add(ap)

            name = os.path.basename(ap)
            parent = os.path.basename(os.path.dirname(ap))

            display = f"{parent}\\{name}" if parent else name

            app.select_interpreter.addItem(display, ap)

        app.select_interpreter.blockSignals(False)
        self.app.validator.update_ui_state()
        self.app.validator.validation_status_message()

    def interpreter_delete(self):
        app = self.app
        full_path = getattr(app, "python_interpreter_path", "") or ""

        if not full_path:
            return

        reply = QMessageBox.question(
            app,
            "Delete Interpreter",
            f"Are you sure you want to remove:\n\n{full_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # 🔑 clear current if matching
        if os.path.abspath(os.path.normpath(full_path)) == os.path.abspath(os.path.normpath(getattr(app, "python_interpreter_path", ""))):
            if hasattr(app, "python_entry_input"):
                app.python_entry_input.clear()
            app.python_interpreter_path = ""
            app.python_path = ""

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        lst = data.get("recent_interpreters", [])

        norm = os.path.abspath(os.path.normpath(full_path))
        lst = [p for p in lst if os.path.abspath(os.path.normpath(p)) != norm]

        data["recent_interpreters"] = lst
        app.state_data = data

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        app.validator.validation_status_message()
        self.app.validator.update_ui_state()
        self.app.validator.validation_status_message()
        self.populate_recent_interpreters_dropdown()

    def all_interpreter_delete(self):
        app = self.app

        reply = QMessageBox.question(
            app,
            "Delete All Interpreters",
            "Are you sure you want to delete ALL interpreters?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        data["recent_interpreters"] = []
        app.state_data = data

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Delete all interpreters error:", e)

        # 🔑 clear current UI/state
        if hasattr(app, "python_entry_input"):
            app.python_entry_input.clear()

        app.python_interpreter_path = ""
        app.python_path = ""

        app.validator.validation_status_message()
        self.app.validator.update_ui_state()
        self.app.validator.validation_status_message()
        self.populate_recent_interpreters_dropdown()


    def add_recent_script(self, path):
        app = self.app
        ap = os.path.abspath(os.path.normpath(path)) if path else ""
        if not ap:
            return

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        lst = data.get("recent_scripts", [])

        if ap in lst:
            lst.remove(ap)

        lst.insert(0, ap)
        lst = lst[:10]

        data["recent_scripts"] = lst

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Recent scripts save error:", e)

        app.state_data = data
        self.app.validator.update_ui_state()
        self.app.validator.validation_status_message()
        
    def populate_recent_dropdown(self):
        app = self.app

        def _abs(p):
            return os.path.abspath(os.path.normpath(p)) if p else ""

        app.recent_folder_dropdown.blockSignals(True)
        app.recent_folder_dropdown.clear()
        
        app.recent_folder_dropdown.addItem("Select Recent File")
        model = app.recent_folder_dropdown.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
       
        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        paths = sorted(
            data.get("recent_scripts", []),
            key=lambda p: (
                os.path.basename(os.path.dirname(p)).lower(),  # project folder
                os.path.basename(p).lower()                    # file name
            )
        )

        seen = set()

        for p in paths:
            ap = _abs(p)

            if not ap:
                continue
            if not os.path.isfile(ap):
                continue
            if ap in seen:
                continue

            seen.add(ap)

            name = os.path.basename(ap)
            parent = os.path.basename(os.path.dirname(ap))

            display = f"{parent}\\{name}" if parent else name

            app.recent_folder_dropdown.addItem(display, ap)

        app.recent_folder_dropdown.blockSignals(False)
        self.app.validator.update_ui_state()
        self.app.validator.validation_status_message()
                
    def on_recent_file_selected(self, index):
        app = self.app
        if index <=0:
            return

        path = app.recent_folder_dropdown.currentData()

        if not path:
            return

        path = os.path.abspath(os.path.normpath(path))

        print("Selected:", path)

        if hasattr(app, "file_pickers"):
            app.file_pickers._apply_selected_entry(path)

        self.app.validator.update_ui_state()
        self.app.validator.validation_status_message()

        self.app.script_path_input.setText(self.app.script_path)
        QTimer.singleShot(0, lambda: self.app.script_path_input.setCursorPosition(0))
                    
    def confirm_delete_recent(self):
        app = self.app
        full_path = getattr(app, "entry_script", "") or getattr(app, "script_path", "")

        if not full_path:
            return

        reply = QMessageBox.question(
            app,
            "Delete Recent File",
            f"Are you sure you want to remove:\n\n{full_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if os.path.abspath(os.path.normpath(full_path)) == os.path.abspath(os.path.normpath(getattr(app, "entry_script", ""))):
            app.script_path_input.clear()
            app.entry_script = None
            app.project_root = None
            app.script_path = ""

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        lst = data.get("recent_scripts", [])

        norm = os.path.abspath(os.path.normpath(full_path))
        lst = [p for p in lst if os.path.abspath(os.path.normpath(p)) != norm]

        data["recent_scripts"] = lst
        app.state_data = data

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.populate_recent_dropdown()
        app.validator.validation_status_message()
        self.app.validator.update_ui_state()
        
    def confirm_delete_all_folder(self):
        app = self.app

        reply = QMessageBox.question(
            app,
            "Delete All Recent Files",
            "Are you sure you want to delete ALL recent files?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        # 🔑 clear list
        data["recent_scripts"] = []

        app.state_data = data

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Delete all recent scripts error:", e)

        # 🔑 clear UI + runtime state
        if hasattr(app, "script_path_input"):
            app.script_path_input.clear()
        app.entry_script = None
        app.project_root = None
        app.script_path = ""

        # 🔑 refresh dropdown
        self.populate_recent_dropdown()

        app.validator.validation_status_message()
        self.app.validator.update_ui_state()

    #========================================
    #================================ Icons
    #========================================
    
    def on_recent_icon_selected(self, index):
        app = self.app
        if index <= 0:
            return

        path = app.select_recent_icons.currentData()

        if not path:
            return

        path = os.path.abspath(os.path.normpath(path))

        print("Selected:", path)

        if hasattr(app, "file_pickers"):
            app.file_pickers._apply_selected_icon(path)
        
        self.app.validator.update_ui_state()

        self.app.icon_path_input.setText(self.app.icon_path)
        QTimer.singleShot(0, lambda: self.app.icon_path_input.setCursorPosition(0))
                            
   
        
    def add_recent_icon(self, path):
        app = self.app
        ap = os.path.abspath(os.path.normpath(path)) if path else ""
        if not ap:
            return

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        lst = data.get("recent_icons", [])

        if ap in lst:
            lst.remove(ap)

        lst.insert(0, ap)
        lst = lst[:10]

        data["recent_icons"] = lst

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Recent icons save error:", e)

        app.state_data = data
        self.app.validator.update_ui_state()
        
    def populate_recent_icons_dropdown(self):
        app = self.app

        def _abs(p):
            return os.path.abspath(os.path.normpath(p)) if p else ""

        app.select_recent_icons.blockSignals(True)
        app.select_recent_icons.clear()

        app.select_recent_icons.addItem("Select Recent Icon")
        model = app.select_recent_icons.model()
        item = model.item(0)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        paths = sorted(
            data.get("recent_icons", []),
            key=lambda p: os.path.basename(p).lower()
        )

        seen = set()

        for p in paths:
            ap = _abs(p)

            if not ap:
                continue
            if not os.path.exists(ap):
                continue
            if ap in seen:
                continue

            seen.add(ap)

            name = os.path.basename(ap)
            parent = os.path.basename(os.path.dirname(ap))

            display = f"{parent}\\{name}" if parent else name

            app.select_recent_icons.addItem(display, ap)

        app.select_recent_icons.blockSignals(False)
        self.app.validator.update_ui_state()
        
    def confirm_delete_recent_icon(self):
        app = self.app
        full_path = getattr(app, "icon_path", "") or ""

        if not full_path:
            return

        reply = QMessageBox.question(
            app,
            "Delete Recent Icon",
            f"Are you sure you want to remove:\n\n{full_path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        if os.path.abspath(os.path.normpath(full_path)) == os.path.abspath(os.path.normpath(getattr(app, "icon_path", ""))):
            app.icon_path_input.clear()
            app.icon_path = ""

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        lst = data.get("recent_icons", [])

        norm = os.path.abspath(os.path.normpath(full_path))
        lst = [p for p in lst if os.path.abspath(os.path.normpath(p)) != norm]

        data["recent_icons"] = lst
        app.state_data = data

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        self.populate_recent_icons_dropdown()
        app.validator.validation_status_message()
        self.app.validator.update_ui_state()
        
        
    def confirm_delete_all_icons(self):
        app = self.app

        reply = QMessageBox.question(
            app,
            "Delete All Recent Icons",
            "Are you sure you want to delete ALL recent icons?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        data["recent_icons"] = []

        app.state_data = data

        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print("Delete all recent icons error:", e)

        if hasattr(app, "icon_path_input"):
            app.icon_path_input.clear()
        app.icon_path = ""

        self.populate_recent_icons_dropdown()

        app.validator.validation_status_message()
        self.app.validator.update_ui_state()