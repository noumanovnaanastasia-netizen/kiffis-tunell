# Использовать официальный образ Python
FROM python:3.11-slim

# Установить рабочую папку внутри контейнера
WORKDIR /app

# Скопировать список зависимостей
COPY requirements.txt .

# Установить все необходимые библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать ВСЕ файлы проекта (включая config, database, handlers, main)
COPY . .

# Команда для запуска нашего бота
CMD ["python", "main.py"]
