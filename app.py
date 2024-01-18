from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
import pyupbit
import telepot
import schedule
import time
import uvicorn

app = FastAPI()
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# 모든 종목 코드 확인
all_tickers = pyupbit.get_tickers()

# KRW로 표기된 종목만 필터링
krw_tickers = [ticker for ticker in all_tickers if "KRW-" in ticker]

# 최근 조회한 골든크로스 결과를 저장할 변수
last_golden_cross_coins = []

# 텔레그램 봇 설정
telegram_token = "6389499820:AAHCKStfe6P0FuUakX7xzEcBByaxwzD_dak"  # 텔레그램 봇 토큰
telegram_chat_id = "@6596886700"  # 텔레그램 채널 ID
telegram_bot = telepot.Bot(telegram_token)


# 거래대금 상위 30개 코인 조회
def get_top_30_tickers():
    ticker_info = []

    for ticker in krw_tickers:
        orderbook = pyupbit.get_orderbook(tickers=ticker)
        if orderbook:
            trade_price = orderbook[0]['orderbook_units'][0]['ask_price']
            trade_volume = orderbook[0]['orderbook_units'][0]['ask_size']
            trade_amount = trade_price * trade_volume
            ticker_info.append({"ticker": ticker, "trade_amount": trade_amount})

    # 거래대금이 높은 순으로 정렬
    sorted_ticker_info = sorted(ticker_info, key=lambda x: x["trade_amount"], reverse=True)

    # 상위 30개 코인 반환
    return sorted_ticker_info[:30]


# 골든크로스 조회를 위한 함수
def get_golden_cross_coins():
    golden_cross_coins = []

    for ticker in krw_tickers:
        # API 요청을 통해 2400분 단위로 조회
        df = pyupbit.get_ohlcv(ticker, interval='minute15', count=2400)

        # 종가 (Close)의 120분 지수이동평균 계산
        df['EMA120'] = df['close'].ewm(span=120, adjust=False).mean()

        # 종가 (Close)의 240분 지수이동평균 계산
        df['EMA240'] = df['close'].ewm(span=240, adjust=False).mean()

        # 120선이 240선을 돌파하는 골든크로스 확인
        if df['EMA120'].iloc[-1] > df['EMA240'].iloc[-1] and df['EMA120'].iloc[-2] <= df['EMA240'].iloc[-2]:
            golden_cross_coins.append({"ticker": ticker, "cross_date": df.index[-1]})

    # 최근에 골든크로스가 나타난 순서로 정렬
    sorted_golden_cross_coins = sorted(golden_cross_coins, key=lambda x: x["cross_date"], reverse=True)

    return sorted_golden_cross_coins


# 주기적으로 백그라운드 태스크를 실행하는 함수
def update_golden_cross():
    global last_golden_cross_coins
    current_time = datetime.now()

    # 현재 시간과 최근 조회한 골든크로스 결과의 시간 차이가 15분 이상인 경우에만 조회
    if not last_golden_cross_coins or (current_time - last_golden_cross_coins[0]["cross_date"]).total_seconds() >= 900:
        # 골든크로스 결과 업데이트
        last_golden_cross_coins = get_golden_cross_coins()

        # 거래 대금이 높은 30개 코인 조회
        top_30_tickers = get_top_30_tickers()

        # 메시지 전송
        send_golden_cross_message(last_golden_cross_coins, top_30_tickers)


# 텔레그램으로 메시지 전송하는 함수
def send_golden_cross_message(golden_cross_coins, top_30_tickers):
    message = "\n골든크로스가 나타난 코인들:\n"
    for coin in golden_cross_coins:
        message += f"{coin['ticker']} - 최근 골든크로스 일자: {coin['cross_date']}\n"

    message += "\n거래 대금이 높은 상위 30개 코인:\n"
    for ticker_info in top_30_tickers:
        message += f"{ticker_info['ticker']} - 거래 대금: {ticker_info['trade_amount']}\n"

    telegram_bot.sendMessage(chat_id=telegram_chat_id, text=message)


# 주기적으로 골든크로스 업데이트 실행
schedule.every(15).minutes.do(update_golden_cross)

while True:
    schedule.run_pending()
    time.sleep(1)

