import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

ZALO_OA_TOKEN = os.environ.get("ZALO_OA_TOKEN", "")
VERIFY_FILE_NAME = os.environ.get("ZALO_VERIFY_FILE", "zalo_verifier.html")
VERIFY_FILE_CONTENT = os.environ.get("ZALO_VERIFY_CONTENT", "")
IUH_DRL_URL = os.environ.get("IUH_DRL_URL", "https://sv.iuh.edu.vn")


def fetch_activities():
    try:
        resp = requests.get(IUH_DRL_URL, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for link in soup.select("a")[:5]:
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if title and len(title) > 15:
                items.append(f"- {title}\n  Link: {href}")
        if not items:
            return "Hiện chưa có hoạt động điểm rèn luyện mới được cập nhật."
        return "Danh sách hoạt động điểm rèn luyện mới:\n\n" + "\n\n".join(items)
    except Exception as e:
        return f"Không thể kết nối đến cổng thông tin trường lúc này: {e}"


def send_zalo_message(user_id, text):
    url = "https://openapi.zalo.me/v3.0/oa/message/cs"
    headers = {
        "Content-Type": "application/json",
        "access_token": ZALO_OA_TOKEN
    }
    payload = {
        "recipient": {"user_id": user_id},
        "message": {"text": text}
    }
    requests.post(url, json=payload, headers=headers, timeout=10)


@app.route(f"/{VERIFY_FILE_NAME}", methods=["GET"])
def verify_domain():
    return VERIFY_FILE_CONTENT, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return "Webhook is active", 200

    data = request.get_json(silent=True) or {}
    event_name = data.get("event_name")

    if event_name == "user_send_text":
        sender_id = data.get("sender", {}).get("id")
        message_text = data.get("message", {}).get("text", "").strip().lower()

        if message_text == "/sk" and sender_id:
            reply_text = fetch_activities()
            send_zalo_message(sender_id, reply_text)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)