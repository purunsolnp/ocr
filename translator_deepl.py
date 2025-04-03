import requests
from config import get_setting, increment_deepl_usage

# DeepL API 키 로드 함수
def load_deepl_key():
    try:
        with open("deepl.txt", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"[⚠️ DeepL API 키 로드 오류]: {e}")
        return ""

# 언어 코드 정규화 함수 추가
def normalize_lang_code(lang_code):
    """언어 코드를 정규화하여 다양한 형식의 언어 코드를 통일된 형식으로 변환"""
    if not lang_code:
        return ""
        
    # 소문자로 변환
    lang_code = lang_code.lower()
    
    # 중국어 코드 정규화 (zh, zh-cn, zh-CN 등을 모두 zh-cn으로 통일)
    if lang_code == "zh" or lang_code.startswith("zh-"):
        return "zh-cn"
        
    return lang_code

# DeepL API를 이용한 번역 함수 (source_lang 매개변수 추가)
def deepl_translate(text, source_lang=None):
    # 빈 텍스트는 번역하지 않음
    if not text:
        return ""
    
    # DeepL API 키 가져오기
    api_key = load_deepl_key()
    if not api_key:
        print(f"[⚠️ DeepL API 키가 설정되지 않았습니다]")
        return "(DeepL API 키가 설정되지 않았습니다)"
    
    # 제한된 자동 감지 지원 언어
    LIMITED_LANGS = get_setting("LIMITED_AUTO_DETECT_LANGS") or ["ko", "ja", "en", "zh-CN", "zh", "ru", "fr"]
    
    # DeepL API 언어 코드로 변환
    DEEPL_LANGS = {
        "ko": "KO",
        "en": "EN",
        "ja": "JA",
        "zh-cn": "ZH",
        "zh-CN": "ZH",
        "zh": "ZH",
        "ru": "RU",
        "fr": "FR",
        "es": "ES",
        "de": "DE",
        "pt": "PT",
        "it": "IT",
        "nl": "NL",
        "pl": "PL"
    }
    
    # 최종 대체 언어 (알 수 없는 언어일 경우)
    FALLBACK_LANG = "en"
    
    # 환경 설정에서 언어 설정 가져오기
    if source_lang is None:
        auto_detect = get_setting("AUTO_DETECT_LANG") or False
        if auto_detect:
            # 제한된 자동 감지인지 확인
            use_limited = get_setting("USE_LIMITED_AUTO_DETECT") or True
            if use_limited:
                source_lang = None
                print(f"[🔍 DeepL 제한된 언어 자동 감지 사용] 대상 언어: {', '.join(LIMITED_LANGS)}")
            else:
                source_lang = None
                print(f"[🔍 DeepL 모든 언어 자동 감지 사용]")
        else:
            source_lang = get_setting("SOURCE_LANG")
            print(f"[🔍 DeepL 소스 언어]: {source_lang}")
    else:
        if source_lang == "auto":
            source_lang = None
            print(f"[🔍 DeepL 언어 자동 감지 사용]")
        else:
            print(f"[🔍 DeepL 소스 언어 (수동 지정)]: {source_lang}")
    
    target_lang = get_setting("TARGET_LANG")
    
    # DeepL API 형식에 맞게 언어 코드 변환
    deepl_target = DEEPL_LANGS.get(target_lang, "EN")
    deepl_source = None if source_lang is None else DEEPL_LANGS.get(source_lang, "EN")
    
    # 같은 언어면 번역 스킵
    if deepl_source and deepl_source == deepl_target:
        print(f"[🔍 DeepL 번역 스킵] 소스와 타겟이 동일: {deepl_source}")
        return text
    
    print(f"[🔍 DeepL 타겟 언어]: {deepl_target}")
    
    # DeepL API 요청 URL 및 헤더
    url = "https://api-free.deepl.com/v2/translate"
    headers = {
        "Authorization": f"DeepL-Auth-Key {api_key}",
        "Content-Type": "application/json"
    }
    
    # API 요청 데이터 준비
    data = {
        "text": [text],
        "target_lang": deepl_target
    }
    
    # source_lang가 None이 아닌 경우에만 추가 (자동 감지인 경우 제외)
    if deepl_source:
        data["source_lang"] = deepl_source
    
    # 디버그 로그 추가
    print(f"[🔍 DeepL API 요청 준비] 대상 언어: {deepl_target}, 소스 언어: {'자동 감지' if deepl_source is None else deepl_source}")
    
    # DeepL API 호출
    try:
        print(f"[🔍 DeepL API 요청 중...]")
        response = requests.post(url, headers=headers, json=data)
        print(f"[🔍 DeepL API 응답 상태 코드]: {response.status_code}")
        
        # 응답 코드 확인
        if response.status_code != 200:
            print(f"[⚠️ DeepL API 오류]: {response.text}")
            return f"(DeepL 번역 실패: HTTP {response.status_code})"
        
        # 응답 처리
        result = response.json()
        translations = result.get("translations", [])
        
        if translations:
            translated_text = translations[0].get("text", "")
            detected_lang = translations[0].get("detected_source_language", "")
            
            # 자동 감지된 언어 확인 및 제한된 언어 목록 체크
            if deepl_source is None:
                print(f"[🔍 DeepL 감지된 언어]: {detected_lang}")
                
                # 제한된 자동 감지 모드인 경우
                use_limited = get_setting("USE_LIMITED_AUTO_DETECT", True)
                if use_limited:
                    # 언어 코드 정규화 (수정된 부분)
                    detected_lower = normalize_lang_code(detected_lang)
                    
                    # 제한 목록의 언어 코드도 정규화하여 비교
                    normalized_limited_langs = [normalize_lang_code(lang) for lang in LIMITED_LANGS]
                    
                    # 감지된 언어가 제한 목록에 없는 경우
                    if detected_lower not in normalized_limited_langs:
                        print(f"[⚠️ 감지된 언어({detected_lang})가 제한 목록에 없습니다. 영어로 재시도합니다.]")
                        # 영어로 가정하고 다시 번역
                        return deepl_translate(text, source_lang=FALLBACK_LANG)
            
            # 번역된 텍스트 길이에 따라 사용량 증가
            increment_deepl_usage(len(text))
            print(f"[✅ DeepL 번역 완료] 결과 길이: {len(translated_text)}자")
            
            return translated_text
        else:
            print(f"[⚠️ DeepL 번역 결과 없음]")
            return "(DeepL 번역 결과 없음)"
    except Exception as e:
        print(f"[⚠️ DeepL 예외] {e}")
        return f"(DeepL 번역 실패: {str(e)})"

# DeepL API용 언어 코드 변환 함수 (필요한 경우 참조용)
def convert_deepl_lang_code(lang_code):
    # DeepL API의 언어 코드 형식으로 변환
    mapping = {
        "ko": "KO",
        "en": "EN",
        "ja": "JA",
        "zh-CN": "ZH",
        "zh-TW": "ZH",
        "zh": "ZH",
        "es": "ES",
        "fr": "FR",
        "de": "DE",
        "ru": "RU",
        "pt": "PT",
        "it": "IT",
        "nl": "NL",
        "pl": "PL"
    }
    
    return mapping.get(lang_code, "EN")  # 기본값은 영어