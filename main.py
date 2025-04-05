import tkinter as tk
import threading
from core_utils import create_status_window, stop_ocr
from overlay_webserver import run_flask_server
from config import load_settings
import keyboard
import os
import webbrowser

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

    # 기본 종료 핸들러 추가
    def safe_exit():
        try:
            stop_ocr()
            if 'status' in gui_elements:
                gui_elements['status'].destroy()
            keyboard.unhook_all()
            print("[🔄 정상 종료 절차 진행 중...]")
        except Exception as e:
            print(f"[⚠️ 종료 중 오류 발생]: {e}")
        finally:
            root.destroy()
            os._exit(0)

    root.protocol("WM_DELETE_WINDOW", safe_exit)
    
    # 프로그램 시작 3초 후 광고 페이지 열기
    root.after(3000, lambda: webbrowser.open("https://sonagi-psy.tistory.com/15"))

    # GUI 루프 실행
    try:
        root.mainloop()
    except Exception as e:
        print(f"[❌ GUI 오류 발생]: {e}")
    finally:
        print("[🛑 종료됨 - OCR 정리 중]")
        stop_ocr()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"[❌ 프로그램 시작 중 치명적인 오류 발생]")
        print(traceback.format_exc())
        
        # 오류 메시지 창 표시 시도
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("소나기OCR 오류", f"프로그램 실행 중 오류가 발생했습니다:\n{str(e)}")
        except:
            pass
            
        # 3초 후 종료
        import time
        time.sleep(3)