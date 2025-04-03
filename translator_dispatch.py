from translator import translate_text as _translate_text

def translate_text(text):
    from config import get_setting
    
    # LibreTranslate 엔진 추가
    if get_setting("ENGINE") == "libretranslate":
        from translator_libre import libre_translate
        return libre_translate(text)
    else:
        return _translate_text(text)

def get_lang(lang_code):
    if lang_code.startswith("ja"):
        return ["ja", "en"]
    elif lang_code.startswith("zh"):
        return ["ch_sim", "en"]
    elif lang_code.startswith("ko"):
        return ["ko", "en"]
    else:
        return ["en"]