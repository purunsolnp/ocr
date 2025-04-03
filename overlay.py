# overlay.py
import tkinter as tk
from config import get_setting

_overlay_root = None


def create_overlay_window():
    global _overlay_root
    _overlay_root = tk.Toplevel()
    _overlay_root.overrideredirect(True)
    _overlay_root.attributes("-topmost", True)
    _overlay_root.attributes("-alpha", 0.8)

    x, y = get_setting("OUTPUT_POSITION")
    _overlay_root.geometry(f"800x120+{x}+{y}")

    label = tk.Label(
        _overlay_root,
        text="",
        font=(get_setting("FONT_FAMILY"), get_setting("FONT_SIZE")),
        fg=get_setting("FONT_COLOR"),
        bg=get_setting("OVERLAY_BG"),
        justify="left",
        wraplength=780,
        anchor="nw"
    )
    label.pack(fill="both", expand=True)
    return label


def hide_overlay():
    if _overlay_root:
        _overlay_root.after(0, _overlay_root.withdraw)


def show_overlay():
    if _overlay_root:
        _overlay_root.after(0, _overlay_root.deiconify)
def update_overlay_position():
    if _overlay_root:
        x, y = get_setting("OUTPUT_POSITION")
        _overlay_root.geometry(f"800x120+{x}+{y}")
def destroy_overlay():
    global _overlay_root
    if _overlay_root:
        _overlay_root.destroy()
        _overlay_root = None