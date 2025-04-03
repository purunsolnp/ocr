# ocr.py (SocketIO 클라이언트 수정)
import time
import pyautogui
import numpy as np
import threading
import socketio
import easyocr
from config import get_setting
from translator_dispatch import translate_text, get_lang

# easyocr Reader 초기화
def init_ocr_reader():
    lang_list = get_lang(get_setting("SOURCE_LANG"))
    use_gpu = get_setting("USE_GPU")
    print(f"[🔍 OCR 리더 초기화] 언어: {lang_list}, GPU: {use_gpu}")
    return easyocr.Reader(lang_list, gpu=use_gpu)

# 전역 변수로 OCR 리더 관리
ocr_reader = None
def reinit_ocr_reader():
    global ocr_reader
    ocr_reader = init_ocr_reader()
    print(f"[🔄 OCR 리더 재초기화됨] 언어: {get_setting('SOURCE_LANG')}")

# 최초 OCR 리더 초기화
if ocr_reader is None:
    ocr_reader = init_ocr_reader()

# SocketIO 클라이언트 초기화 (네임스페이스 문제 해결)
sio = socketio.Client()
sio_connected = False

ocr_thread = None
ocr_running = False

# 중복 텍스트 관리를 위한 변수들
last_text = ""
last_translated = ""
repeat_count = 0
MAX_REPEAT = 3  # 최대 3번까지만 같은 텍스트 번역

def ocr_loop(overlay_label, output_mode="tk", status_window=None):
    global ocr_running, sio_connected, last_text, last_translated, repeat_count

    while ocr_running:
        try:
            if output_mode == "obs":
                if not sio_connected or not sio.connected:
                    try:
                        # 디버그 로그 추가
                        print(f"[🔌 현재 연결 상태] sio_connected: {sio_connected}, sio.connected: {sio.connected}")
                        
                        # 네임스페이스 제거, 기본 네임스페이스 사용
                        sio.connect("http://localhost:5000")
                        sio_connected = True
                        print("[🔌 WebSocket 연결 성공]")
                    except Exception as e:
                        print("[WebSocket 연결 실패]", e)
                        time.sleep(1)
                        continue

            region = get_setting("OCR_REGION")
            if not region:
                print("[⚠️ OCR 영역이 설정되지 않음]")
                time.sleep(1)
                continue

            x1, y1, x2, y2 = region
            img = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))

            # OCR 리더가 없으면 초기화
            global ocr_reader
            if ocr_reader is None:
                ocr_reader = init_ocr_reader()

            result = ocr_reader.readtext(np.array(img), detail=0)
            text = "\n".join(result).strip()
            
            # 텍스트가 없으면 건너뜀
            if not text:
                time.sleep(get_setting("OCR_INTERVAL"))
                continue
                
            print(f"[🧾 OCR 원본 텍스트]: {text}")

            # 이전 텍스트와 동일한지 확인
            if text == last_text:
                repeat_count += 1
                print(f"[🔄 동일 텍스트 감지] 반복 횟수: {repeat_count}/{MAX_REPEAT}")
                
                # 최대 반복 횟수 이상이면 이전 번역 결과 재사용
                if repeat_count >= MAX_REPEAT:
                    print(f"[⏩ 번역 스킵] 이전 번역 결과 재사용 (API 사용량 절약)")
                    translated = last_translated
                else:
                    # 최대 반복 횟수 미만이면 새로 번역
                    translated = translate_text(text)
                    last_translated = translated
            else:
                # 새로운 텍스트면 초기화 후 번역
                last_text = text
                repeat_count = 0
                translated = translate_text(text)
                last_translated = translated

            print(f"[🌐 번역 결과]: {translated}")
            print(f"[🧭 현재 출력 모드]: {output_mode}")

            if output_mode == "tk":
                overlay_label.config(text=translated)
            elif sio_connected:
                try:
                    # 디버그 로그 추가
                    print(f"[🌐 OBS 모드 번역 텍스트 전송] {translated}")
                    print(f"[🔌 현재 연결 상태] sio_connected: {sio_connected}, sio.connected: {sio.connected}")
                    
                    # 이벤트만 emit, 네임스페이스 없음
                    sio.emit("push_text", translated)
                    print("[🌐 OBS 모드: WebSocket 전송 중]")
                except Exception as e:
                    print("[WebSocket emit 실패]", e)
                    sio_connected = False

        except Exception as e:
            print("[OCR ERROR]", e)

        time.sleep(get_setting("OCR_INTERVAL"))


def start_ocr_thread(overlay_label, mode="tk"):
    global ocr_thread, ocr_running, last_text, last_translated, repeat_count
    if ocr_thread and ocr_thread.is_alive():
        print("[⚠️ OCR 스레드 이미 실행 중]")
        return
        
    # 중복 감지 변수 초기화
    last_text = ""
    last_translated = ""
    repeat_count = 0
    
    ocr_running = True
    ocr_thread = threading.Thread(target=ocr_loop, args=(overlay_label, mode), daemon=True)
    ocr_thread.start()

def stop_ocr():
    global ocr_running, sio_connected
    ocr_running = False
    
    # OBS 모드일 때 투명 모드로 전환
    if sio_connected:
        try:
            # 디버그 로그 추가
            print("[🔌 stop_ocr() 호출됨 - OBS 모드 투명화 처리 중]")
            
            # 먼저 overlay_mode 이벤트를 보내고, 약간의 지연 후 텍스트 이벤트를 보냄
            sio.emit("set_overlay_mode", "transparent")
            
            # 서버 연결 종료 전 메시지가 전송될 시간을 주기 위해 잠시 대기
            import time
            time.sleep(0.3)
            
            # 연결 종료
            sio.disconnect()
            sio_connected = False
            print("[🔌 WebSocket 연결 종료 및 투명 모드 전환 완료]")
        except Exception as e:
            print("[WebSocket 종료 중 오류]", e)