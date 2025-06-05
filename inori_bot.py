from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import json
import re
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)

# LINE Botのキー設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ストーリー読み込み
with open("line_novel_bot_episode_data_FULL_1to20.json", "r", encoding="utf-8") as f:
    story_data = json.load(f)

# プレミアムユーザー保存ファイル
PREMIUM_FILE = "premium_users.json"

# 初期化：ファイルがなければ作成
if not os.path.exists(PREMIUM_FILE):
    with open(PREMIUM_FILE, "w") as f:
        json.dump([], f)

with open(PREMIUM_FILE, "r") as f:
    premium_users = json.load(f)

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
    user_id = event.source.user_id or "UNKNOWN"

    print(f"[DEBUG] user_id = {user_id}")
    print(f"[DEBUG] premium_users = {premium_users}")

    # プレミアムコード処理
    if text == "inori_2025_unlock":
        if user_id != "UNKNOWN" and user_id not in premium_users:
            premium_users.append(user_id)
            with open(PREMIUM_FILE, "w") as f:
                json.dump(premium_users, f)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ プレミアム登録完了。第6話以降が読めます。")
        )
        return

    # 話数入力
    match = re.search(r'\d{1,2}', text)
    if match:
        story_number = int(match.group(0))
        key = f"第{story_number}話"

        if key in story_data:
            if story_number <= 5:
                messages = [TextSendMessage(text=msg) for msg in story_data[key]]
                line_bot_api.reply_message(event.reply_token, messages)
            elif user_id != "UNKNOWN" and user_id in premium_users:
                messages = [TextSendMessage(text=msg) for msg in story_data[key]]
                line_bot_api.reply_message(event.reply_token, messages)
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(
                    text="🔒この話はプレミアム限定です。\n解除コードはnoteから入手してください。\nhttps://note.com/〇〇/n/xxxxxxxxxxxx"
                ))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text="❌ その話数は存在しません（1〜20）。"
            ))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text="『3』のように数字で話数を送ってください（1〜20話対応）"
        ))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
