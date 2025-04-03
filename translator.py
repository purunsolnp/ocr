# translator.py - 제한된 언어 자동 감지 기능 추가
import os
import json
import requests
from config import get_setting, increment_token_usage
from translator_nhn import nhn_translate
from translator_deepl import deepl_translate

def load_openai_key():
    try:
        with open("openai.txt", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"[⚠️ OpenAI API 키 로드 오류]: {e}")
        return ""

def gpt_translate(text):
    # 빈 텍스트는 번역하지 않음
    if not text:
        return ""
        
    api_key = load_openai_key()
    if not api_key:
        print(f"[⚠️ OpenAI API 키가 설정되지 않았습니다]")
        return "(OpenAI API 키가 설정되지 않았습니다)"
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # 제한된 자동 감지 지원 언어
    LIMITED_LANGS = get_setting("LIMITED_AUTO_DETECT_LANGS", ["ko", "ja", "en", "zh-CN", "ru", "fr"])
    # 최종 대체 언어 (알 수 없는 언어일 경우)
    FALLBACK_LANG = "en"

    # 자동 감지 모드 확인
    auto_detect = get_setting("AUTO_DETECT_LANG") or False
    source = get_setting("SOURCE_LANG") or "en"
    target = get_setting("TARGET_LANG") or "ko"
    
    # 자동 감지 모드인 경우의 프롬프트
    if auto_detect:
        # 제한된 자동 감지인지 확인
        use_limited = get_setting("USE_LIMITED_AUTO_DETECT", True)
        if use_limited:
            prompt = (f"Translate the following text to {target}. "
                      f"Detect the source language, but only consider these languages: "
                      f"{', '.join(LIMITED_LANGS)}. "
                      f"If the text doesn't match any of these languages, assume it's {FALLBACK_LANG}.\n\n{text}")
            print(f"[🔍 GPT 제한된 언어 자동 감지 모드] 대상 언어: {', '.join(LIMITED_LANGS)}")
        else:
            prompt = f"Translate the following text to {target}. Detect the source language automatically:\n\n{text}"
            print(f"[🔍 GPT 모든 언어 자동 감지 모드]")
    else:
        prompt = f"Translate the following text from {source} to {target}:\n\n{text}"
        print(f"[🔍 GPT 번역] 원본 언어: {source}, 목표 언어: {target}")

    body = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        print(f"[🔍 GPT API 요청 중...]")
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
        
        print(f"[🔍 GPT API 응답 상태 코드]: {res.status_code}")
        
        if res.status_code != 200:
            print(f"[⚠️ GPT API 오류]: {res.text}")
            return f"(GPT 번역 실패: HTTP {res.status_code})"
            
        data = res.json()
        result = data["choices"][0]["message"]["content"].strip()

        usage = data.get("usage", {}).get("total_tokens", 0)
        increment_token_usage(usage)
        
        print(f"[✅ GPT 번역 완료] 토큰 사용량: {usage}")

        return result
    except Exception as e:
        print(f"[⚠️ GPT 예외] {e}")
        return f"(GPT 번역 실패: {str(e)})"

# 공용 번역 함수
def translate_text(text):
    if not text:
        return ""
        
    engine = get_setting("ENGINE")
    print(f"[🔍 번역 시작] 엔진: {engine}, 텍스트 길이: {len(text)}자")

    # 자동 감지 모드 상태 로깅
    if get_setting("AUTO_DETECT_LANG", False):
        use_limited = get_setting("USE_LIMITED_AUTO_DETECT", True)
        if use_limited:
            langs = ", ".join(get_setting("LIMITED_AUTO_DETECT_LANGS", ["ko", "ja", "en", "zh-CN", "ru", "fr"]))
            print(f"[🔍 제한된 언어 자동 감지 활성화됨] 대상 언어: {langs}")
        else:
            print(f"[🔍 모든 언어 자동 감지 활성화됨]")
    
    if engine == "papago-nhn":
        return nhn_translate(text)
    elif engine == "deepl":
        return deepl_translate(text)
    else:
        return gpt_translate(text)