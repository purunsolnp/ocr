# core_utils.py (OBS 가이드 팝업 추가 버전)
import tkinter as tk
import os
import webbrowser
import pyperclip  # 클립보드 사용을 위한 라이브러리 (pip install pyperclip 필요)
from tkinter import simpledialog, messagebox, StringVar, BooleanVar
from config import get_setting, update_setting, make_usage_string
from presets import select_preset_gui, load_presets
from settings import open_settings_window
from overlay import create_overlay_window, update_overlay_position, hide_overlay, destroy_overlay, show_overlay
from ocr import start_ocr_thread, stop_ocr
from translator_dispatch import translate_text
import keyboard
import threading
import webview
from PIL import Image, ImageTk
import io
import urllib.request

def show_obs_setup_guide(parent, ocr_region):
    if not ocr_region:
        messagebox.showerror("오류", "OCR 영역이 설정되지 않았습니다. 먼저 OCR 위치를 설정해주세요.")
        return
    
    # 브라우저 소스 크기 계산
    x1, y1, x2, y2 = ocr_region
    browser_width = x2 - x1
    browser_height = max(120, int((y2 - y1) * 0.4))  # 대사창 스타일에 맞게 40%로 조정
    
    # OBS 가이드 창 생성
    guide_win = tk.Toplevel(parent)
    guide_win.title("OBS 설정 가이드")
    guide_win.geometry("500x450")
    guide_win.resizable(False, False)
    
    # 상단 제목
    tk.Label(guide_win, text="OBS 브라우저 소스 설정 방법", font=("Arial", 14, "bold")).pack(pady=10)
    
    # 안내 텍스트
    guide_text = f"""
1️⃣ OBS Studio를 실행하세요.

2️⃣ 장면(Scene)을 선택하고 소스 목록에서 '+' 버튼을 클릭하세요.

3️⃣ '브라우저'를 선택하고 소스 이름을 입력하세요(예: '소나기OCR').

4️⃣ 브라우저 속성에서 다음 설정을 입력하세요:
   • URL: http://localhost:5000/overlay
   • 너비: {browser_width}px
   • 높이: {browser_height}px
   • 사용자 지정 CSS: 
     body {{ 
       margin: 0; 
       padding: 0; 
       overflow: visible; 
       background-color: transparent; 
     }}

5️⃣ '확인'을 클릭하여 브라우저 소스를 생성하세요.

6️⃣ 브라우저 소스를 OCR 영역 위에 배치하세요.

7️⃣ 텍스트가 잘리면 브라우저 소스 높이를 150-180px 정도로 늘려보세요.

8️⃣ 소나기OCR에서 '출력 모드'를 'OBS'로 선택하고 번역을 시작하세요.
"""
    
    text_frame = tk.Frame(guide_win)
    text_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    guide_textbox = tk.Text(text_frame, wrap="word", height=18, font=("Arial", 10))
    guide_textbox.insert("1.0", guide_text)
    guide_textbox.config(state="disabled")  # 읽기 전용
    guide_textbox.pack(fill="both", expand=True)
    
    # 크기 정보를 클립보드에 복사하는 버튼
    def copy_size_to_clipboard():
        size_text = f"너비: {browser_width}px, 높이: {browser_height}px"
        pyperclip.copy(size_text)
        messagebox.showinfo("복사 완료", "브라우저 소스 크기가 클립보드에 복사되었습니다.")
    
    # CSS를 클립보드에 복사하는 버튼 추가
    def copy_css_to_clipboard():
        css_text = "body { margin: 0; padding: 0; overflow: visible; background-color: transparent; }"
        pyperclip.copy(css_text)
        messagebox.showinfo("복사 완료", "사용자 지정 CSS가 클립보드에 복사되었습니다.")
    
    # OBS 웹사이트 열기 함수
    def open_obs_website():
        webbrowser.open("https://obsproject.com/ko/download")
    
    button_frame = tk.Frame(guide_win)
    button_frame.pack(fill="x", padx=20, pady=10)
    
    tk.Button(button_frame, text="크기 정보 복사", command=copy_size_to_clipboard).pack(side="left", padx=5)
    tk.Button(button_frame, text="CSS 복사", command=copy_css_to_clipboard).pack(side="left", padx=5)
    tk.Button(button_frame, text="OBS 다운로드", command=open_obs_website).pack(side="left", padx=5)
    tk.Button(button_frame, text="닫기", command=guide_win.destroy).pack(side="right", padx=5)
    
    # 체크박스: 이 안내를 다시 표시하지 않음
    show_again_var = tk.BooleanVar(value=True)
    tk.Checkbutton(guide_win, text="다음에 OCR 영역 설정 시 이 안내 표시", variable=show_again_var).pack(pady=5)
    
    # 창이 닫힐 때 설정 저장
    def on_guide_close():
        update_setting("SHOW_OBS_GUIDE", show_again_var.get())
        guide_win.destroy()
    
    guide_win.protocol("WM_DELETE_WINDOW", on_guide_close)
    guide_win.transient(parent)  # 부모 창 위에 표시
    guide_win.grab_set()  # 모달 창으로 설정

