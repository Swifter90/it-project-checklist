FROM python:3.8

# Установка зависимостей для WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов
COPY . .

# Указание порта
EXPOSE 10000

# Команда запуска с правильной обработкой переменной PORT
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
