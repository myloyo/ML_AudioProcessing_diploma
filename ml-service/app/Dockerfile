FROM python:3.11-slim

# Устанавливаем зависимости системы, нужные для librosa, soundfile и PyTorch
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код сервиса
COPY . .

# FastAPI будет работать на порту 8000
EXPOSE 8000

# Точка входа — запуск сервиса FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
