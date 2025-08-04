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

# Установка переменной окружения для WeasyPrint
ENV LD_LIBRARY_PATH=/usr/lib

# Очистка кэша pip
RUN pip cache purge

# Явная установка Gunicorn
RUN pip install gunicorn==23.0.0

# Проверка установки Gunicorn
RUN which gunicorn && gunicorn --version || { echo "ERROR: Gunicorn not found"; exit 1; }

# Копирование и установка остальных зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Повторная проверка Gunicorn и отладка
RUN ls -la /app/venv/bin/ && /app/venv/bin/pip list && which gunicorn && gunicorn --version || { echo "ERROR: Gunicorn not found after requirements.txt"; exit 1; }

# Проверка существования gunicorn перед копированием файлов
RUN test -f /app/venv/bin/gunicorn || { echo "ERROR: /app/venv/bin/gunicorn does not exist"; exit 1; }

# Даем права на выполнение Gunicorn
RUN chmod +x /app/venv/bin/gunicorn

# Проверка WeasyPrint
RUN weasyprint --version || { echo "ERROR: WeasyPrint not found"; exit 1; }

# Копирование остальных файлов
COPY . .

# Проверка gunicorn после копирования файлов
RUN test -f /app/venv/bin/gunicorn || { echo "ERROR: /app/venv/bin/gunicorn missing after COPY"; exit 1; }
RUN ls -la /app/venv/bin/

# Создание стартового скрипта для Gunicorn
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo 'echo "Checking gunicorn availability:"' >> /app/start.sh && \
    echo 'ls -la /app/venv/bin/gunicorn' >> /app/start.sh && \
    echo 'if [ ! -f /app/venv/bin/gunicorn ]; then' >> /app/start.sh && \
    echo '  echo "ERROR: /app/venv/bin/gunicorn not found at runtime"' >> /app/start.sh && \
    echo '  exit 1' >> /app/start.sh && \
    echo 'fi' >> /app/start.sh && \
    echo 'exec /app/venv/bin/gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:app' >> /app/start.sh && \
    chmod +x /app/start.sh

# Указание порта
EXPOSE $PORT

# Запуск через стартовый скрипт
CMD ["/app/start.sh"]
