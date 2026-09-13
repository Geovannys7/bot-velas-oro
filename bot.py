import time
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import pytz

# ================== CONFIGURACIÓN ==================
TELEGRAM_TOKEN = "8786067561:AAGWwwBYBJrobcDhxPGvpVsQ3_hNED8W2eo"
CHAT_ID = "5876887399"
SYMBOL = "GC=F"          # Oro
TIMEFRAME = "15m"
CHECK_INTERVAL = 60      # Revisar cada 60 segundos

last_signal_time = None

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Error enviando Telegram: {e}")

def get_data():
    ticker = yf.Ticker(SYMBOL)
    df = ticker.history(period="2d", interval=TIMEFRAME)
    if df.empty:
        return None
    df = df.reset_index()
    df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close"}, inplace=True)
    return df

def is_bearish_engulfing_strong(df):
    if len(df) < 3:
        return False

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    # Vela anterior alcista
    prev_bullish = prev["close"] > prev["open"]

    # Vela actual bajista
    curr_bearish = curr["close"] < curr["open"]

    # Envuelve el cuerpo
    engulf_body = (curr["open"] >= prev["close"]) and (curr["close"] <= prev["open"])

    # Cierra por debajo de la mecha inferior de la vela anterior
    break_low = curr["close"] < prev["low"]

    return prev_bullish and curr_bearish and engulf_body and break_low

def main():
    global last_signal_time
    print("Bot iniciado - Buscando velas envolventes bajistas fuertes en XAUUSD 15m...")
    send_telegram("🟢 <b>Bot de Velas Envolventes activado</b>\nTimeframe: 15 minutos\nMercado: Oro")

    while True:
        try:
            df = get_data()
            if df is not None and is_bearish_engulfing_strong(df):
                curr = df.iloc[-1]
                signal_time = str(curr.name) if hasattr(curr, 'name') else str(datetime.now())

                if last_signal_time != signal_time:
                    price = round(curr["close"], 2)
                    message = (
                        f"🔴 <b>SEÑAL VELA ENVOLVENTE BAJISTA FUERTE</b>\n\n"
                        f"Par: XAUUSD (Oro)\n"
                        f"Timeframe: 15 minutos\n"
                        f"Precio: <b>{price}</b>\n"
                        f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                        f"La vela envolvió y cerró por debajo de la mecha de la vela anterior."
                    )
                    send_telegram(message)
                    print(f"Señal enviada - Precio: {price}")
                    last_signal_time = signal_time

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
