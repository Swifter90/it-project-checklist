# Используем образ Python 3.8
FROM python:3.8

# Установка системных зависимостей для WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Создание виртуального окружения
RUN python -m venv /app/venv

# Активируем виртуальную среду
ENV PATH="/app/venv/bin:$PATH"

# Очистка кэша pip
RUN pip cache purge

# Явная установка Gunicorn
RUN pip install gunicorn==23.0.0

# Проверка установки Gunicorn
RUN which gunicorn && gunicorn --version || { echo "ERROR: Gunicorn not found"; exit 1; }

# Копирование и установка остальных зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Повторная проверка Gunicorn
RUN which gunicorn && gunicorn --version || { echo "ERROR: Gunicorn not found after requirements.txt"; exit 1; }

# Даем права на выполнение Gunicorn
RUN chmod +x /app/venv/bin/gunicorn

# Копирование остальных файлов
COPY . .

# Указание порта (для Render порт задается через переменную $PORT, а не фиксированный 10000)
EXPOSE $PORT

# Команда запуска Gunicorn с полным путем
CMD ["/app/venv/bin/gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
