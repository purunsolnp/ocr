import tkinter as tk
import threading
import traceback
import time
import os
import sys

# 로그 함수 정의 - 다른 모듈에서도 사용할 수 있도록 글로벌 함수로 설정
def write_log(message):
    try:
        with open("debug_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"{message}\n")
        print(message)  # 콘솔에도 출력
    except Exception as e:
        print(f"로그 기록 실패: {e}")

# 초기 로그 파일 생성
try:
    with open("debug_log.txt", "w", encoding="utf-8") as log_file:
        log_file.write(f"프로그램 시작: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    write_log("로그 파일 생성 완료")
except Exception as e:
    print(f"로그 파일 생성 실패: {e}")

# 모듈이 임포트될 때 write_log 함수를 글로벌로 사용할 수 있도록 설정
sys.modules['write_log'] = write_log

# 나머지 모듈 임포트는 로그 함수 정의 이후에 진행
try:
    from core_utils import create_status_window, stop_ocr
    from overlay_webserver import run_flask_server
    from config import load_settings
    import keyboard
    write_log("기본 모듈 임포트 완료")
except Exception as e:
    write_log(f"[⚠️ 모듈 임포트 오류]: {str(e)}")
    write_log(traceback.format_exc())

flask_thread = None

def ensure_flask_server_running():
    global flask_thread
    if not flask_thread or not flask_thread.is_alive():
        write_log("[Flask 서버 실행 중...]")
        try:
            flask_thread = threading.Thread(target=run_flask_server, daemon=True)
            flask_thread.start()
            write_log("[Flask 서버 스레드 시작됨]")
        except Exception as e:
            write_log(f"[⚠️ Flask 서버 시작 실패]: {str(e)}")
            write_log(traceback.format_exc())

def main():
    try:
        write_log("[main 함수 시작]")
        
        # GUI 메인 루트 먼저 숨기기
        root = tk.Tk()
        root.withdraw()
        write_log("[Tkinter 루트 초기화 완료]")

        # 설정 로드
        settings = load_settings()
        output_mode = settings.get("OUTPUT_MODE", "tk")
        write_log(f"[설정 로드 완료] 출력 모드: {output_mode}")

        # Flask 서버 실행
        ensure_flask_server_running()
        write_log("[Flask 서버 실행 요청됨]")

        # 상태창 + overlay 등 생성
        write_log("[GUI 요소 생성 중...]")
        gui_elements = create_status_window()
        write_log("[GUI 요소 생성 완료]")

        # 출력 모드 바뀔 때마다 Flask 보장 실행
        output_mode_var = gui_elements.get("output_mode_var")
        if output_mode_var:
            def on_output_mode_change(*args):
                if output_mode_var.get() == "obs":
                    ensure_flask_server_running()
            output_mode_var.trace_add("write", on_output_mode_change)
            write_log("[출력 모드 변경 이벤트 등록됨]")

        # 단축키 등록 (번역 토글)
        toggle_button = gui_elements.get("toggle_button")
        hotkey = settings.get("HOTKEY", "f8")
        if toggle_button:
            try:
                keyboard.add_hotkey(hotkey, toggle_button.invoke)
                write_log(f"[단축키 '{hotkey}' 등록됨 - toggle 동작]")
            except Exception as e:
                write_log(f"[단축키 등록 실패]: {str(e)}")
                write_log(traceback.format_exc())

        # GUI 루프 실행
        write_log("[GUI 메인 루프 시작]")
        try:
            tk.mainloop()
        except Exception as e:
            write_log(f"[⚠️ Tkinter 메인 루프 오류]: {str(e)}")
            write_log(traceback.format_exc())
            
    except Exception as e:
        write_log(f"[main 함수 실행 중 오류 발생]: {str(e)}")
        write_log(traceback.format_exc())
        
        try:
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("프로그램 오류", f"프로그램에 오류가 발생했습니다:\n{str(e)}\n\n자세한 내용은 debug_log.txt 파일을 확인하세요.")
        except:
            pass
    finally:
        write_log("[종료됨 - OCR 정리 중]")
        try:
            stop_ocr()
        except Exception as e:
            write_log(f"[OCR 정리 중 오류]: {str(e)}")
            write_log(traceback.format_exc())
        write_log(f"[로그 종료] {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        write_log("[프로그램 진입점 실행]")
        main()
    except Exception as e:
        write_log(f"[예상치 못한 오류 발생]: {str(e)}")
        write_log(traceback.format_exc())
        
        try:
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("프로그램 오류", f"프로그램에 오류가 발생했습니다:\n{str(e)}\n\n자세한 내용은 debug_log.txt 파일을 확인하세요.")
        except:
            pass