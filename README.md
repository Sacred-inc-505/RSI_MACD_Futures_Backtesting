
## Languages / Языки
- [English](#english)
- [Русский](#русский)

---

# English

## Project Overview

This project implements an algorithmic trading strategy based on the RSI and MACD technical indicators for analyzing historical futures data.  
The goal is to automate the search for trading signals and evaluate the profitability of the strategy, including broker commissions.

This repository demonstrates skills in Python, pandas, pandas_ta, backtesting, trading strategy development, and data visualization.

> All amounts have been converted from Russian rubles (₽) to approximate USD values at ~90 ₽/$ for international readability.

---

## Objectives
- Automatic calculation of RSI and MACD on historical data.
- Generation of BUY and SELL signals based on predefined conditions:
  - BUY — RSI increases for 4 consecutive periods, MACD_Diff changes sign from negative to positive.
  - SELL — RSI decreases for 4 consecutive periods, MACD_Diff changes sign from positive to negative.
- Smart trade exit logic:
  - Exit when MACD_Diff changes unfavorably.
  - If no exit signal appears — force close after 6 candles (24 hours on 4h timeframe).
- Profit calculation assuming full capital allocation per trade (~$5,500) and broker commission.
- Report generation:
  - Detailed CSV for each trade.
  - Summary table with financial results per instrument.

---

## How It Works
1. Load historical market data (CSV or via Tinkoff Invest API).
2. Preprocess data using pandas.
3. Calculate indicators with pandas_ta.
4. Identify trading signals based on RSI and MACD_Diff rules.
5. Manage trades:
   - Dynamic exit based on MACD_Diff.
   - Forced close after N candles.
6. Calculate profit, accounting for capital and 0.005% round-trip commission.
7. Save reports and visualize results.

---

## Data Paths
Files should be placed as follows:
- Ticker list: `data/tickers.txt`
- API token for Tinkoff Invest: `token.txt`
- Directory for saving market data: `SBERBANK_FUTURES` (created automatically)

Example structure:
```
project_root/
├─ data/
│  └─ tickers.txt
├─ token.txt
├─ SBERBANK_FUTURES/
│   └─ ... (downloaded quotes)
```

---

## Backtest Results

### Summary Table

| Instrument | Period            | Trades | Start Balance | End Balance | Avg Annual Return | Best Year |
|------------|-------------------|--------|---------------|-------------|-------------------|-----------|
| Sberbank   | 2020Q4–2025Q2     | 284    | $5,500        | $21,800     | 65% ($3,600/year) | 2022 (+$6,000) |
| Gazprom    | 2021Q1–2025Q2     | 250    | $5,500        | $5,900      | 26% ($1,450/year) in profitable years | 2022 (−$3,500) |

### Sberbank Futures (Q4 2020 — Q2 2025)
![Sberbank Futures Trading Results](docs/sber_futures.png)

### Gazprom Futures (Q1 2021 — Q2 2025)
![Gazprom Futures Trading Results](docs/gazprom_futures.png)

**Note:** The strategy was tested on historical data with broker commissions applied, assuming full capital allocation per trade.  
Charts reflect the year-by-year equity curve.

---

## License
This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.

---

# Русский

## Описание проекта

Проект реализует алгоритмическую торговую стратегию на основе технических индикаторов RSI и MACD для анализа исторических данных по фьючерсам.  
Цель — автоматизировать поиск торговых сигналов и оценить прибыльность стратегии с учётом комиссий брокера.

---

## Задачи проекта
- Автоматический расчёт RSI и MACD на исторических данных.
- Генерация сигналов BUY и SELL по заданным условиям:
  - BUY — RSI растёт 4 периода подряд, MACD_Diff меняет знак с отрицательного на положительный.
  - SELL — RSI падает 4 периода подряд, MACD_Diff меняет знак с положительного на отрицательный.
- Умный выход из сделки:
  - Закрытие позиции при неблагоприятном изменении MACD_Diff.
  - Если сигналов на выход нет — принудительное закрытие через 6 свечей (24 часа на ТФ 4h).
- Расчёт прибыли с учётом торговли на всю сумму капитала (500 000 руб. на сделку) и комиссий брокера.
- Формирование отчётов:
  - Детализированный CSV по каждой сделке.
  - Сводная таблица с результатами по каждому инструменту.

---

## Как это работает
1. Загрузка данных (CSV или через Tinkoff Invest API).
2. Предобработка данных с помощью pandas.
3. Расчёт индикаторов с помощью pandas_ta.
4. Поиск сигналов по условиям RSI и MACD_Diff.
5. Сопровождение сделок:
   - Динамический выход по MACD_Diff.
   - Принудительное закрытие через N свечей.
6. Подсчёт прибыли с учётом капитала и комиссии 0,005% за цикл сделки.
7. Сохранение отчётов и визуализация результатов.

---

## Путь для данных
Файлы должны располагаться по следующим путям:
- Список тикеров: `data/tickers.txt`
- Токен для Tinkoff Invest API: `token.txt`
- Папка для сохранения данных: `SBERBANK_FUTURES` (создаётся автоматически)

Пример структуры:
```
project_root/
├─ data/
│  └─ tickers.txt
├─ token.txt
├─ SBERBANK_FUTURES/
│   └─ ... (скачанные котировки)
```

---

## Результаты бэктестов

### Сводная таблица

| Инструмент | Период            | Сделок | Начальный баланс | Итоговый баланс | Среднегодовая доходность | Лучший год |
|------------|-------------------|--------|------------------|-----------------|--------------------------|------------|
| Сбербанк   | 2020Q4–2025Q2     | 284    | 500 000 ₽        | 1 962 000 ₽     | 65% (325 000 ₽/год)      | 2022 (+535 000 ₽) |
| Газпром    | 2021Q1–2025Q2     | 250    | 500 000 ₽        | 527 000 ₽       | 26% (130 000 ₽/год) в прибыльные годы | 2022 (−320 000 ₽) |

### Фьючерсы Сбербанка (4Q 2020 — 2Q 2025)
![Результаты торговли фьючерсами Сбербанка](docs/sber_futures.png)

### Фьючерсы Газпрома (1Q 2021 — 2Q 2025)
![Результаты торговли фьючерсами Газпрома](docs/gazprom_futures.png)

**Примечание:** стратегия тестировалась на исторических данных с применением комиссий брокера, торговля велась на весь капитал в сделке.  
Графики отражают динамику роста/снижения баланса по годам.

---

## Лицензия
Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для деталей.
