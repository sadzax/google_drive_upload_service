# Базовый образ Python
FROM python:3.10-slim

# Устанавливаем зависимости (/app - это у контейнера, т.е. внутри app/app)
WORKDIR /app
COPY . /app

# Для совместимости импорта
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Установка переменных окружения для портов
ARG APP_PORT=8000
ENV APP_PORT=${APP_PORT}

# Установка зависимостей
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Команда по умолчанию
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${APP_PORT}"]
