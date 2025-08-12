import os
import pandas as pd
from math import floor
from glob import glob


def calculate_trade_profit_smart(data, signal_index, trade_type, tp_ticks=2):

    entry_price = data.iloc[signal_index]['close']
    open_macd_diff = data.iloc[signal_index]['MACD_Diff']
    max_wait = min(6, len(data) - signal_index - 1)
    exit_index = None

    # Счётчик подряд благоприятных тиков
    tick_count = 0

    for i in range(1, max_wait + 1):
        idx = signal_index + i
        prev_close = data.iloc[idx - 1]['close']
        curr_close = data.iloc[idx]['close']
        curr_macd_diff = data.iloc[idx]['MACD_Diff']

        # Проверяем движение цены
        if trade_type == 'BUY':
            if curr_close > prev_close:
                tick_count += 1
            else:
                tick_count = 0
        else:  # SELL
            if curr_close < prev_close:
                tick_count += 1
            else:
                tick_count = 0

        # Если набрали нужное число подряд, выходим по TP
        if tick_count >= tp_ticks:
            exit_index = idx
            break

        # Иначе проверяем условие MACD_Diff
        if trade_type == 'BUY' and curr_macd_diff < open_macd_diff:
            exit_index = idx
            break
        elif trade_type == 'SELL' and curr_macd_diff > open_macd_diff:
            exit_index = idx
            break

    # Если ни одно условие не сработало — выходим в последний возможный бар
    if exit_index is None:
        exit_index = signal_index + max_wait

    exit_price = data.iloc[exit_index]['close']
    profit = (exit_price - entry_price) if trade_type == 'BUY' else (entry_price - exit_price)
    exit_timestamp = data.iloc[exit_index]['timestamp']
    return exit_timestamp, profit, exit_index


def check_buy_signals(data, ticker):
    """
    Ищет сигналы на покупку (BUY) в данных и возвращает список сделок.
    Сделка рассматривается только если на момент сигнала значение can_trade == 1.
    """
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
            trade = {
                'ticker': ticker,
                'direction': 'BUY',
                'entry_time': data.iloc[i]['timestamp'],
                'entry_price': data.iloc[i]['close'],
                'open_MACD_Diff': data.iloc[i]['MACD_Diff'],
                'exit_time': exit_time,
                'exit_price': data.iloc[exit_index]['close'],
                'profit': profit
            }
            trades.append(trade)
    return trades


def check_sell_signals(data, ticker):
    """
    Ищет сигналы на продажу (SELL) в данных и возвращает список сделок.
    Сделка рассматривается только если на момент сигнала значение can_trade == 1.
    """
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
            trade = {
                'ticker': ticker,
                'direction': 'SELL',
                'entry_time': data.iloc[i]['timestamp'],
                'entry_price': data.iloc[i]['close'],
                'open_MACD_Diff': data.iloc[i]['MACD_Diff'],
                'exit_time': exit_time,
                'exit_price': data.iloc[exit_index]['close'],
                'profit': profit
            }
            trades.append(trade)
    return trades


def compute_max_drawdown_from_series(series: pd.Series) -> float:
    """
    Для данного ряда значений (equity) считает максимальную просадку (в абсолютном выражении).
    """
    running_max = series.cummax()
    drawdown = running_max - series
    return float(drawdown.max())


