# settings.py - 제한된 언어 자동 감지 옵션 추가
import tkinter as tk
from tkinter import colorchooser, ttk, StringVar, messagebox, BooleanVar
from config import get_setting, update_setting
import keyboard
import tkinter.font as tkfont

# ✅ Tk 루트 창 초기화
root = tk.Tk()
root.withdraw()

# ✅ 설치된 폰트 필터링
available_fonts = list(tkfont.families())

# ✅ 사용하고자 하는 폰트들
base_fonts = [
    "Malgun Gothic", "Noto Sans KR", "Nanum Gothic", "맑은 고딕", "굴림",
    "돋움", "Arial", "Consolas", "Courier New", "Segoe UI",
    "Maplestory Light",        # 메이플스토리체
    "Gungsuh",                 # 궁서체
    "NanumSquareRound",        # 나눔스퀘어라운드
]

FONT_LIST = [f for f in base_fonts if f in available_fonts]

# ✅ Tk 루트 창 종료
root.destroy()

LANGUAGES = {
    "영어 (English)": "en",
    "일본어 (Japanese)": "ja",
    "중국어 (Chinese)": "zh-CN",
    "스페인어 (Spanish)": "es",
    "독일어 (German)": "de", 
    "러시아어 (Russian)": "ru",
    "한국어 (Korean)": "ko",
    "프랑스어 (French)": "fr"  # 프랑스어 추가
}

def get_language_display_name(code):
    # 언어 코드로부터 표시 이름 찾기
    for display, lang_code in LANGUAGES.items():
        if lang_code == code:
            return display
    return code