# 🔲 마우스로 드래그해서 영역 선택 (fullscreen으로)
def select_area(callback):
    temp = tk.Toplevel()
    temp.attributes("-fullscreen", True)
    temp.attributes("-alpha", 0.3)
    temp.attributes("-topmost", True)
    temp.configure(bg="black")
    temp.overrideredirect(True)

    canvas = tk.Canvas(temp, bg="black")
    canvas.pack(fill="both", expand=True)

    rect = None
    start_x = start_y = 0
    temp_box = get_setting("SHOW_OCR_BOX")
    show_box = True if temp_box is None else temp_box
    def on_mouse_down(event):
        nonlocal start_x, start_y, rect
        start_x, start_y = event.x, event.y
        if show_box:
            rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline="red", width=2)

    def on_mouse_move(event):
        if show_box and rect:
            canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        end_x, end_y = event.x, event.y
        x1, y1 = min(start_x, end_x), min(start_y, end_y)
        x2, y2 = max(start_x, end_x), max(start_y, end_y)
        temp.destroy()
        callback((x1, y1, x2, y2))

    canvas.bind("<Button-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    temp.mainloop()


# 🪟 상태창 + overlay + 버튼 등 전체 생성
def create_status_window():
    translating = False
    overlay_label = create_overlay_window()
    hide_overlay()

    win = tk.Toplevel()
    win.title("소나기OCR")
    win.iconbitmap("rururu.ico")
    win.geometry("280x720")  # 창 너비를 260에서 280으로 증가
    win.resizable(False, False)

    btn_width = 24  # 버튼 너비 증가 (22에서 24로)

    # 상태 표시줄에 padding 추가하여 드래그 영역 확장
    status = tk.Label(win, text="⚫ 번역 미사용", bg="#888888", fg="white", 
                     font=("Arial", 12, "bold"), padx=10, pady=5)  # padding 추가
    status.pack(fill="x")

    usage = tk.Label(win, text=make_usage_string(), justify="left")
    usage.pack(pady=5)

    engine_var = StringVar(value=get_setting("ENGINE"))
    engine_dropdown = tk.OptionMenu(win, engine_var, "gpt", "papago-nhn", "deepl", "libretranslate")
    engine_dropdown.config(width=btn_width - 6)
    engine_dropdown.pack(pady=2)

    tk.Label(win, text="출력 모드 선택").pack()
    mode_var = StringVar(value=get_setting("OUTPUT_MODE"))
    
    def on_mode_change():
        mode = mode_var.get()
        update_setting("OUTPUT_MODE", mode)
        print(f"[🔄 출력 모드 변경됨]: {mode}")
        
        # OBS 모드에서는 오버레이 숨기기, TK 모드에서는 필요시 다시 표시
        if translating:  # 번역 중일 때만 적용
            if mode == "obs":
                hide_overlay()
                print("[🔍 OBS 모드: 오버레이 숨김]")
            else:
                show_overlay()
                update_overlay_position()
                print("[🔍 TK 모드: 오버레이 표시]")
    
    # 라디오 버튼 가로로 배치
    mode_frame = tk.Frame(win)
    mode_frame.pack()
    tk.Radiobutton(mode_frame, text="일반", variable=mode_var, value="tk", command=on_mode_change).pack(side="left", padx=10)
    tk.Radiobutton(mode_frame, text="OBS", variable=mode_var, value="obs", command=on_mode_change).pack(side="left", padx=10)

    show_box_value = get_setting("SHOW_OCR_BOX")
    show_box_var = BooleanVar(value=True if show_box_value is None else show_box_value)
    def on_show_box_change():
        update_setting("SHOW_OCR_BOX", show_box_var.get())
    tk.Checkbutton(win, text="🟥 OCR 박스 보이기", variable=show_box_var, command=on_show_box_change).pack()

    toggle_btn = tk.Button(win, text="▶️ 번역 시작", width=btn_width)
    toggle_btn.pack(pady=2)

    def update_status(running):
        engine = get_setting("ENGINE").upper()
        win.after(0, lambda: status.config(
            text=f"🟢 번역 켜 ({engine})" if running else "⚫ 번역 미사용",
            bg="#3cb043" if running else "#888888"
        ))
        win.after(0, lambda: usage.config(text=make_usage_string()))
        toggle_btn.config(text="⏸️ 번역 중단" if running else "▶️ 번역 시작")
        
        # 번역이 켜지면 상태창에 현재 언어 정보 표시
        if running:
            source_lang = get_setting("SOURCE_LANG")
            target_lang = get_setting("TARGET_LANG")
            print(f"[✅ 현재 번역 언어] {source_lang} → {target_lang}")

    def toggle_translate():
        nonlocal translating

        if translating:
            translating = False
            stop_ocr()
            hide_overlay()
            update_status(False)
        else:
            if not get_setting("OCR_REGION"):
                messagebox.showerror("오류", "OCR 영역이 설정되지 않았습니다. OCR 위치 재설정을 먼저 해주세요.")
                return
                
            if mode_var.get() != "obs" and not get_setting("OUTPUT_POSITION"):
                messagebox.showerror("오류", "출력 위치가 설정되지 않았습니다. Overlay 위치 재설정을 먼저 해주세요.")
                return
            
            translating = True
            engine = engine_var.get()
            update_setting("ENGINE", engine)
            mode = mode_var.get() or "tk"
            print(f"[⚙️ 설정된 출력 모드]: {mode}")

            from ocr import reinit_ocr_reader
            reinit_ocr_reader()
            start_ocr_thread(overlay_label, mode)
            
            if mode == "obs":
                hide_overlay()
                print("[🔍 OBS 모드: 오버레이 숨김]")
            else:
                overlay_label.master.deiconify()
                update_overlay_position()
                overlay_label.config(text="로딩 중...")
                show_overlay()
                print("[🔍 TK 모드: 오버레이 표시]")

            update_status(True)


    # 토글 버튼에 명령 연결
    toggle_btn.config(command=toggle_translate)

    def ocr_reset():
        def on_area_selected(box):
            update_setting("OCR_REGION", box)
            messagebox.showinfo("완료", "OCR 영역이 설정되었습니다.")
            
            # OBS 출력 모드인 경우 가이드 표시
            if mode_var.get() == "obs" and get_setting("SHOW_OBS_GUIDE", True):
                show_obs_setup_guide(win, box)
        
        select_area(on_area_selected)

    def overlay_reset():
        if mode_var.get() == "obs":
            messagebox.showinfo("OBS 모드", "OBS 모드에서는 Overlay 위치 재설정이 필요하지 않습니다.\nOBS 브라우저 소스에서 직접 조절하세요.")
            return
        select_area(lambda pos: (
            update_setting("OUTPUT_POSITION", (pos[0], pos[1])),
            update_overlay_position()
        ))
        messagebox.showinfo("완료", "Overlay 위치가 설정되었습니다.")

    def reset_to_default():
        update_setting("OCR_REGION", (200, 800, 1700, 1000))
        update_setting("OUTPUT_POSITION", (600, 850))
        destroy_overlay()
        new_overlay = create_overlay_window()
        hide_overlay()
        nonlocal overlay_label
        overlay_label = new_overlay
        update_overlay_position()
        messagebox.showinfo("초기화 완료", "기본 프리셋 위치로 초기화되었습니다.")

    def save_preset():
        name = simpledialog.askstring("프리셋 저장", "프리셋 이름을 입력하세요:")
        if name:
            ocr = get_setting("OCR_REGION")
            out = get_setting("OUTPUT_POSITION")
            with open("presets.txt", "a", encoding="utf-8") as f:
                f.write(f"{name}|{','.join(map(str, ocr))}|{','.join(map(str, out))}\n")
            messagebox.showinfo("프리셋 저장", f"'{name}' 프리셋이 저장되었습니다.")

    def load_preset():
        presets = load_presets()
        selected = select_preset_gui(presets)
        if selected:
            messagebox.showinfo("프리셋 불러오기", f"'{selected}' 프리셋이 적용되었습니다.")

# core_utils.py 파일의 generate_nhn_papago 함수 개선

    def generate_nhn_papago():
        # 안내 메시지 먼저 표시
        messagebox.showinfo(
            "NHN Papago API 설정 안내",
            "NHN(네이버) Papago 번역 API를 사용하려면 다음과 같이 설정하세요:\n\n"
            "1. 네이버 클라우드 플랫폼(https://www.ncloud.com)에 가입하세요\n"
            "2. 콘솔 > AI·NAVER API > Papago NMT에서 서비스를 활성화하세요\n"
            "3. 콘솔 > 계정 관리 > API 인증키 관리에서 Client ID와 Client Secret을 확인하세요\n\n"
            "이제 API 키 정보를 입력해주세요."
        )
        
        client_id = simpledialog.askstring("NHN Papago API 설정", "Client ID를 입력하세요:")
        
        if not client_id:
            print("[⚠️ NHN Papago API 설정 취소됨] Client ID 입력 취소")
            return
        
        client_secret = simpledialog.askstring("NHN Papago API 설정", "Client Secret을 입력하세요:")
        
        if not client_secret:
            print("[⚠️ NHN Papago API 설정 취소됨] Client Secret 입력 취소")
            return
        
        # 키가 모두 입력된 경우
        try:
            # 키 형식 확인 (앞뒤 공백 제거)
            client_id = client_id.strip()
            client_secret = client_secret.strip()
            
            # 키 저장
            with open("papago_nhn.txt", "w", encoding="utf-8") as f:
                f.write(f"{client_id}|{client_secret}")
            
            print(f"[✅ NHN Papago API 키 저장됨] Client ID: {client_id[:4]}...")
            
            # 확인 메시지에 도움말 포함
            messagebox.showinfo(
                "NHN Papago API 설정 완료", 
                "Papago API 설정이 완료되었습니다!\n\n"
                "이제 '번역 시작' 버튼을 눌러 번역을 시작하세요.\n"
                "번역 엔진 드롭다운에서 'papago-nhn'을 선택해야 합니다."
            )
            
            # 바로 API 키 테스트
            try:
                from translator_nhn import load_nhn_keys
                test_id, test_secret = load_nhn_keys()
                if test_id and test_secret:
                    if test_id == client_id and len(test_secret) > 5:
                        print(f"[✅ NHN Papago API 키 저장 및 로드 성공]")
                    else:
                        print(f"[⚠️ NHN Papago API 키 형식 경고] 저장된 키와 로드된 키가 일치하지 않습니다")
                else:
                    print(f"[⚠️ NHN Papago API 키 로드 실패]")
            except Exception as e:
                print(f"[⚠️ NHN Papago API 키 테스트 오류]: {e}")
                    
        except Exception as e:
            print(f"[⚠️ NHN Papago API 키 저장 오류]: {e}")
            messagebox.showerror("오류", f"파일 생성에 실패했습니다. 오류: {e}")

    def generate_deepl():
        key = simpledialog.askstring("DeepL API Key", "DeepL API Key를 입력하세요:")
        if key:
            try:
                with open("deepl.txt", "w", encoding="utf-8") as f:
                    f.write(key)
                messagebox.showinfo("완료", "deepl.txt 파일이 생성되었습니다!")
            except:
                messagebox.showerror("오류", "파일 생성에 실패했습니다.")
    def setup_libretranslate():
        # LibreTranslate API URL 설정
        api_url = simpledialog.askstring(
            "LibreTranslate API URL", 
            "LibreTranslate API URL을 입력하세요:\n(기본값: https://libretranslate.com/translate)",
            initialvalue=get_setting("LIBRE_API_URL") or "https://libretranslate.com/translate"
        )
        
        if api_url:
            update_setting("LIBRE_API_URL", api_url)
        
        # API 키 설정 (선택 사항)
        api_key = simpledialog.askstring(
            "LibreTranslate API Key (선택사항)", 
            "API 키가 있다면 입력하세요:\n(없으면 비워두세요)",
            initialvalue=get_setting("LIBRE_API_KEY") or ""
        )
        
        if api_key is not None:  # 취소를 누르지 않았다면
            update_setting("LIBRE_API_KEY", api_key)
            
            # 설정 저장
            try:
                with open("libretranslate.txt", "w", encoding="utf-8") as f:
                    f.write(f"{api_url}|{api_key}")
                messagebox.showinfo("완료", "LibreTranslate API 설정이 저장되었습니다!")
            except:
                messagebox.showerror("오류", "LibreTranslate 설정 파일 생성에 실패했습니다.")
                
    def quit_program():
        import requests
        stop_ocr()
        
        # Flask 서버 종료 시도
        try:
            requests.get("http://localhost:5000/shutdown", timeout=1)
            print("🛑 Flask 서버 종료 요청 전송됨")
        except:
            print("⚠️ Flask 서버 종료 실패 (이미 종료되었거나 응답 없음)")
        
        # Tkinter 정리
        try:
            if win and win.winfo_exists():
                win.destroy()
        except:
            pass
            
        # 강제 종료
        os._exit(0)

    win.protocol("WM_DELETE_WINDOW", quit_program)

    # 모든 버튼 너비 조정
    tk.Button(win, text="📐 OCR 위치 재설정", command=ocr_reset, width=btn_width).pack(pady=2)
    tk.Button(win, text="🖼️ Overlay 위치 재설정", command=overlay_reset, width=btn_width).pack(pady=2)
    tk.Button(win, text="📂 프리셋 저장", command=save_preset, width=btn_width).pack(pady=2)
    tk.Button(win, text="📂 프리셋 불러오기", command=load_preset, width=btn_width).pack(pady=2)
    tk.Button(win, text="🧹 프리셋 리셋", command=reset_to_default, width=btn_width).pack(pady=2)
    tk.Button(win, text="☁️ NHN Papago API 입력", command=generate_nhn_papago, width=btn_width).pack(pady=2)
    tk.Button(win, text="🔑 DeepL API 입력", command=generate_deepl, width=btn_width).pack(pady=2)
    tk.Button(win, text="🌍 LibreTranslate 설정", command=setup_libretranslate, width=btn_width).pack(pady=2)
    tk.Button(win, text="⚙️ 설정", command=lambda: open_settings_window(overlay_label, toggle_translate, restart_ocr=toggle_translate), width=btn_width).pack(pady=2)
    tk.Button(win, text="❌ 프로그램 종료", command=quit_program, width=btn_width).pack(pady=2)

    # 블로그 링크
    blog = tk.Label(win, text="🔗 블로그: sonagi-psy", fg="blue", cursor="hand2") 
    blog.pack(pady=5)
    blog.bind("<Button-1>", lambda e: webbrowser.open("https://sonagi-psy.tistory.com/8"))
    
    # AdSense 웹뷰 프레임 생성 (상시 노출)
    ad_frame = tk.Frame(win, height=100, bg="#f5f5f5")
    ad_frame.pack(side="bottom", fill="x", pady=5)

    # 제목 레이블
    tk.Label(ad_frame, text="💫개발자 지원하기", bg="#f5f5f5", fg="#333333", font=("Arial", 9, "bold")).pack(pady=(5, 2))

    # 버튼 프레임
    button_frame = tk.Frame(ad_frame, bg="#f5f5f5")
    button_frame.pack(pady=2)

    # Buy Me a Coffee 버튼
    coffee_btn = tk.Button(
        button_frame, 
        text="☕제작자 후원", 
        bg="#FFDD00", fg="#000000",
        command=lambda: webbrowser.open("https://www.buymeacoffee.com/sonagi")
    )
    coffee_btn.pack(side="left", padx=5)

    # 광고 보기 버튼
    ad_btn = tk.Button(
        button_frame,
        text="🌐 광고 보기",
        bg="#4285F4", fg="white", 
        command=lambda: webbrowser.open("https://sonagi-psy.tistory.com/15")
    )
    ad_btn.pack(side="left", padx=5)
    
    return {
        "status": win,
        "overlay": overlay_label,
        "toggle_button": toggle_btn,
        "output_mode_var": mode_var
        # "support_component": support_component  <- 이 부분 삭제 또는 주석 처리
    }

def create_support_component(parent_window):
    """후원 및 광고 컴포넌트 생성"""
    support_frame = tk.Frame(parent_window, bg="#f5f5f5")
    support_frame.pack(fill="x", side="bottom", pady=5)
    
    # 구분선 추가
    separator = tk.Frame(support_frame, height=1, bg="#cccccc")
    separator.pack(fill="x", pady=5)
    
    # 1. Buy Me a Coffee 후원 버튼
    def create_buymeacoffee_button():
        button_frame = tk.Frame(support_frame, bg="#f5f5f5")
        button_frame.pack(pady=5)
        
        # 이미지를 가져오거나 로컬에 저장된 이미지 사용
        try:
            # 온라인 이미지 가져오기 (또는 로컬 파일 사용)
            img_url = "https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
            with urllib.request.urlopen(img_url) as u:
                raw_data = u.read()
            img = Image.open(io.BytesIO(raw_data))
            img = img.resize((160, 40), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # 이미지 버튼
            btn = tk.Button(button_frame, image=photo, bd=0, 
                          command=lambda: webbrowser.open("https://www.buymeacoffee.com/sonagi"))
            btn.image = photo  # 참조 유지
            btn.pack()
        except:
            # 이미지 로드 실패 시 텍스트 버튼
            btn = tk.Button(button_frame, text="☕ Buy me a coffee", bg="#FFDD00", fg="#000000",
                         command=lambda: webbrowser.open("https://www.buymeacoffee.com/sonagi"))
            btn.pack()
        
        return button_frame
    
    buymeacoffee_btn = create_buymeacoffee_button()
    
    # 2. 내장 광고 웹뷰 (소나기 블로그 AdSense)
    ad_frame = tk.Frame(support_frame)
    ad_frame.pack(pady=5, fill="x")
    
    ad_label = tk.Label(ad_frame, text="💫 소나기OCR 후원 광고", bg="#f5f5f5", fg="#333333")
    ad_label.pack()
    
    # 웹뷰 구현 (pywebview 사용)
    def open_embedded_webview():
        try:
            # 웹뷰 프레임 생성
            webview_frame = tk.Frame(support_frame, height=150)
            webview_frame.pack(fill="x", expand=True, pady=5)
            
            # 별도 스레드에서 웹뷰 실행
            def run_webview():
                webview.create_window(
                    'ad_window',  # 창 제목
                    'https://sonagi-psy.tistory.com/15',  # AdSense가 포함된 블로그 페이지
                    width=280,
                    height=150,
                    x=parent_window.winfo_x(),
                    y=parent_window.winfo_y() + parent_window.winfo_height() - 200,
                    resizable=True,
                    frameless=True
                )
                webview.start()
            
            threading.Thread(target=run_webview, daemon=True).start()
            return webview_frame
        except Exception as e:
            print(f"[⚠️ 광고 웹뷰 오류]: {e}")
            # 오류 발생 시 대체 버튼
            fallback_btn = tk.Button(
                support_frame, 
                text="블로그 방문하여 후원하기", 
                command=lambda: webbrowser.open("https://sonagi-psy.tistory.com/15")
            )
            fallback_btn.pack(pady=5)
            return fallback_btn
    
    # pywebview 지원 확인 후 광고 열기
    try:
        import webview
        open_embedded_webview_btn = tk.Button(
            ad_frame, 
            text="광고 표시하기", 
            command=open_embedded_webview
        )
        open_embedded_webview_btn.pack(pady=5)
    except ImportError:
        # webview 라이브러리가 없을 경우 대체 버튼
        fallback_btn = tk.Button(
            ad_frame, 
            text="브라우저에서 광고 보기", 
            command=lambda: webbrowser.open("https://sonagi-psy.tistory.com/15")
        )
        fallback_btn.pack(pady=5)
    
    return support_frame