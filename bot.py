import time
import requests
import pandas as pd
from datetime import datetime

# ================== CONFIGURACIÓN OANDA ==================
OANDA_TOKEN = "02c790a6ba72c96467d0bd90879f3142-e14a1d565813fe0590975823cc4de639"
OANDA_ACCOUNT_ID = "101-00128073586-001"   # Si falla, prueba con 101-001-28073586-001
OANDA_URL = "https://api-fxpractice.oanda.com/v3"

TELEGRAM_TOKEN = "8786067561:AAGWwwBYBJrobcDhxPGvpVsQ3_hNED8W2eo"
CHAT_ID = "5876887399"

INSTRUMENT = "XAU_USD"
GRANULARITY = "M5"          # 5 minutos
CHECK_INTERVAL = 10         # segundos

last_signal_time = None

headers = {
    "Authorization": f"Bearer {OANDA_TOKEN}",
    "Content-Type": "application/json"
}

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

def get_candles():
    url = f"{OANDA_URL}/instruments/{INSTRUMENT}/candles"
    params = {
        "granularity": GRANULARITY,
        "count": 10,
        "price": "M"          # Mid prices
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code != 200:
            print(f"Error OANDA: {response.status_code} - {response.text}")
            return None
        
        data = response.json()
        candles = data.get("candles", [])
        
        rows = []
        for c in candles:
            if c["complete"]:
                mid = c["mid"]
                rows.append({
                    "time": c["time"],
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"])
                })
        
        df = pd.DataFrame(rows)
        return df
    except Exception as e:
        print(f"Error obteniendo velas: {e}")
        return None

def is_bearish_engulfing_strong(df):
    if len(df) < 2:
        return False

    prev = df.iloc[-2]
    curr = df.iloc[-1]

    prev_bullish = prev["close"] > prev["open"]
    curr_bearish = curr["close"] < curr["open"]
    engulf_body = (curr["open"] >= prev["close"]) and (curr["close"] <= prev["open"])
    break_low = curr["close"] < prev["low"]

    return prev_bullish and curr_bearish and engulf_body and break_low

def main():
    global last_signal_time
    print("Bot iniciado - OANDA XAU_USD 5m - Velas envolventes bajistas fuertes...")
    send_telegram("🟢 <b>Bot OANDA activado</b>\nInstrumento: XAU_USD\nTimeframe: 5 minutos\nFuente: OANDA Practice")

    while True:
        try:
            df = get_candles()
            if df is not None and len(df) >= 2 and is_bearish_engulfing_strong(df):
                curr = df.iloc[-1]
                signal_time = curr["time"]

                if last_signal_time != signal_time:
                    price = round(curr["close"], 2)
                    message = (
                        f"🔴 <b>SEÑAL VELA ENVOLVENTE BAJISTA FUERTE</b>\n\n"
                        f"Par: XAU_USD (OANDA)\n"
                        f"Timeframe: 5 minutos\n"
                        f"Precio: <b>{price}</b>\n"
                        f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                        f"La vela envolvió y cerró por debajo de la mecha de la vela anterior."
                    )
                    send_telegram(message)
                    print(f"Señal enviada - Precio: {price}")
                    last_signal_time = signal_time

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"Error general: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
