# translator_libre.py
import requests
from config import get_setting, increment_libre_usage

def load_libretranslate_config():
    """저장된 LibreTranslate 설정을 로드합니다."""
    try:
        with open("libretranslate.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()
            parts = content.split("|")
            api_url = parts[0]
            api_key = parts[1] if len(parts) > 1 else ""
            return api_url, api_key
    except Exception as e:
        print(f"[정보] LibreTranslate 설정 로드 실패 (파일이 없을 수 있음): {e}")
        return get_setting("LIBRE_API_URL"), get_setting("LIBRE_API_KEY")

def libre_translate(text):
    # LibreTranslate API URL 및 키 가져오기
    api_url, api_key = load_libretranslate_config()
    
    # 설정값으로 갱신
    api_url = api_url or get_setting("LIBRE_API_URL") or "https://libretranslate.com/translate"
    
    # 언어 코드 매핑
    LANG_MAP = {
        "en": "en",
        "ko": "ko",
        "ja": "ja",
        "zh": "zh",
        "zh-CN": "zh",
        "es": "es",
        "de": "de",
        "ru": "ru",
        "fr": "fr",
        "it": "it",
        "pt": "pt"
    }
    
    source = LANG_MAP.get(get_setting("SOURCE_LANG"), "en")
    target = LANG_MAP.get(get_setting("TARGET_LANG"), "ko")
    
    # 소스와 타겟 언어가 같으면 번역 필요 없음
    if source == target:
        return text
    
    # API 요청 데이터 준비
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text"
    }
    
    # API 키가 있으면 추가
    if api_key:
        payload["api_key"] = api_key
        
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"[🌐 LibreTranslate 요청] {source} → {target}, 텍스트 길이: {len(text)}자")
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()  # HTTP 오류 발생시 예외 처리
        
        result = response.json().get("translatedText", "")
        
        # 사용량 추적
        increment_libre_usage(len(text))
        print(f"[LibreTranslate 사용량 누적] 이번 번역: {len(text)}자")
        
        return result
    except requests.exceptions.HTTPError as e:
        print(f"[LibreTranslate HTTP 오류] {e.response.status_code} - {e.response.text}")
        return f"(LibreTranslate 번역 실패 - HTTP 오류 {e.response.status_code})"
    except requests.exceptions.ConnectionError:
        print(f"[LibreTranslate 연결 오류] API URL: {api_url}")
        return "(LibreTranslate 연결 실패 - 서버에 접속할 수 없습니다)"
    except Exception as e:
        print(f"[LibreTranslate 예외] {e}")
        return "(LibreTranslate 번역 실패)"