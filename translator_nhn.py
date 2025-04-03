import json
import requests
import re
from config import get_setting, increment_nhn_papago_usage

def load_nhn_keys():
    try:
        with open("papago_nhn.txt", encoding="utf-8") as f:
            access_key, secret_key = f.read().strip().split("|")
            return access_key, secret_key
    except Exception as e:
        print(f"[⚠️ NHN Papago API 키 로드 오류]: {e}")
        return "", ""

def is_meaningful_text(text):
    """
    텍스트가 의미 있는지 확인하는 함수
    - 특수문자 비율이 높으면 의미 없는 텍스트로 간주
    - 한글, 일본어, 중국어, 영어 등 의미 있는 언어 패턴이 있는지 확인
    """
    if not text or len(text.strip()) == 0:
        return False
        
    # 1. 특수문자 비율 계산
    special_chars = sum(1 for c in text if not (c.isalnum() or c.isspace() or c in '.,;:!?()-"\''))
    total_chars = len(text)
    special_ratio = special_chars / total_chars if total_chars > 0 else 0
    
    threshold = get_setting("SPECIAL_CHAR_THRESHOLD", 0.3)
    
    # 2. 언어 패턴 확인 (최소한의 한글, 일본어, 중국어, 영어 패턴)
    has_korean = bool(re.search(r'[가-힣]', text))
    has_japanese = bool(re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]', text))
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
    has_english = bool(re.search(r'[a-zA-Z]{3,}', text))  # 최소 3자 이상의 영어 단어
    
    # 패턴이 감지되면 의미 있는 텍스트로 간주
    if has_korean or has_japanese or has_chinese or has_english:
        return True
    
    # 특수문자 비율이 임계값 이상이면 의미 없는 텍스트
    if special_ratio > threshold:
        print(f"[⚠️ 특수문자 비율({special_ratio:.1%})이 임계값({threshold:.1%})을 초과하여 의미 없는 텍스트로 판단]")
        return False
    
    return True

