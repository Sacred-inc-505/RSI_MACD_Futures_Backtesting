import os
import pandas as pd
from math import floor
from glob import glob


def calculate_trade_profit_smart(data, signal_index, trade_type, tp_ticks=2):
    entry_price = data.iloc[signal_index]['close']
    open_macd_diff = data.iloc[signal_index]['MACD_Diff']
    max_wait = min(6, len(data) - signal_index - 1)
    exit_index = None
    tick_count = 0

    for i in range(1, max_wait + 1):
        idx = signal_index + i
        prev_close = data.iloc[idx - 1]['close']
        curr_close = data.iloc[idx]['close']
        curr_macd_diff = data.iloc[idx]['MACD_Diff']

        if trade_type == 'BUY':
            tick_count = tick_count + 1 if curr_close > prev_close else 0
        else:  # SELL
            tick_count = tick_count + 1 if curr_close < prev_close else 0

        if tick_count >= tp_ticks:
            exit_index = idx
            break

        if (trade_type == 'BUY' and curr_macd_diff < open_macd_diff) or \
           (trade_type == 'SELL' and curr_macd_diff > open_macd_diff):
            exit_index = idx
            break

    if exit_index is None:
        exit_index = signal_index + max_wait

    exit_price = data.iloc[exit_index]['close']
    profit = (exit_price - entry_price) if trade_type == 'BUY' else (entry_price - exit_price)
    exit_timestamp = data.iloc[exit_index]['timestamp']
    return exit_timestamp, profit, exit_index


def check_buy_signals(data, ticker):
    trades = []
    for i in range(4, len(data)):
        if data.iloc[i].get('can_trade', 0) != 1:
            continue

        last_five = data.iloc[i - 4:i + 1]
        current_macd_diff = last_five['MACD_Diff'].iloc[-1]
        prev_macd_diff = last_five['MACD_Diff'][:-1]
        current_rsi = last_five['RSI'].iloc[-1]
        prev_rsi = last_five['RSI'][:-1]

        if (prev_rsi < current_rsi).all() and current_macd_diff > 0 and (prev_macd_diff < 0).all():
            exit_time, profit, exit_index = calculate_trade_profit_smart(data, i, 'BUY')
            trades.append({
                'ticker': ticker,
                'direction': 'BUY',
                'entry_time': data.iloc[i]['timestamp'],
                'entry_price': data.iloc[i]['close'],
                'exit_time': exit_time,
                'exit_price': data.iloc[exit_index]['close'],
                'profit': profit
            })
    return trades


def check_sell_signals(data, ticker):
    trades = []
    for i in range(4, len(data)):
        if data.iloc[i].get('can_trade', 0) != 1:
            continue

        last_five = data.iloc[i - 4:i + 1]
        current_macd_diff = last_five['MACD_Diff'].iloc[-1]
        prev_macd_diff = last_five['MACD_Diff'][:-1]
        current_rsi = last_five['RSI'].iloc[-1]
        prev_rsi = last_five['RSI'][:-1]

        if (prev_rsi > current_rsi).all() and current_macd_diff < 0 and (prev_macd_diff > 0).all():
            exit_time, profit, exit_index = calculate_trade_profit_smart(data, i, 'SELL')
            trades.append({
                'ticker': ticker,
                'direction': 'SELL',
                'entry_time': data.iloc[i]['timestamp'],
                'entry_price': data.iloc[i]['close'],
                'exit_time': exit_time,
                'exit_price': data.iloc[exit_index]['close'],
                'profit': profit
            })
    return trades


input_dir = "GAZPROM_FUTURES/4_hour/rsi_macd"
all_files = glob(os.path.join(input_dir, "*.csv"))

all_trades = []
for file_path in all_files:
    try:
        data = pd.read_csv(file_path, parse_dates=['timestamp'])
        required_columns = {'timestamp', 'RSI', 'MACD_Diff', 'close', 'can_trade'}
        if not required_columns.issubset(data.columns):
            print(f"Пропущены колонки в файле: {file_path}")
            continue
        data.sort_values('timestamp', inplace=True)
        ticker = os.path.basename(file_path).replace(".csv", "")
        trades_buy = check_buy_signals(data, ticker)
        trades_sell = check_sell_signals(data, ticker)
        all_trades.extend(trades_buy + trades_sell)
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")

output_file = "trade_report.csv"
df = pd.DataFrame(all_trades)
df = df[['ticker', 'direction', 'entry_time', 'entry_price', 'exit_time', 'exit_price', 'profit']]
df.to_csv(output_file, index=False)
print(f"Trade report saved to: {output_file}")
