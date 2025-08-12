import os
import pandas as pd
from tinkoff.invest import Client, CandleInterval
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

# Настройки
TICKERS_FILE = os.getenv("TICKERS_FILE", "data/tickers.txt")
TOKEN_FILE = os.getenv("TOKEN_FILE", "token.txt")
SAVE_DIR = "SBERBANK_FUTURES"
INTERVALS = {
    "4_hour": CandleInterval.CANDLE_INTERVAL_4_HOUR
}

# Убедимся, что папка для сохранения существует
for folder in INTERVALS.keys():
    os.makedirs(os.path.join(SAVE_DIR, folder), exist_ok=True)

# Чтение тикеров из файла
def read_tickers(file_name):
    with open(file_name, "r") as f:
        return [line.strip() for line in f if line.strip()]

# Чтение токена из файла
def read_token(file_name):
    token = os.getenv("TINKOFF_TOKEN")
    if token:
        return token.strip()
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            return f.read().strip()
    raise FileNotFoundError("Provide TINKOFF_TOKEN in env or token.txt")

# Получение UID для тикера
def fetch_uid_for_ticker(client, ticker):
    instruments = client.instruments.find_instrument(query=ticker).instruments
    for instrument in instruments:
        try:
            print(f"UID: {instrument.uid}, Название: {instrument.name}, Тип: {instrument.instrument_type}")
            return instrument.uid
        except Exception as e:
            print(f"Ошибка получения данных для {ticker}: {e}")
    print(f"Для тикера {ticker} не найден подходящий UID.")
    return None

# Получение данных за последние 5 лет по 30-дневным отрезкам
def fetch_candles(client, uid, interval, interval_name):
    now = datetime.utcnow() + timedelta(hours=3)  # МСК
    five_years_ago = now - timedelta(days=365 * 5)
    candles = []

    start = five_years_ago
    while start < now:
        end = min(start + timedelta(days=30), now)
        print(f"Запрашиваем данные с {start} до {end} (UTC+3) для интервала {interval_name}.")
        try:
            response = client.market_data.get_candles(
                instrument_id=uid,
                from_=start,
                to=end,
                interval=interval,
            )
            for candle in response.candles:
                adjusted_time = candle.time + timedelta(hours=3)
                candles.append({
                    "time": adjusted_time,
                    "open": candle.open.units + candle.open.nano / 1e9,
                    "high": candle.high.units + candle.high.nano / 1e9,
                    "low": candle.low.units + candle.low.nano / 1e9,
                    "close": candle.close.units + candle.close.nano / 1e9,
                    "volume": candle.volume,
                })
        except Exception as e:
            print(f"Ошибка получения данных для UID {uid}: {e}")

        start = end

    return candles

# Основной процесс
def main():
    tickers = read_tickers(TICKERS_FILE)
    token = read_token(TOKEN_FILE)

    with Client(token) as client:
        for ticker in tickers:
            print(f"Обработка тикера: {ticker}...")

            uid = fetch_uid_for_ticker(client, ticker)
            if not uid:
                continue

            for interval_name, interval in INTERVALS.items():
                candles = fetch_candles(client, uid, interval, interval_name)

                if candles:
                    output_dir = os.path.join(SAVE_DIR, interval_name)
                    os.makedirs(output_dir, exist_ok=True)
                    output_file = os.path.join(output_dir, f"{ticker}.csv")
                    pd.DataFrame(candles).to_csv(output_file, index=False)
                    print(f"Данные сохранены: {output_file}")
                else:
                    print(f"Нет данных для {ticker}.")

if __name__ == "__main__":
    main()

