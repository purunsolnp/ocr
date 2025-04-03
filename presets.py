# presets.py
from tkinter import simpledialog
from config import update_setting

def save_preset(ocr_region, output_position, vertical=None, side=None):
    name = simpledialog.askstring("프리셋 저장", "프리셋 이름을 입력하세요:")
    if name:
        with open("presets.txt", "a", encoding="utf-8") as f:
            v_str = "None" if vertical is None else str(vertical)
            s_str = "None" if side is None else side
            f.write(f"{name}|{','.join(map(str, ocr_region))}|{','.join(map(str, output_position))}|{v_str}|{s_str}\n")
        return name
    return None

def load_presets():
    presets = {}
    try:
        with open("presets.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 3:
                    name = parts[0]
                    ocr = tuple(map(int, parts[1].split(",")))
                    pos = tuple(map(int, parts[2].split(",")))
                    vertical = None
                    side = None
                    if len(parts) >= 5:
                        vertical = None if parts[3] == "None" else (parts[3] == "True")
                        side = None if parts[4] == "None" else parts[4]
                    presets[name] = (ocr, pos, vertical, side)
    except FileNotFoundError:
        pass
    return presets

def select_preset_gui(presets):
    if not presets:
        return None
    from tkinter import simpledialog
    name = simpledialog.askstring("프리셋 불러오기", f"불러올 프리셋 이름을 입력하세요:\n{', '.join(presets.keys())}")
    if name and name in presets:
        ocr, pos, vertical, side = presets[name]
        update_setting("OCR_REGION", ocr)
        update_setting("OUTPUT_POSITION", pos)
        update_setting("VERTICAL", vertical)
        update_setting("PRIMARY_MONITOR_SIDE", side)
        return name
    return None