import requests

# papago.txt에서 키 읽기
with open("papago.txt", encoding="utf-8") as f:
    cid, secret = f.read().strip().split("|")

text = "こんにちは、元気ですか？"
source = "ja"
target = "ko"

headers = {
    "X-Naver-Client-Id": cid,
    "X-Naver-Client-Secret": secret,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

data = {
    "source": source,
    "target": target,
    "text": text
}

res = requests.post("https://openapi.naver.com/v1/papago/n2mt", headers=headers, data=data)

print("응답 코드:", res.status_code)
print("결과:", res.text)
