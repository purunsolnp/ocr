# overlay_webserver.py (번역 문제 해결)
from flask import Flask, render_template, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
from config import get_setting
import json
import os
import sys

# PyInstaller 리소스 경로 처리
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Flask 앱 초기화 (템플릿 폴더 경로 설정)
app = Flask(__name__, 
            template_folder=resource_path('templates'), 
            static_folder=resource_path('static'))

# 로깅 옵션 제거 또는 False로 설정
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

# 텍스트 상태 저장
default_text = "(번역 없음)"
latest_text = default_text

# overlay_webserver.py의 run_flask_server 함수 수정
def run_flask_server():
    print("🌐 Flask 서버 실행 중 (OBS 모드)")
    import threading
    # debug=True 제거 및 다른 옵션 간소화
    threading.Thread(target=lambda: socketio.run(app, host="127.0.0.1", port=5000), daemon=True).start()

@app.route("/overlay")
def serve_overlay_display():
    return render_template("overlay_display.html")

@app.route("/overlay/edit")
def edit_overlay():
    return render_template("overlay_edit.html")

# 오버레이 설정값 가져오는 API
@app.route("/get_overlay_settings")
def get_overlay_settings():
    settings = {
        "fontFamily": get_setting("FONT_FAMILY") or "Malgun Gothic",
        "fontSize": get_setting("FONT_SIZE") or 16,
        "fontColor": get_setting("FONT_COLOR") or "white",
        "backgroundColor": get_setting("OVERLAY_BG") or "rgba(0, 0, 0, 0.5)"
    }
    
    print(f"[⚙️ 오버레이 설정 요청됨]: {settings}")
    return jsonify(settings)

@app.route("/get_browser_size")
def get_browser_size():
    ocr_region = get_setting("OCR_REGION")
    if not ocr_region:
        return jsonify({"width": 800, "height": 120})  # 기본값
    
    x1, y1, x2, y2 = ocr_region
    width = x2 - x1
    height = y2 - y1  # 원본 높이
    
    # 대사창 스타일 번역 오버레이에 적합한 높이 (원본의 약 40%)
    recommended_height = max(120, int(height * 0.4))
    
    print(f"[📏 OCR 기반 브라우저 권장 크기]: 너비: {width}px, 높이: {recommended_height}px")
    return jsonify({
        "width": width, 
        "height": height,
        "recommended_height": recommended_height
    })

@app.route("/save_overlay_position", methods=["POST"])
def save_overlay_position():
    data = request.get_json()
    x = int(data.get("x", 600))
    y = int(data.get("y", 850))

    # config.json에 저장
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        config["OUTPUT_POSITION"] = [x, y]
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return jsonify(success=True)
    except Exception as e:
        print(f"[⚠️ 오버레이 위치 저장 오류]: {e}")
        # 설정 객체에 직접 저장
        from config import update_setting
        update_setting("OUTPUT_POSITION", [x, y])
        return jsonify(success=True, message="config.json 파일 없음, 메모리에만 저장됨")

@app.route("/get_overlay_position")
def get_overlay_position():
    pos = list(get_setting("OUTPUT_POSITION") or [600, 850])
    print(f"[📍 get_overlay_position 요청]: {pos}")
    return jsonify({"x": pos[0], "y": pos[1]})

# WebSocket 이벤트 핸들러
@socketio.on("connect")
def handle_connect():
    print("[🌐 WebSocket 연결됨]")
    # 연결 즉시 최신 텍스트 전송
    emit("overlay_text", latest_text)

@socketio.on("disconnect")
def handle_disconnect():
    print("[🔌 WebSocket 연결 끊김]")

# 최신 텍스트 요청 이벤트 추가
@socketio.on("get_latest_text")
def handle_get_latest_text():
    print("[📤 최신 텍스트 요청됨]")
    emit("overlay_text", latest_text)

# push_text 이벤트 핸들러
@socketio.on("push_text")
def handle_push(data):
    global latest_text
    # 기본 텍스트를 명시적으로 처리
    latest_text = data if data else default_text
    print(f"[✅ push_text 수신]: {latest_text}")
    
    # 모든 클라이언트에 브로드캐스트
    emit("overlay_text", latest_text, broadcast=True)

@socketio.on("set_overlay_mode")
def handle_set_overlay_mode(mode):
    global latest_text
    
    # 디버그 로깅 추가
    print(f"[🔍 set_overlay_mode 이벤트 수신] 모드: {mode}")
    
    if mode == 'transparent':
        # 투명 모드로 설정
        latest_text = default_text
        print("[🔍 오버레이 투명 모드 설정 - 서버 측 처리]")
        
        # 먼저 모드를 설정하고, 텍스트는 설정하지 않음
        # 클라이언트는 투명 모드 이벤트만으로 처리 가능
        emit("set_overlay_mode", mode, broadcast=True)
    else:
        # 일반 모드로 설정
        print("[🔍 오버레이 일반 모드 설정 - 서버 측 처리]")
        
        # 모드를 먼저 보내고, 최신 텍스트를 다시 보냄
        emit("set_overlay_mode", mode, broadcast=True)
        
        # 최신 텍스트가 있는 경우 다시 보냄 (일반 모드에서만)
        if latest_text and latest_text != default_text:
            emit("overlay_text", latest_text, broadcast=True)
@app.route('/shutdown')
def shutdown():
    try:
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            # 다른 종료 방법 시도
            import os
            os._exit(0)
        func()
        return 'Server shutting down...'
    except:
        # 강제 종료
        import os
        os._exit(0)

# 웹서버 상태 확인용 라우트
@app.route('/status')
def status():
    return jsonify({
        "status": "ok",
        "latest_text": latest_text,
        "settings": {
            "font_family": get_setting("FONT_FAMILY"),
            "font_size": get_setting("FONT_SIZE"),
            "font_color": get_setting("FONT_COLOR"),
            "background_color": get_setting("OVERLAY_BG")
        }
    })

if __name__ == "__main__":
    socketio.run(app, port=5000, debug=True)