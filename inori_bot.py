import json
import os

PREMIUM_FILE = "premium_users.json"

# 初期ロード（存在しなければ空リスト）
if os.path.exists(PREMIUM_FILE):
    with open(PREMIUM_FILE, "r") as f:
        premium_users = json.load(f)
else:
    premium_users = []

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id
    match = re.search(r'(\d{1,2})', text)

    # ✅ プレミアム解除コード対応
    if text == "inori_2025_unlock":
        if user_id not in premium_users:
            premium_users.append(user_id)
            with open(PREMIUM_FILE, "w") as f:
                json.dump(premium_users, f)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="✅ プレミアム登録が完了しました。第6話以降も解放されました。")
        )
        return

    # ✅ 話数入力処理
    if match:
        story_number = match.group(1)
        key = f"第{story_number}話"

        if key in story_data:
            story_num_int = int(story_number)

            if story_num_int <= 5:
                # 無料話
                messages = [TextSendMessage(text=ep) for ep in story_data[key]]
                line_bot_api.reply_message(event.reply_token, messages)
                return
            else:
                # 第6話以降 → プレミアム判定
                if user_id in premium_users:
                    messages = [TextSendMessage(text=ep) for ep in story_data[key]]
                    line_bot_api.reply_message(event.reply_token, messages)
                    return
                else:
                    # 有料誘導
                    pay_message = TextSendMessage(
                        text="🔒 第6話以降はプレミアム限定です。\n解除するには、以下のnoteでコードを購入してください👇\nhttps://note.com/〇〇/n/xxxxxxxxxxxx"
                    )
                    line_bot_api.reply_message(event.reply_token, pay_message)
                    return

    # 無効メッセージ
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="『3』のように数字で話数を送ってください（1〜20話）。")
    )