def nhn_translate(text, source_lang=None):
    # 빈 텍스트는 번역하지 않음
    if not text:
        return ""
    
    # NHN API 키 가져오기
    access_key, secret_key = load_nhn_keys()
    if not access_key or not secret_key:
        print(f"[⚠️ NHN API 키가 설정되지 않았습니다]")
        return "(NHN API 키가 설정되지 않았습니다)"
    
    print(f"[🔍 NHN Papago API 키 확인] Client ID: {access_key[:4]}... (일부만 표시)")

    # 지원되는 언어 매핑
    LANGS = {
        "en": "en", "ko": "ko", "ja": "ja",
        "zh": "zh-CN", "zh-CN": "zh-CN", "zh-TW": "zh-TW",
        "es": "es", "de": "de", "ru": "ru", "fr": "fr",
        "pt": "pt", "th": "th", "vi": "vi", "id": "id",
        "auto": "auto"  # 자동 감지 추가
    }
    
    # 제한된 자동 감지 지원 언어
    LIMITED_LANGS = get_setting("LIMITED_AUTO_DETECT_LANGS") or ["ko", "ja", "en", "zh-CN", "zh", "ru", "fr"]
    FALLBACK_LANG = "en"
    skip_meaningless = get_setting("SKIP_MEANINGLESS_TEXT") or True
        
    # 의미 없는 텍스트 확인
    if skip_meaningless and not is_meaningful_text(text):
        print(f"[⚠️ 의미 없는 텍스트로 판단되어 번역을 건너뜁니다]")
        return text
    
    # 소스 언어 설정
    if source_lang is None:
        # 자동 감지 모드 확인
        auto_detect = get_setting("AUTO_DETECT_LANG") or False
        if auto_detect:
            use_limited = get_setting("USE_LIMITED_AUTO_DETECT") or True
            if use_limited:
                source = "auto"
                print(f"[🔍 NHN Papago 제한된 언어 자동 감지 사용] 대상 언어: {', '.join(LIMITED_LANGS)}")
            else:
                source = "auto"
                print(f"[🔍 NHN Papago 모든 언어 자동 감지 사용]")
        else:
            source = LANGS.get(get_setting("SOURCE_LANG"), "en")
            print(f"[🔍 NHN Papago 소스 언어]: {source}")
    else:
        source = LANGS.get(source_lang, "en")
        if source_lang == "auto":
            print(f"[🔍 NHN Papago 언어 자동 감지 사용]")
        else:
            print(f"[🔍 NHN Papago 소스 언어 (수동 지정)]: {source}")
    
    # 타겟 언어 설정
    target = LANGS.get(get_setting("TARGET_LANG"), "ko")
    print(f"[🔍 NHN Papago 타겟 언어]: {target}")
    
    # 같은 언어면 번역 스킵
    if source != "auto" and source == target:
        print(f"[🔍 NHN Papago 번역 스킵] 소스와 타겟이 동일: {source}")
        return text

    url = "https://naveropenapi.apigw.ntruss.com/nmt/v1/translation"
    headers = {
        "Content-Type": "application/json",
        "X-NCP-APIGW-API-KEY-ID": access_key,
        "X-NCP-APIGW-API-KEY": secret_key
    }
    
    print(f"[🔍 NHN Papago API 헤더 설정 완료]")

    body = {
        "source": source,
        "target": target,
        "text": text
    }
    
    print(f"[🔍 NHN Papago API 요청] Source: {source}, Target: {target}, Text 길이: {len(text)}자")

    try:
        print(f"[🔍 NHN Papago API 호출 시작]")
        
        res = requests.post(url, headers=headers, data=json.dumps(body))
        
        print(f"[🔍 NHN Papago API 응답 상태 코드]: {res.status_code}")
        
        if res.status_code != 200:
            print(f"[⚠️ NHN Papago API 오류]: {res.text}")
            return f"(NHN Papago 번역 실패: HTTP {res.status_code})"
        
        result_json = res.json()
        
        # 응답 구조 확인
        if "message" in result_json and "result" in result_json["message"]:
            # 자동 감지 모드에서 감지된 언어 확인
            detected_lang = None
            if source == "auto" and "srcLangType" in result_json["message"]["result"]:
                detected_lang = result_json["message"]["result"]["srcLangType"]
                print(f"[🔍 NHN Papago 감지된 언어]: {detected_lang}")
                
                # 제한된 언어 자동 감지 모드인 경우 확인
                use_limited = get_setting("USE_LIMITED_AUTO_DETECT", True)
                if use_limited:
                    # 언어 코드 비교 (대소문자 무시)
                    detected_lower = detected_lang.lower()
                    
                    # zh 계열 언어 통합 처리 (zh, zh-cn, zh-tw 등)
                    if detected_lower.startswith('zh'):
                        detected_lower = 'zh-cn'
                    
                    # 언어 코드 매칭 (대소문자 및 하이픈 무시)
                    matched_lang = False
                    for lang in LIMITED_LANGS:
                        if lang.lower().replace('-', '') == detected_lower.replace('-', ''):
                            matched_lang = True
                            break
                    
                    if not matched_lang:
                        print(f"[⚠️ 감지된 언어({detected_lang})가 제한 목록에 없습니다. 영어로 재시도합니다.]")
                        
                        # 의미 없는 텍스트 추가 확인
                        if skip_meaningless and not is_meaningful_text(text):
                            print(f"[⚠️ 지원되지 않는 언어이며 의미 없는 텍스트로 판단됨. 번역 건너뜀]")
                            return text
                        
                        # 영어로 가정하고 다시 번역 시도
                        return nhn_translate(text, source_lang=FALLBACK_LANG)
            
            # 번역 결과 추출
            result = result_json["message"]["result"]["translatedText"]
            
            # 결과가 원본과 동일하고 원본 언어가 자동 감지였다면 의미 없는 텍스트로 간주
            if result == text and source == "auto":
                print(f"[⚠️ 번역 결과가 원본과 동일합니다. 의미 없는 텍스트로 간주하여 처리를 중단합니다.]")
                return text
            
            increment_nhn_papago_usage(len(text))
            print(f"[✅ NHN Papago 번역 완료] 결과 길이: {len(result)}자")
            
            return result
        else:
            print(f"[⚠️ NHN Papago 응답 형식 오류]: {result_json}")
            return "(NHN Papago 응답 형식 오류)"
            
    except Exception as e:
        print(f"[⚠️ NHN Papago 예외 발생]: {e}")
        return f"(NHN Papago 번역 실패: {str(e)})"