def open_settings_window(overlay_label, hotkey_callback=None, restart_ocr=None):
    win = tk.Toplevel()
    win.title("설정")
    win.geometry("360x780")  # 높이 증가
    win.resizable(False, False)

    # 전체 스크롤 가능한 프레임 생성
    canvas = tk.Canvas(win)
    scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # 기본 설정 영역
    frame = scrollable_frame

    # 단축키 설정
    tk.Label(frame, text="단축키 (예: f8)").grid(row=0, column=0, sticky="e", pady=4)
    hotkey_entry = tk.Entry(frame)
    hotkey_entry.insert(0, get_setting("HOTKEY"))
    hotkey_entry.grid(row=0, column=1, sticky="w", pady=4)

    #글로벌 핫키
    global_hotkey_var = tk.BooleanVar(value=get_setting("GLOBAL_HOTKEY", False))
    tk.Checkbutton(frame, text="글로벌 핫키 사용 (다른 창에서도 작동)", 
                variable=global_hotkey_var).grid(row=1, column=1, columnspan=2, sticky="w", pady=4)

    # 폰트 설정
    tk.Label(frame, text="폰트 종류").grid(row=1, column=0, sticky="e", pady=4)
    font_var = tk.StringVar(value=get_setting("FONT_FAMILY"))
    font_menu = ttk.Combobox(frame, textvariable=font_var, values=FONT_LIST, state="readonly")
    font_menu.grid(row=2, column=1, sticky="w", pady=4)

    tk.Label(frame, text="폰트 크기").grid(row=3, column=0, sticky="e", pady=4)
    size_spin = tk.Spinbox(frame, from_=8, to=64)
    size_spin.delete(0, "end")
    size_spin.insert(0, get_setting("FONT_SIZE"))
    size_spin.grid(row=3, column=1, sticky="w", pady=4)

    # 색상 설정
    tk.Label(frame, text="글자색").grid(row=4, column=0, sticky="e", pady=4)
    font_color_btn = tk.Button(frame, text="선택")
    font_color_btn.config(bg=get_setting("FONT_COLOR"))
    font_color_btn.grid(row=4, column=1, sticky="w", pady=4)

    tk.Label(frame, text="박스 배경색").grid(row=5, column=0, sticky="e", pady=4)
    bg_color_btn = tk.Button(frame, text="선택")
    bg_color_btn.config(bg=get_setting("OVERLAY_BG"))
    bg_color_btn.grid(row=5, column=1, sticky="w", pady=4)

    # GPU 사용 옵션
    gpu_var = tk.BooleanVar(value=get_setting("USE_GPU"))
    tk.Checkbutton(frame, text="GPU 사용 (속도 향상)", variable=gpu_var).grid(row=6, column=0, columnspan=2, pady=4)

    # OCR 주기 설정
    tk.Label(frame, text="OCR 주기 (초)").grid(row=7, column=0, sticky="e", pady=4)
    interval_spin = tk.Spinbox(frame, from_=0.1, to=10.0, increment=0.1, format="%.1f")
    interval_spin.delete(0, "end")
    interval_spin.insert(0, get_setting("OCR_INTERVAL"))
    interval_spin.grid(row=7, column=1, sticky="w", pady=4)

    # 미리보기
    preview_label = tk.Label(
        frame, text="미리보기: Hello 번역!",
        font=(font_var.get(), int(size_spin.get())),
        fg=font_color_btn["bg"], bg=bg_color_btn["bg"]
    )
    preview_label.grid(row=8, column=0, columnspan=2, pady=12, ipadx=5, ipady=5)

    # 언어 자동 감지 설정 추가
    tk.Label(frame, text="언어 설정", font=("Arial", 10, "bold")).grid(row=9, column=0, columnspan=2, pady=(10, 5))
    
    # 자동 감지 체크박스 추가
    auto_detect_var = tk.BooleanVar(value=get_setting("AUTO_DETECT_LANG", True))
    auto_detect_cb = tk.Checkbutton(frame, text="언어 자동 감지 사용", variable=auto_detect_var)
    auto_detect_cb.grid(row=10, column=0, columnspan=2, sticky="w", pady=4)
    
    # 제한된 자동 감지 체크박스 추가
    limited_auto_var = tk.BooleanVar(value=get_setting("USE_LIMITED_AUTO_DETECT", True))
    limited_auto_cb = tk.Checkbutton(frame, text="제한된 언어만 자동 감지 (추천)", variable=limited_auto_var)
    limited_auto_cb.grid(row=11, column=0, columnspan=2, sticky="w", pady=2)
    
    # 제한된 언어 목록 표시
    limited_langs = get_setting("LIMITED_AUTO_DETECT_LANGS", ["ko", "ja", "en", "zh-CN", "ru", "fr"])
    limited_langs_display = ", ".join([get_language_display_name(code) for code in limited_langs])
    limited_langs_label = tk.Label(
        frame, 
        text=f"제한된 언어 목록: {limited_langs_display}",
        justify="left", wraplength=340, fg="#666666", font=("Arial", 8)
    )
    limited_langs_label.grid(row=12, column=0, columnspan=2, sticky="w", pady=2)
    
    # 설명 레이블 추가
    auto_detect_desc = tk.Label(
        frame, 
        text="자동 감지 사용 시 원본 언어 설정은 무시됩니다.\n"
             "제한된 언어 자동 감지를 사용하면 정확도가 향상되고 API 사용량이 감소합니다.\n"
             "제한된 언어 목록에 없는 언어가 감지되면 영어로 간주합니다.",
        justify="left", wraplength=340, fg="#666666", font=("Arial", 8)
    )
    auto_detect_desc.grid(row=13, column=0, columnspan=2, sticky="w", pady=2)

    # 언어 설정 (자동 감지 체크 시 원본 언어 비활성화)
    tk.Label(frame, text="원본 언어").grid(row=14, column=0, sticky="e", pady=4)
    
    # 현재 설정된 언어에 맞는 표시 이름 찾기
    current_source = get_setting("SOURCE_LANG")
    current_target = get_setting("TARGET_LANG")
    
    current_source_display = get_language_display_name(current_source)
    current_target_display = get_language_display_name(current_target)
    
    source_var = StringVar(value=current_source_display)
    source_menu = ttk.Combobox(frame, textvariable=source_var, values=list(LANGUAGES.keys()), state="readonly", width=15)
    source_menu.grid(row=14, column=1, sticky="w", pady=4)

    # 자동 감지 체크 시 소스 언어 메뉴 및 제한 언어 옵션 비활성화
    def update_menu_states():
        if auto_detect_var.get():
            source_menu.config(state="disabled")
            limited_auto_cb.config(state="normal")
            limited_langs_label.config(state="normal")
        else:
            source_menu.config(state="readonly")
            limited_auto_cb.config(state="disabled")
            limited_langs_label.config(state="disabled")
    
    # 자동 감지 체크박스 상태 변경 이벤트 연결
    auto_detect_var.trace_add("write", lambda *args: update_menu_states())
    
    # 초기 상태 적용
    update_menu_states()

    tk.Label(frame, text="목표 언어").grid(row=15, column=0, sticky="e", pady=4)
    target_var = StringVar(value=current_target_display)
    target_menu = ttk.Combobox(frame, textvariable=target_var, values=list(LANGUAGES.keys()), state="readonly", width=15)
    target_menu.grid(row=15, column=1, sticky="w", pady=4)

    # 자동 시작 옵션 추가
    auto_restart_var = tk.BooleanVar(value=False)
    tk.Checkbutton(frame, text="설정 변경 시 자동으로 번역 시작", variable=auto_restart_var).grid(row=16, column=0, columnspan=2, pady=4)
    

    # 미리보기 업데이트 함수
    def refresh_preview(*args):
        try:
            preview_label.config(
                font=(font_var.get(), int(size_spin.get())),
                fg=font_color_btn["bg"],
                bg=bg_color_btn["bg"]
            )
        except Exception as e:
            print(f"미리보기 업데이트 오류: {e}")

    # 색상 선택 함수
    def pick_color(btn):
        color = colorchooser.askcolor()[1]
        if color:
            btn.config(bg=color)
            refresh_preview()

    # 이벤트 연결
    font_menu.bind("<<ComboboxSelected>>", refresh_preview)
    size_spin.bind("<KeyRelease>", refresh_preview)
    font_color_btn.config(command=lambda: pick_color(font_color_btn))
    bg_color_btn.config(command=lambda: pick_color(bg_color_btn))

    # 설정 저장 함수
    def apply_and_close():
        try:
            old_source_lang = get_setting("SOURCE_LANG")  # 현재 설정된 언어 저장
            old_auto_detect = get_setting("AUTO_DETECT_LANG", True)  # 이전 자동 감지 설정
            old_limited_auto = get_setting("USE_LIMITED_AUTO_DETECT", True)  # 이전 제한 자동 감지 설정
            
            # 설정 업데이트
            update_setting("HOTKEY", hotkey_entry.get().strip())
            update_setting("GLOBAL_HOTKEY", global_hotkey_var.get())
            update_setting("FONT_FAMILY", font_var.get())
            update_setting("FONT_SIZE", int(size_spin.get()))
            update_setting("FONT_COLOR", font_color_btn["bg"])
            update_setting("OVERLAY_BG", bg_color_btn["bg"])
            update_setting("USE_GPU", gpu_var.get())
            update_setting("OCR_INTERVAL", float(interval_spin.get()))
            
            # 자동 감지 설정 저장
            update_setting("AUTO_DETECT_LANG", auto_detect_var.get())
            update_setting("USE_LIMITED_AUTO_DETECT", limited_auto_var.get())
            
            # 표시 이름으로부터 언어 코드 가져오기
            selected_source_lang = LANGUAGES.get(source_var.get(), "en")
            selected_target_lang = LANGUAGES.get(target_var.get(), "ko")
            
            update_setting("SOURCE_LANG", selected_source_lang)
            update_setting("TARGET_LANG", selected_target_lang)

            # 언어 설정이나 자동 감지 설정이 변경되었는지 확인
            lang_changed = (old_source_lang != selected_source_lang or 
                          old_auto_detect != auto_detect_var.get() or
                          old_limited_auto != limited_auto_var.get())
            
            # 오버레이 업데이트
            if overlay_label:
                overlay_label.config(
                    font=(get_setting("FONT_FAMILY"), get_setting("FONT_SIZE")),
                    fg=get_setting("FONT_COLOR"),
                    bg=get_setting("OVERLAY_BG")
                )
                overlay_label.master.config(bg=get_setting("OVERLAY_BG"))

            # 단축키 재설정
            try:
                keyboard.unhook_all_hotkeys()
            except Exception as e:
                print(f"단축키 초기화 오류 (무시됨): {e}")
            
            if hotkey_callback:
                try:
                    keyboard.add_hotkey(get_setting("HOTKEY"), hotkey_callback)
                except Exception as e:
                    print(f"단축키 등록 오류 (무시됨): {e}")

            # OCR 리더 재초기화 (언어가 변경된 경우)
            if lang_changed:
                try:
                    from ocr import reinit_ocr_reader
                    reinit_ocr_reader()
                    
                    # 변경 사항 로그
                    if old_auto_detect != auto_detect_var.get():
                        print(f"[🔄 언어 자동 감지 설정 변경됨] {old_auto_detect} -> {auto_detect_var.get()}")
                    
                    if old_limited_auto != limited_auto_var.get():
                        print(f"[🔄 제한된 언어 자동 감지 설정 변경됨] {old_limited_auto} -> {limited_auto_var.get()}")
                    
                    if old_source_lang != selected_source_lang:
                        print(f"[🔄 원본 언어 변경됨] {old_source_lang} -> {selected_source_lang}")
                    
                    # 자동 시작 체크박스가 체크된 경우에만 OCR 재시작
                    if auto_restart_var.get() and restart_ocr:
                        try:
                            print("[🔄 설정 변경으로 OCR 자동 재시작]")
                            restart_ocr()
                        except Exception as e:
                            print(f"OCR 재시작 오류: {e}")
                    elif lang_changed:
                        # 설정이 변경되었으나 자동 시작이 체크되지 않은 경우
                        if auto_detect_var.get():
                            limited_text = "제한된 " if limited_auto_var.get() else ""
                            auto_mode_text = f"{limited_text}언어 자동 감지 모드"
                        else:
                            auto_mode_text = f"'{source_var.get()}' 언어"
                        messagebox.showinfo("설정 변경됨", f"언어 설정이 {auto_mode_text}로 변경되었습니다.\n필요한 경우 번역을 다시 시작하세요.")
                except Exception as e:
                    print(f"OCR 리더 재초기화 오류: {e}")
            
            win.destroy()
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 중 오류가 발생했습니다: {e}")
            print(f"설정 저장 오류: {e}")

    # 저장 버튼
    btn_frame = tk.Frame(frame)
    btn_frame.grid(row=17, column=0, columnspan=2, pady=10)
    save_btn = tk.Button(btn_frame, text="저장", command=apply_and_close, width=10)
    save_btn.pack(pady=5)