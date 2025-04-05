# test_imports.py
import easyocr
import torch
import numpy as np
from PIL import Image
import socketio
import flask
import flask_socketio

print("모든 모듈이 성공적으로 가져와졌습니다!")

# 간단한 EasyOCR 테스트
reader = easyocr.Reader(['en'], gpu=False)
print("EasyOCR 리더가 성공적으로 초기화되었습니다!")