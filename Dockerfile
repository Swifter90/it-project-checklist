FROM python:3.10-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt .
COPY app.py .
COPY templates/ templates/

# Установка системных зависимостей для kaleido
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    fonts-liberation \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
