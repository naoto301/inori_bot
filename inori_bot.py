from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import csv
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 環境変数からキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# CSV読み込み（グローバル変数に一括読み込み）
story_data = {}

with open("彼女は祈りを忘れた_全20話_完全版.csv", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader)  # ヘッダーをスキップ
    for row in reader:
        episode = row[0].replace("彼女は祈りを忘れた ", "").replace("第", "").replace("話", "")  # 3 のように変換
        story_data[episode] = row[1:6]  # 吹き出し1〜5

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
    match = re.search(r'(\d{1,2})', text)
    
    if match:
        story_number = match.group(1)
        if story_number in story_data:
            messages = [TextSendMessage(text=msg) for msg in story_data[story_number]]
            line_bot_api.reply_message(event.reply_token, messages)
            return

    # 条件に合わない場合のデフォルト返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="『3』のように数字で話数を送ってください。")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
