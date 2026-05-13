# WeldFOAM - Калькулятор сварочных деформаций
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .

# Установка Python пакетов
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Открытие портов
EXPOSE 8000 8501

# Запуск API сервера и UI
CMD ["sh", "-c", "python main.py & streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
