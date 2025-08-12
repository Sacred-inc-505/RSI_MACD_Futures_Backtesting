import os
import pandas as pd
import pandas_ta as ta
from glob import glob

# Настройки индикаторов
RSI_PERIOD = 20
MACD_FAST = 15
MACD_SLOW = 30
MACD_SIGNAL = 10

input_dir = "GAZPROM_FUTURES/4_hour"
output_dir = os.path.join(input_dir, "rsi_macd")
os.makedirs(output_dir, exist_ok=True)

def calculate_and_save_indicators(file_path, output_file, rsi_period=RSI_PERIOD, macd_fast=MACD_FAST,
                                  macd_slow=MACD_SLOW, macd_signal=MACD_SIGNAL):
    print(f"Обработка файла: {file_path}")
    data = pd.read_csv(file_path, parse_dates=['time'])
    data.rename(columns={'time': 'timestamp'}, inplace=True)

    # Проверяем наличие необходимых колонок
    if not {'timestamp', 'close'}.issubset(data.columns):
        print(f"Пропущены нужные колонки в {file_path}")
        return

    data.sort_values('timestamp', inplace=True)

    if len(data) < max(macd_slow, rsi_period):
        print(f"Недостаточно данных в {file_path}")
        return

    data['close'] = data['close'].ffill().bfill()

    # Расчет RSI
    data['RSI'] = ta.rsi(data['close'], length=rsi_period)

    # Расчет MACD и связанных индикаторов
    try:
        macd = ta.macd(data['close'], fast=macd_fast, slow=macd_slow, signal=macd_signal)
        if macd is None:
            print("MACD не рассчитан")
            return

        macd_column = f"MACD_{macd_fast}_{macd_slow}_{macd_signal}"
        signal_column = f"MACDs_{macd_fast}_{macd_slow}_{macd_signal}"

        data['MACD'] = macd[macd_column]
        data['Signal'] = macd[signal_column]
        data['MACD_Diff'] = data['MACD'] - data['Signal']
    except Exception as e:
        print(f"Ошибка при расчёте MACD: {e}")
        return

    # Оценка возможности торговли по объему
    # Изначально для каждой свечи ставим 0, то есть торговля невозможна
    data['can_trade'] = 0
    if 'volume' in data.columns:
        found = False
        for i in range(len(data) - 2):
            # Если нашли 3 подряд свечи с volume > 1000, начиная с этой свечи считаем, что торговать можно
            if data.iloc[i]['volume'] > 1000 and data.iloc[i+1]['volume'] > 1000 and data.iloc[i+2]['volume'] > 1000:
                start_index = i + 2  # начиная с третьей свечи
                data.loc[start_index:, 'can_trade'] = 1
                found = True
                break
        if not found:
            print(f"В файле {file_path} не найдено 3 подряд свечей с volume > 1000")
    else:
        print(f"Колонка 'volume' не найдена в {file_path}")

    # Сохраняем результат
    columns_to_save = ['timestamp', 'close', 'RSI', 'MACD', 'Signal', 'MACD_Diff', 'can_trade']
    data[columns_to_save].to_csv(output_file, index=False)
    print(f"Сохранено: {output_file}")

# Обработка всех CSV-файлов
csv_files = glob(os.path.join(input_dir, "*.csv"))

for file_path in csv_files:
    filename = os.path.basename(file_path)
    output_path = os.path.join(output_dir, filename)
    calculate_and_save_indicators(file_path, output_path)
