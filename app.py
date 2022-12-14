from flask import Flask, request, abort, redirect, session, url_for, render_template, flash
from flask_login import LoginManager, current_user, login_user
from flask.json import jsonify

from line_bot import *

from apscheduler.schedulers.background import BackgroundScheduler

from requests_oauthlib import OAuth2Session
from database import init_db, db_session
from models import User
from forms import SubscriptionForm

from jobs import news_scraper

# This information is obtained upon registration of a new GitHub
client_id = "1657607783"
client_secret = "1437c2fc73ecc30def7400bbc8af76ce"
authorization_base_url = 'https://access.line.me/oauth2/v2.1/authorize'
token_url = 'https://api.line.me/oauth2/v2.1/token'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thesecretkey'

login_manager = LoginManager(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# login
def get_redirect_url():
    return url_for(
        '.oauth_callback',
        _external=True,
        _scheme='https'
    )
# 在收到第一個請求後執行db的初始化
@app.before_first_request
def init():    
    init_db()
# 在每個請求後或是server關閉後關閉db
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route("/login")
def login():
    line_login = OAuth2Session(
        client_id, 
        redirect_uri=get_redirect_url(),
        scope='profile openid'
    )
    authorization_url, state = line_login.authorization_url(authorization_base_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/oauth_callback")
def oauth_callback():
    line_login = OAuth2Session(client_id, state=session['oauth_state'], redirect_uri=get_redirect_url())
    token = line_login.fetch_token(
        token_url, 
        client_secret=client_secret,
        authorization_response=request.url.replace('http', 'https')
    )

    user_data = line_login.get('https://api.line.me/v2/profile').json()

    user = User.query.filter_by(social_id=user_data.get('userId')).first()

    if not user:
        user = User(
            social_id=user_data.get('userId'),
            name=user_data.get('displayName'),
            profile_image_url=user_data.get('pictureUrl')
        )

        db_session.add(user)
        db_session.commit()
    login_user(user)
    return redirect(url_for('subscription'))

@app.route("/subscription", methods=['GET', 'POST'])
def subscription():
    if current_user.is_anonymous:
        return redirect(url_for('login'))
    
    form = SubscriptionForm(opj=current_user)
    if request.method == 'POST':
        form.populate_obj(current_user)
        db_session.add(current_user)
        db_session.commit()
        flash('Save Successfully!!')

    return render_template('subscription.html', form=form, user=current_user)

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

@handler.add(UnfollowEvent)
def handle_unfollow(event):
    user = User.query.filter(User.social_id == event.source.user_id).first()
    if user:
        user.is_blocked = True
        db_session.commit()

@handler.add(FollowEvent)
def handle_follow(event):
    user = User.query.filter(User.social_id == event.source.user_id).first()
    if user:
        user.is_blocked = False
        db_session.commit()


if __name__ == "__main__":
    sched = BackgroundScheduler()
    sched.add_job(news_scraper, 'interval', seconds=600)
    # sched.add_job(news_scraper, 'cron', hour='8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21')
    sched.start()
    app.run(host='0.0.0.0', port=5001, debug=True)
