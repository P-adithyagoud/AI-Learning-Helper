import requests
import json
url = "http://127.0.0.1:8000/generate-plan"
data = {
  "skill": "python",
  "level": "Beginner",
  "daily_hours": "2"
}
try:
    resp = requests.post(url, json=data, timeout=30)
    print("Status:", resp.status_code)
    print("Headers:", resp.headers)
    print("Body:", resp.text)
except Exception as e:
    print("Exception:", e)
