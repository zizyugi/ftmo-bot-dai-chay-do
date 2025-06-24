# FTMO Bot - Dai Chay Do (Breakout + Momentum + Retest H4)

import time
import requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# ===============================
# CONFIG
# ===============================
ASSET_LIST = ['XAUUSD', 'BTCUSD', 'ETHUSD', 'EURUSD', 'DJI', 'SPX500']
ACCOUNT_SIZE = 10000
RISK_PCT = 0.005
PUSHOVER_TOKEN = "aqscvtti9k5txuk9gncqz3bniyfbwr"
PUSHOVER_USER = "ukk76ch7a2piuz6ova5i2gffqj8uh1"
API_BASE_URL = "https://api.twelvedata.com/time_series"
API_KEY = "YOUR_TWELVE_DATA_API_KEY"

# ===============================
# Data Fetching
# ===============================
def fetch_candle_data(symbol, interval='1day', lookback_days=120):
    try:
        url = f"{API_BASE_URL}?symbol={symbol}&interval={interval}&outputsize={lookback_days}&apikey={API_KEY}&format=JSON"
        res = requests.get(url)
        data = res.json()
        if 'values' not in data:
            print(f"Khong co du lieu cho {symbol}: {data.get('message', 'Unknown error')}")
            return None
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        df = df.astype(float)
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close"})
        df = df[['Open', 'High', 'Low', 'Close']].sort_index()
        return df
    except Exception as e:
        print(f"Loi tai du lieu {symbol}: {e}")
        return None

# ===============================
# Signal Detection (Manual SMA)
# ===============================
def simple_moving_average(series, window):
    return series.rolling(window=window).mean()

def detect_breakout_signal(df):
    close = df['Close']
    ma50 = simple_moving_average(close, 50)
    ma200 = simple_moving_average(close, 200)

    recent_highs = df['High'][-21:-1]
    is_breakout = close.iloc[-1] > recent_highs.max()
    strong_momentum = (close.iloc[-1] > ma50.iloc[-1]) and (ma50.iloc[-1] > ma200.iloc[-1])

    if is_breakout and strong_momentum:
        return {
            'breakout_price': close.iloc[-1],
            'breakout_date': df.index[-1].strftime('%Y-%m-%d')
        }
    return None

# ===============================
# Entry Calculation
# ===============================
def calculate_trade_parameters(df, signal, symbol):
    atr = (df['High'] - df['Low']).rolling(window=14).mean()
    atr_value = atr.iloc[-1]

    entry = signal['breakout_price']
    sl = entry - 1.5 * atr_value
    tp = entry + 3.0 * atr_value

    risk_usd = ACCOUNT_SIZE * RISK_PCT
    stop_loss_pips = abs(entry - sl)
    volume = round(risk_usd / stop_loss_pips, 2)

    return {
        'symbol': symbol,
        'entry': round(entry, 2),
        'sl': round(sl, 2),
        'tp': round(tp, 2),
        'volume': volume,
        'risk_usd': round(risk_usd, 2),
        'date': signal['breakout_date']
    }

# ===============================
# Notifications
# ===============================
def send_signal_notification(symbol, trade_info):
    message = (
        f"✅ TIN HIEU BREAKOUT - {symbol}\n"
        f"Ngay: {trade_info['date']}\n"
        f"Entry: {trade_info['entry']} | SL: {trade_info['sl']} | TP: {trade_info['tp']}\n"
        f"Volume: {trade_info['volume']} lot | Risk: {trade_info['risk_usd']} USD"
    )
    try:
        response = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "message": message
        })
        print("Phản hồi Pushover:", response.status_code, response.text)
    except Exception as e:
        print(f"Loi khi gui tin nhan Pushover: {e}")

# ===============================
# Logging Placeholder
# ===============================
def log_trade(symbol, trade_info):
    print(f"[LOG] {symbol} | Entry: {trade_info['entry']} | SL: {trade_info['sl']} | TP: {trade_info['tp']} | Volume: {trade_info['volume']} | Risk: {trade_info['risk_usd']} | Ngay: {trade_info['date']}")

# ===============================
# Test Pushover Notification
# ===============================
def send_test_signal():
    test_trade_info = {
        'symbol': 'TEST_SIGNAL',
        'entry': 2000.0,
        'sl': 1980.0,
        'tp': 2040.0,
        'volume': 0.15,
        'risk_usd': 50.0,
        'date': datetime.now().strftime("%Y-%m-%d")
    }
    send_signal_notification('TEST_SIGNAL', test_trade_info)
    print("✅ Đã gửi test signal Pushover.")

# ===============================
# Main Bot Loop
# ===============================
def daily_bot_run():
    for symbol in ASSET_LIST:
        df = fetch_candle_data(symbol, interval='1day', lookback_days=120)
        if df is None or len(df) < 60:
            continue

        signal = detect_breakout_signal(df)
        if signal:
            trade_info = calculate_trade_parameters(df, signal, symbol)
            send_signal_notification(symbol, trade_info)
            log_trade(symbol, trade_info)

if __name__ == "__main__":
    send_test_signal()
    print("Bot Dai Chay Do dang chay...")
    while True:
        now = datetime.now()
        in_time_range = (now.hour >= 19 or now.hour < 2)
        if in_time_range and now.minute % 10 == 0:
            daily_bot_run()
            time.sleep(60)
        time.sleep(10)
