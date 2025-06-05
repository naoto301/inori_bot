from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import csv
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

# JSON形式のストーリーデータを読み込み
with open("line_novel_bot_episode_data_FULL_1to20.json", encoding="utf-8") as f:
    story_data = json.load(f)

# プレミアムユーザー記録ファイルのパス
PREMIUM_FILE = "premium_users.json"

# 初期ロード（ファイルがなければ空リスト）
if os.path.exists(PREMIUM_FILE):
    with open(PREMIUM_FILE, "r") as f:
        premium_users = json.load(f)
else:
    premium_users = []

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
    user_id = event.source.user_id
    match = re.search(r'(\d{1,2})', text)

    # ✅ プレミアム解除コード処理
    if text == "inori_2025_unlock":
        if user_id and user_id not in premium_users:
            premium_users.append(user_id)
            with open(PREMIUM_FILE, "w") as f:
                json.dump(premium_users, f)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ プレミアム登録が完了しました。第6話以降も解放されました。")
        )
        return

    # ✅ 話数の入力処理
    if match:
        story_number = match.group(1)
        key = f"第{int(story_number)}話"

        if key in story_data:
            story_num_int = int(story_number)

            if story_num_int <= 5:
                # 無料話（第1〜5話）
                messages = [TextSendMessage(text=msg) for msg in story_data[key]]
                line_bot_api.reply_message(event.reply_token, messages)
                return
            else:
                # 第6話以降 → プレミアム判定（user_idがNoneなら非プレミアム扱い）
                if user_id and user_id in premium_users:
                    messages = [TextSendMessage(text=msg) for msg in story_data[key]]
                    line_bot_api.reply_message(event.reply_token, messages)
                    return
                else:
                    pay_message = TextSendMessage(
                        text=(
                            "🔒 この話はプレミアム限定です。\n"
                            "解除するには、以下のnoteでコードを購入してください👇\n"
                            "https://note.com/loyal_cosmos1726/n/n02affd979258"
                        )
                    )
                    line_bot_api.reply_message(event.reply_token, pay_message)
                    return

    # 無効な入力
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="『3』のように数字で話数を送ってください（1〜20話）。")
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

