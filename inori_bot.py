from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import json
import re
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# GASエンドポイント
GAS_URL = "https://script.google.com/macros/s/AKfycbwoZzyGUYV1bT2cIJDIwAHj7srg7GjbM4ifZXS1Ds3z4p6koJIsv0AB4V7ApLDos7dOXg/exec"

# JSONファイルからストーリー読み込み
with open("line_novel_bot_episode_data_FULL_1to20.json", encoding="utf-8") as f:
    story_data = json.load(f)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

def is_premium_user(user_id):
    try:
        response = requests.get(GAS_URL, params={"user_id": user_id})
        return response.json().get("exists", False)
    except:
        return False

def register_premium_user(user_id):
    try:
        requests.post(GAS_URL, json={"user_id": user_id})
    except:
        pass

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    if text == "inori_2025_unlock":
        register_premium_user(user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ プレミアム解放完了しました。\n第6話以降が読めるようになります。")
        )
        return

    match = re.search(r'(\d{1,2})', text)
    if match:
        story_number = match.group(1)
        if story_number in story_data:
            if int(story_number) > 5 and not is_premium_user(user_id):
                pay_message = TextSendMessage(
                    text="🔒 第6話以降はプレミアム限定です。\n\nhttps://note.com/loyal_cosmos1726/n/n02affd979258"
                )
                line_bot_api.reply_message(event.reply_token, pay_message)
                return

            messages = [TextSendMessage(text=msg) for msg in story_data[story_number]]
            line_bot_api.reply_message(event.reply_token, messages)
            return

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="『3』のように数字で話数を送ってください。")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
