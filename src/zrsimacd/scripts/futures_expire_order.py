import os
import pandas as pd
from glob import glob

# Папка с данными
input_dir = "GAZPROM_FUTURES/4_hour"

# Получаем все CSV-файлы
csv_files = glob(os.path.join(input_dir, "*.csv"))

# Храним: [(старое_имя, последняя_дата)]
futures_closure = []

for file_path in csv_files:
    try:
        df = pd.read_csv(file_path, parse_dates=["time"])
        if df.empty:
            continue
        last_date = df["time"].max()
        futures_closure.append((file_path, last_date))
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")

# Сортировка по дате закрытия
futures_closure.sort(key=lambda x: x[1])

# Переименование файлов в соответствии с порядком закрытия
for i, (old_path, date) in enumerate(futures_closure, start=1):
    new_filename = f"{i}.csv"
    new_path = os.path.join(input_dir, new_filename)

    # Удалим файл, если уже существует (перезапись)
    if os.path.exists(new_path):
        os.remove(new_path)

    os.rename(old_path, new_path)
    print(f"✅ {os.path.basename(old_path)} → {new_filename} (закрытие: {date.date()})")

print("\n🎉 Переименование завершено.")


