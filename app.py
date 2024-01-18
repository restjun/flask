from flask import Flask, render_template
import pyupbit
import telepot
import schedule
import time

app = Flask(__name__)

# 텔레그램 봇 설정
telegram_token = "6389499820:AAHCKStfe6P0FuUakX7xzEcBByaxwzD_dak"  # 텔레그램 봇 토큰
telegram_chat_id = "@6596886700"  # 텔레그램 채널 ID
telegram_bot = telepot.Bot(telegram_token)

def send_top_30_tickers():
    # Upbit에서 상위 30개 코인 가져오기
    tickers = pyupbit.get_tickers("KRW")
    top_30_tickers = tickers[:30]

    # 메세지 내용 생성
    message = "Top 30 Tickers:\n"
    for ticker in top_30_tickers:
        message += f"{ticker}\n"

    # 텔레그램으로 메세지 전송
    telegram_bot.sendMessage(chat_id=telegram_chat_id, text=message)

# 5분마다 send_top_30_tickers 함수 실행
schedule.every(5).minutes.do(send_top_30_tickers)

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    # Flask 
