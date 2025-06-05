from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 環境変数からキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# JSON読み込み（第1話〜第20話）
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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    match = re.search(r'(\d{1,2})', text)  # 「3」などの数字抽出

    if match:
        story_number = match.group(1)
        key = f"第{story_number}話"
        if key in story_data:
            # 吹き出し5個（[0]=サブタイトル, [1]〜[4]が本文）
            episode = story_data[key]
            messages = [TextSendMessage(text=ep) for ep in episode]
            line_bot_api.reply_message(event.reply_token, messages)
            return

    # 話数指定が不正 or 存在しない
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="『3』のように数字で話数を送ってください（1〜20話対応）。")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
