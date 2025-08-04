FROM python:3.8

# Установка зависимостей для WeasyPrint
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
ENV PATH="/app/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Проверка установки Gunicorn
RUN which gunicorn || echo "Gunicorn not found after pip install"

# Копирование остальных файлов
COPY . .

# Указание порта
EXPOSE 10000

# Команда запуска Gunicorn с явной активацией виртуального окружения
CMD ["/app/venv/bin/gunicorn", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:${PORT:-10000}", "app:app"]
