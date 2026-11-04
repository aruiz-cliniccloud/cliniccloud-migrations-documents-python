from flask import Blueprint, jsonify

folder_picker_bp = Blueprint("folder_picker", __name__)


def _pick_folder() -> str | None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    path = filedialog.askdirectory(title="Select folder")
    root.destroy()
    return path or None


@folder_picker_bp.get("/browse-folder")
def browse_folder():
    try:
        path = _pick_folder()
        return jsonify({"path": path})
    except Exception:
        return jsonify({"path": None})
