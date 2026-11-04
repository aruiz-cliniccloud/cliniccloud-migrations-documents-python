import json
import subprocess
import sys
from flask import Blueprint, jsonify

folder_picker_bp = Blueprint("folder_picker", __name__)

_DIALOG_TIMEOUT_SECONDS = 60

# Minimal script run in a subprocess so tkinter gets its own main thread
_TKINTER_SCRIPT = """
import tkinter as tk
from tkinter import filedialog
import json, sys

root = tk.Tk()
root.withdraw()
root.wm_attributes("-topmost", 1)
path = filedialog.askdirectory()
root.destroy()
print(json.dumps(path if path else None))
"""


def _pick_folder() -> str | None:
    result = subprocess.run(
        [sys.executable, "-c", _TKINTER_SCRIPT],
        capture_output=True,
        text=True,
        timeout=_DIALOG_TIMEOUT_SECONDS,
    )
    if result.returncode == 0 and result.stdout.strip():
        return json.loads(result.stdout.strip())
    return None


@folder_picker_bp.get("/browse-folder")
def browse_folder():
    try:
        path = _pick_folder()
        return jsonify({"path": path})
    except Exception:
        return jsonify({"path": None})
