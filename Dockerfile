# Базовый образ Python
FROM python:3.10-slim

# Устанавливаем зависимости
WORKDIR /app
COPY . /app

# Для совместимости импорта
ENV PYTHONPATH="${PYTHONPATH}:/app"

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Команда по умолчанию, которая будет перезаписана для каждого сервиса в docker-compose.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
