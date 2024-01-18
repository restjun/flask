from flask import Flask, render_template
import requests
import schedule
import time

app = Flask(__name__)

def get_top_30_tickers():
    url = "https://api.upbit.com/v1/market/all"
    params = {"isDetails": "false"}
    headers = {"accept": "application/json"}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    # 거래대금이 높은 상위 30개 코인을 추출
    top_30_tickers = sorted(data, key=lambda x: x.get("acc_trade_price_24h", 0), reverse=True)[:30]

    return top_30_tickers

def print_top_30_tickers():
    # 상위 30개 코인 정보를 얻어옴
    top_30_tickers = get_top_30_tickers()

    # 로그에 거래대금 순위 상위 30개 코인 정보 출력
    print("거래대금 순위 상위 30개 코인:")
    for ticker in top_30_tickers:
        print(ticker["market"])

# 초기에 한번 실행
print_top_30_tickers()

# 15분마다 실행되도록 스케줄 설정
schedule.every(15).minutes.do(print_top_30_tickers)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(1)
    app.run(debug=False)
