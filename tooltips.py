import tkinter as tk


# -------------------------------------------------------------
#  Simple tooltip class for CTk widgets
# -------------------------------------------------------------

class CtkTooltip:
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.after_id = None
        
        # Gather all actual hoverable child widgets
        targets = [widget]

        for attr in ("_canvas", "_label", "_text_label", "_fg_label", "_border_frame"):
            if hasattr(widget, attr):
                obj = getattr(widget, attr)
                if obj:
                    targets.append(obj)

        if hasattr(widget, "_windows"):
            for win in widget._windows:
                targets.append(win)

        # Apply bindings to all relevant sub-widgets
        for t in targets:
            try:
                t.bind("<Enter>", self.schedule, add="+")
                t.bind("<Leave>", self.hide, add="+")
                t.bind("<Button-1>", self.hide, add="+")
            except:
                pass


    def schedule(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
        self.after_id = self.widget.after(self.delay, self.show)

    def show(self):
        # Global toggle
        root = self.widget.winfo_toplevel()
        if hasattr(root, "tooltips_enabled"):
            if not root.tooltips_enabled:
                return

        if self.tip_window:
            return

        x = self.widget.winfo_rootx() + 40
        y = self.widget.winfo_rooty() + 25

        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.lift()
        tw.attributes("-topmost", True)

        label = tk.Label(
            tw,
            text=self.text,
            background="#1E1E1E",
            foreground="white",
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4,
            font=("Rubik UI", 14)
        )
        label.pack()
        self.tip_window = tw

    def hide(self, event=None):
        if self.after_id:
            try:
                self.widget.after_cancel(self.after_id)
            except:
                pass
            self.after_id = None

        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# -------------------------------------------------------------
#  Tooltip wiring (UI → text mapping)
# -------------------------------------------------------------

def attach_tooltips(app):
    """
    Attach all tooltips to the EXEBuilderApp instance.
    Assumes widgets already exist on `app`.
    """

    # -----------------------------
    # Title / global controls
    # -----------------------------

    CtkTooltip(
        app.tooltips_switch,
        "Toggle all tooltips on or off.\n"
        "Turn this off once you’re familiar with the interface."
    )

    # -----------------------------
    # Script picker
    # -----------------------------

    CtkTooltip(
        app.script_entry,
        "File path to python script folder and file."
    )

    CtkTooltip(
        app.apps_btn,
        "Opens Windows Installed Apps.\n"
        "Check or remove Python versions.\n"
        "If builds fail due to environment issues,\n"
        "Go to python.org for downloading specific releases."
    )
    
    CtkTooltip(
        app.open_python_site_btn,
        "Direct link to python.org."
    )
    

    CtkTooltip(
        app.folder_btn,
        "Select a folder containing one or more Python files.\n"
        "If the folder contains only one .py file, it will be used automatically.\n"
        "If multiple .py files are found, a popup will appear.\n"
        "allowing you to choose the main entry script."
    )

    # -----------------------------
    # Python interpreter
    # -----------------------------

    CtkTooltip(
        app.interpreter_btn,
        "Select the Python interpreter used to build EXEs.\n"
        "This determines which Python installation PyInstaller runs under."
    )

    CtkTooltip(
        app.python_entry,
        "Displays the full path to the Python interpreter.\n"
        "That will be used for building EXEs.\n"
        "This is read only.\n"
        "Once a path has been set the navigation is locked to where pyton interpreters are.\n"
    )

    # -----------------------------
    # Icon picker
    # -----------------------------

    CtkTooltip(
        app.icon_btn,
        "Choose a .ico file to use as your EXE’s icon.\n"
        "Optional — PyInstaller uses a default icon otherwise."
    )

    CtkTooltip(
        app.ico_convert_btn,
        "Opens 3 websites that convert PNG/JPG images into .ico files\n"
        "for use as custom EXE icons."
    )

    CtkTooltip(
        app.icon_entry,
        "File path to Icon if used."
    )
    
    CtkTooltip(
        app.script_clear_btn,
        "Clear selected script/folder."
    ) 

    CtkTooltip(
        app.icon_clear_btn,
        "Clear icon (build without an icon)."
    )

    # -----------------------------
    # Output / EXE name
    # -----------------------------

    CtkTooltip(
        app.output_btn,
        "The file path to the folder the EXE is to be built in."
    )

    CtkTooltip(
        app.output_entry,
        "File path to the EXE output folder."
    )

    CtkTooltip(
        app.output_refresh_btn,
        "Reset output folder to Desktop."
    )

    CtkTooltip(
        app.exe_entry,
        "Name of the generated EXE folder and file.\n"
        "Do not include .exe."
    )

    CtkTooltip(
        app.refresh_btn,
        "Reset EXE name to match the entry script name.\n"
        "A python folder must be selected to for this to be ungreyed and resetable.\n"
    )

    # -----------------------------
    # Build
    # -----------------------------

    CtkTooltip(
        app.build_btn,
        "Builds your Python project into a standalone Windows EXE,Using PyInstaller.\n"
        
    )