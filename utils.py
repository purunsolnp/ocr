import os
import sys

def resource_path(relative_path):
    """모든 리소스 파일의 절대 경로 획득 (개발 환경과 PyInstaller 모두 지원)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)