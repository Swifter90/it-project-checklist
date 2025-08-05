# Используем Python 3.10
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Обновляем pip до последней версии
RUN pip install --upgrade pip

# Копируем файлы проекта
COPY requirements.txt .
COPY app.py .
COPY templates/ templates/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Указываем порт, который будет использовать приложение
EXPOSE 8080

# Команда для запуска приложения
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
