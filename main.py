import tkinter as tk
import threading
from core_utils import create_status_window, stop_ocr
from overlay_webserver import run_flask_server
from config import load_settings
import keyboard

flask_thread = None

def ensure_flask_server_running():
    global flask_thread
    if not flask_thread or not flask_thread.is_alive():
        print("[🌐 Flask 서버 실행 중...]")
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()

def main():
    # GUI 메인 루트 먼저 숨기기
    root = tk.Tk()
    root.withdraw()

    # 설정 로드
    settings = load_settings()
    output_mode = settings.get("OUTPUT_MODE", "tk")

    # Flask 서버 실행
    ensure_flask_server_running()

    # 상태창 + overlay 등 생성
    gui_elements = create_status_window()

    # 출력 모드 바뀔 때마다 Flask 보장 실행
    output_mode_var = gui_elements.get("output_mode_var")
    if output_mode_var:
        def on_output_mode_change(*args):
            if output_mode_var.get() == "obs":
                ensure_flask_server_running()
        output_mode_var.trace_add("write", on_output_mode_change)

    # ✅ 단축키 등록 (번역 토글)
    toggle_button = gui_elements.get("toggle_button")
    hotkey = settings.get("HOTKEY", "f8")
    if toggle_button:
        try:
            keyboard.add_hotkey(hotkey, toggle_button.invoke)
            print(f"[✅ 단축키 '{hotkey}' 등록됨 - toggle 동작]")
        except Exception as e:
            print(f"[❌ 단축키 등록 실패]: {e}")   

    # GUI 루프 실행
    try:
        tk.mainloop()
    finally:
        print("[🛑 종료됨 - OCR 정리 중]")
        stop_ocr()

if __name__ == "__main__":
    main()
