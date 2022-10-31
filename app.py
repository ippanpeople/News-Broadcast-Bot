from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerSendMessage
)

app = Flask(__name__)

line_bot_api = LineBotApi('BzInYuQWZ2KDpjYaRX+nGGk092AQ7UgWHkRx7IT8J8Xc7mbP6gxzDLgcLCuuePJW7FknCq6k/d8RHjxsLoviwUndZB2uzTOJgb6K/PBk3hKjBzSa4te7peTFaFTBmFg2KSFUZmv8o4I3dh2Tm2et3wdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('a842e0251982aac19ce2ffd563f28d3c')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 預設回覆與使用者相同訊息
    # line_bot_api.reply_message(
    #     event.reply_token,
    #     TextSendMessage(text=event.message.text))

    # 根據接收文字回傳特定訊息
    if event.message.text == '@info':
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text='hello'),
                StickerSendMessage(package_id='1', sticker_id='2')
            ]
        )
    else :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='何言ってんの？分がんないよ〜')
        )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
