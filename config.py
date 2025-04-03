# config.py
import datetime

# ⚙️ 유저 설정 (딕셔너리 기반으로 관리)
settings = {
    "OCR_REGION": (200, 800, 1700, 1000),
    "OUTPUT_POSITION": [600, 850],
    "FONT_FAMILY": "Malgun Gothic",
    "FONT_SIZE": 16,
    "FONT_COLOR": "white",
    "OUTPUT_MODE": "tk", 
    "OVERLAY_BG": "black",
    "HOTKEY": "f8",
    "GLOBAL_HOTKEY": True,  # 기본값은 로컬 핫키
    "ENGINE": "papago-nhn",  # ✅ 기본 번역 엔진: NHN Papago
    "USE_GPU": False,
    "OCR_INTERVAL": 1.0,
    "SOURCE_LANG": "en",
    "TARGET_LANG": "ko",
    "BROWSER_WIDTH": 1920,
    "BROWSER_HEIGHT": 1080,
    "VERTICAL": None,
    "PRIMARY_MONITOR_SIDE": None,
    "LIBRE_API_URL": "https://libretranslate.com/translate",  # LibreTranslate API URL
    "LIBRE_API_KEY": ""  # LibreTranslate API 키 (선택사항)
}

# 설정 업데이트 함수
def update_setting(key, value):
    if key in settings:
        settings[key] = value

# 설정 가져오기 함수
def get_setting(key, default=None):
    try:
        value = settings.get(key, default)
        # 디버깅을 위한 로그 추가
        if key in ["AUTO_DETECT_LANG", "USE_LIMITED_AUTO_DETECT"] and value is None:
            print(f"[⚠️ 설정 기본값] {key}: {default}")
        return value
    except Exception as e:
        print(f"[⚠️ get_setting() 오류] {key}: {e}")
        return default

from config import settings

def load_settings():
    return settings

# 📊 사용량 추적
TOKEN_USAGE = 0
NHN_PAPAGO_USAGE = 0
DEEPL_USAGE = 0
LIBRE_USAGE = 0
PAPAGO_LIMIT = 5000000
DEEPL_LIMIT = 500000
LIBRE_LIMIT = 5000000  # LibreTranslate 한도 (가정)

# 💸 GPT 가격 정보
PRICE_PER_1K_TOKENS = 0.0015  # USD

# 사용량 증가 함수
def increment_token_usage(amount):
    global TOKEN_USAGE
    TOKEN_USAGE += amount

def increment_nhn_papago_usage(amount):
    global NHN_PAPAGO_USAGE
    NHN_PAPAGO_USAGE += amount

def increment_deepl_usage(amount):
    global DEEPL_USAGE
    DEEPL_USAGE += amount

def increment_libre_usage(amount):
    global LIBRE_USAGE
    LIBRE_USAGE += amount

# 사용량 문자열 반환 함수
def make_usage_string():
    engine = get_setting("ENGINE")
    lines = []

    if engine == "gpt":
        gpt_dollars = TOKEN_USAGE / 1000 * PRICE_PER_1K_TOKENS
        lines.append(f"🧠 GPT 사용량: {TOKEN_USAGE:,} tokens (${gpt_dollars:.4f})")

    elif engine == "papago-nhn":
        percent = NHN_PAPAGO_USAGE / PAPAGO_LIMIT * 100
        lines.append(f"🌐 NHN Papago 사용량: {NHN_PAPAGO_USAGE:,} / {PAPAGO_LIMIT:,}자 ({percent:.1f}%)")

    elif engine == "deepl":
        percent = DEEPL_USAGE / DEEPL_LIMIT * 100
        lines.append(f"🔤 DeepL 사용량: {DEEPL_USAGE:,} / {DEEPL_LIMIT:,}자 ({percent:.1f}%)")
        
    elif engine == "libretranslate":
        percent = LIBRE_USAGE / LIBRE_LIMIT * 100
        lines.append(f"🔠 LibreTranslate 사용량: {LIBRE_USAGE:,} / {LIBRE_LIMIT:,}자 ({percent:.1f}%)")

    return "\n".join(lines)