def generate_report(
        trades,
        fixed_output_file='trades_report_fixed.csv',
        reinvest_output_file='trades_report_reinvest.csv',
        nondup_fixed_output_file='trades_report_fixed_nondup.csv',
        quarterly_fixed_file='quarterly_fixed.csv',
        initial_capital=500000
):
    """
    Генерирует четыре отчёта:
      1. Fixed Capital Model.
      2. Reinvestment Model.
      3. Fixed Capital Model без дубликатов по дате.
      4. Quarterly Fixed Capital Model (CSV с квартальной статистикой).

    Теперь в квартальном отчёте вместо max_profit выводится общая сумма profit за квартал.
    """
    if not trades:
        print("Сделок не найдено.")
        return

    # Собираем все сделки в DataFrame и сортируем по entry_time
    df = pd.DataFrame(trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df = df.sort_values('entry_time').reset_index(drop=True)

    # --- 1) Fixed Capital Model ---
    fixed_profits = []
    for _, row in df.iterrows():
        entry_price = row['entry_price']
        exit_price = row['exit_price']
        profit_per_contract = (exit_price - entry_price) if row['direction'] == 'BUY' else (entry_price - exit_price)
        collateral = entry_price / 4.5
        contracts = floor(initial_capital / collateral)
        fixed_profits.append(contracts * profit_per_contract)
    df['fixed_profit'] = fixed_profits
    df['fixed_cum_profit'] = df['fixed_profit'].cumsum()
    df['fixed_equity'] = initial_capital + df['fixed_cum_profit']
    df['fixed_return'] = df['fixed_equity'].pct_change()

    # --- 2) Reinvestment Model ---
    reinvest_profits = []
    reinvest_equity_list = []
    current_capital = initial_capital
    for _, row in df.iterrows():
        entry_price = row['entry_price']
        exit_price = row['exit_price']
        profit_per_contract = (exit_price - entry_price) if row['direction'] == 'BUY' else (entry_price - exit_price)
        collateral = entry_price / 4.5
        contracts = floor(current_capital / collateral)
        reinvest_profit = contracts * profit_per_contract
        current_capital += reinvest_profit
        reinvest_profits.append(reinvest_profit)
        reinvest_equity_list.append(current_capital)
    df['reinvest_profit'] = reinvest_profits
    df['reinvest_equity'] = reinvest_equity_list
    df['reinvest_return'] = df['reinvest_equity'].pct_change()

    # --- 3) Fixed Capital Model без дубликатов по дате ---
    df['trade_date'] = df['entry_time'].dt.date
    df['ticker_numeric'] = pd.to_numeric(df['ticker'], errors='coerce')

    df_sorted = df.sort_values(
        ['trade_date', 'ticker_numeric', 'ticker'],
        ascending=[True, False, False]
    )
    df_nondup = df_sorted.drop_duplicates(subset='trade_date', keep='first').copy()
    df_nondup.drop(columns=['ticker_numeric'], inplace=True)

    # Вновь пересчитаем equity для nondup
    df_nondup['fixed_cum_profit'] = df_nondup['fixed_profit'].cumsum()
    df_nondup['fixed_equity'] = initial_capital + df_nondup['fixed_cum_profit']
    df_nondup['fixed_return'] = df_nondup['fixed_equity'].pct_change()

    # Метрики для nondup
    nondup_valid_returns = df_nondup['fixed_return'].dropna()
    nondup_sharpe = (
        nondup_valid_returns.mean() / nondup_valid_returns.std()
        if nondup_valid_returns.std() != 0 else float('nan')
    )
    nondup_rolling_max = df_nondup['fixed_equity'].cummax()
    nondup_drawdown = nondup_rolling_max - df_nondup['fixed_equity']
    nondup_max_drawdown = float(nondup_drawdown.max())
    nondup_total_profit = df_nondup[df_nondup['fixed_profit'] > 0]['fixed_profit'].sum()
    nondup_total_loss = abs(df_nondup[df_nondup['fixed_profit'] < 0]['fixed_profit'].sum())
    nondup_profit_factor = (
        nondup_total_profit / nondup_total_loss
        if nondup_total_loss != 0 else float('inf')
    )

    # Годовой обзор для nondup
    df_nondup['year'] = df_nondup['entry_time'].dt.year
    nondup_annual = []
    for year, group in df_nondup.groupby('year'):
        group_sorted = group.sort_values('entry_time')
        start_eq = group_sorted.iloc[0]['fixed_equity']
        group_eq = group_sorted['fixed_equity'] - start_eq
        rolling_max_year = group_eq.cummax()
        drawdown_year = rolling_max_year - group_eq
        max_dd_year = float(drawdown_year.max())
        nondup_annual.append({
            'year': year,
            'num_trades': len(group_sorted),
            'total_profit': float(group_sorted['fixed_profit'].sum()),
            'max_drawdown': max_dd_year
        })

    # --- 4) Quarterly Fixed Capital Model ---
    # Собираем equity-кривую для Fixed: в df есть столбцы exit_time, fixed_equity, fixed_profit
    equity_df = df[['exit_time', 'fixed_equity', 'fixed_profit']].copy()
    equity_df.rename(
        columns={
            'exit_time': 'timestamp',
            'fixed_equity': 'equity',
            'fixed_profit': 'profit'
        },
        inplace=True
    )
    equity_df['year'] = equity_df['timestamp'].dt.year
    equity_df['quarter'] = equity_df['timestamp'].dt.quarter

    quarterly_rows = []
    for (y, q), group in equity_df.groupby(['year', 'quarter']):
        num_trades = len(group)  # число сделок (точек equity) в этом квартале
        balance_end = float(group.sort_values('timestamp').iloc[-1]['equity'])
        total_profit = float(group['profit'].sum())  # ИТОГОВАЯ прибыль за квартал

        # Для просадки возьмём equity-ряд, отсортированный по времени
        series_equity = group.sort_values('timestamp')['equity']
        max_drawdown = compute_max_drawdown_from_series(series_equity)

        quarterly_rows.append({
            'year': y,
            'quarter': q,
            'num_trades': num_trades,
            'balance_end': balance_end,
            'profit': total_profit,
            'max_drawdown': max_drawdown
        })

    quarterly_df = pd.DataFrame(quarterly_rows)
    quarterly_df.sort_values(['year', 'quarter'], inplace=True)

    # Сохраняем quarterly_df в отдельный файл
    quarterly_df.to_csv(quarterly_fixed_file, index=False, float_format='%.2f')

    # ========== ПЕЧАТЬ РЕЗУЛЬТАТОВ В КОНСОЛЬ ==========
    print("\n=== Fixed Capital Model без дубликатов по дате ===")
    print(f"Общее число сделок: {len(df_nondup)}")
    print(f"Суммарная прибыль: {df_nondup['fixed_profit'].sum():,.2f} руб.")
    print(f"Итоговая equity: {df_nondup['fixed_equity'].iloc[-1]:,.2f} руб.")
    print(f"Sharpe Ratio: {nondup_sharpe:.4f}")
    print(f"Max Drawdown: {nondup_max_drawdown:,.2f} руб.")
    print(f"Profit Factor: {nondup_profit_factor:.4f}")
    print("Годовой анализ (nondup):")
    for ann in sorted(nondup_annual, key=lambda x: x['year']):
        print(
            f"  {ann['year']}: {ann['num_trades']} сделок, "
            f"прибыль {ann['total_profit']:,.2f} руб., "
            f"макс. просадка {ann['max_drawdown']:,.2f} руб."
        )

    print(f"\nОтчёт nondup сохранён в: {nondup_fixed_output_file}")
    # Сохраняем три CSV, как было до этого
    df.to_csv(fixed_output_file, index=False)
    print(f"Fixed Capital Model сохранён в: {fixed_output_file}")
    df.to_csv(reinvest_output_file, index=False)
    print(f"Reinvestment Model сохранён в: {reinvest_output_file}")
    print(f"Quarterly Fixed Model сохранён в: {quarterly_fixed_file}")


# === Основной блок обработки файлов с индикаторами ===
input_dir = "SBERBANK_FUTURES/4_hour/rsi_macd"
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

fixed_output_file = "trades_report_fixed.csv"
reinvest_output_file = "trades_report_reinvest.csv"
nondup_fixed_output_file = "trades_report_fixed_nondup.csv"
quarterly_fixed_file = "quarterly_fixed.csv"

generate_report(
    all_trades,
    fixed_output_file=fixed_output_file,
    reinvest_output_file=reinvest_output_file,
    nondup_fixed_output_file=nondup_fixed_output_file,
    quarterly_fixed_file=quarterly_fixed_file,
    initial_capital=500000  # <-- исходный баланс 500 000
)

