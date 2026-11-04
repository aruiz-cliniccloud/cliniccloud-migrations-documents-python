import threading
from queue import Empty, Queue
from flask import Blueprint, jsonify

folder_picker_bp = Blueprint("folder_picker", __name__)

_DIALOG_TIMEOUT_SECONDS = 60


def _pick_folder() -> str | None:
    import tkinter as tk
    from tkinter import filedialog

    result: Queue[str | None] = Queue()

    def _run() -> None:
        try:
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes("-topmost", 1)
            path = filedialog.askdirectory()
            root.destroy()
            result.put(path or None)
        except Exception:
            result.put(None)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=_DIALOG_TIMEOUT_SECONDS)

    try:
        return result.get_nowait()
    except Empty:
        raise TimeoutError("Folder dialog did not respond within the timeout.")


@folder_picker_bp.get("/browse-folder")
def browse_folder():
    try:
        path = _pick_folder()
        return jsonify({"path": path})
    except Exception:
        return jsonify({"path": None})
