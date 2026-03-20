
import os, json
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt

class RecentController:
    def __init__(self, app):
        self.app = app

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

        paths = data.get("recent_scripts", [])

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
    
    def update_delete_recent_icon_button(self, index):
        app = self.app
        if index > 0 and app.select_recent_icons.currentData():
            app.delete_recent_icons.setEnabled(True)
        else:
            app.delete_recent_icons.setEnabled(False)
        
    def on_recent_icon_selected(self, index):
        app = self.app
        if index <=0:
            return

        path = app.select_recent_icons.currentData()

        if not path:
            return

        path = os.path.abspath(os.path.normpath(path))

        app.icon_path = path

        if hasattr(app, "icon_path_input"):
            app.icon_path_input.setText(path)

        if hasattr(app, "validator"):
            app.validator.update_build_button_state()

        if hasattr(app, "state_ctrl"):
            app.state_ctrl.save_state()
            
        app.select_recent_icons.setCurrentIndex(0)
        
    def confirm_delete_recent_icon(self):
        app = self.app
        full_path = getattr(app, "icon_path", "").strip()

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

        state_path = app.state_ctrl._state_file_path()

        try:
            if os.path.isfile(state_path):
                with open(state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except:
            data = {}

        icons = data.get("recent_icons", [])

        norm_target = os.path.abspath(os.path.normpath(full_path))

        icons = [
            p for p in icons
            if os.path.abspath(os.path.normpath(p)) != norm_target
        ]

        data["recent_icons"] = icons

        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        current = os.path.abspath(os.path.normpath(getattr(app, "icon_path", "")))

        if current == norm_target:
            app.icon_path_input.clear()
            app.icon_path = ""

        self.populate_recent_icons_dropdown()
        app.validator.validation_status_message()
        
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

        paths = data.get("recent_icons", [])

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

            app.select_recent_icons.addItem(name, ap)

        app.select_recent_icons.blockSignals(False)