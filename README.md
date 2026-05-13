# 🔥 WeldFOAM - Калькулятор сварочных деформаций

Расчёт напряжений и деформаций при сварке тонких листов по методу Окерблома.

## 📊 Возможности

- **Этап 1: Нагрев** - расчёт напряжений и пластических деформаций в момент нагрева
- **Этап 2: Остывание** - пошаговое охлаждение с накоплением пластики
- **Остаточные напряжения** - эпюры после полного остывания
- **Стрелка прогиба** - расчёт деформации полосы

## 🏗️ Материалы

| Марка | E (ГПа) | σ_s0 (МПа) | α (1/°C) | λ (Вт/м·К) |
|-------|---------|------------|----------|------------|
| Ст3 | 210 | 250 | 1.2e-5 | 50 |
| АМг6 | 71 | 150 | 2.4e-5 | 120 |
| 12Х18Н10Т | 193 | 205 | 1.6e-5 | 15 |

## 🚀 Быстрый старт

### Локальный запуск

```
# Клонировать репозиторий
git clone https://github.com/webeginer/weldfoam.git
cd weldfoam

# Создать виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Запустить API сервер
python main.py

# В другом терминале запустить UI
streamlit run app.py
```

### Docker

```
# Собрать образ
docker build -t weldfoam .

# Запустить контейнер
docker run -p 8000:8000 -p 8501:8501 weldfoam
```

### 📡 API Эндпоинты

|Эндпоинт|Метод|Описание|
|---|:---:|---|
|/api/v1/health|GET|Проверка здоровья сервиса
|/api/v1/calculate/direct|POST|Прямой ввод T(y) (отладка)
|/api/v1/calculate/welding|POST|Только нагрев по параметрам сварки
|/api/v1/calculate/welding-full|POST|Полный расчёт (нагрев + остывание)

### Пример запроса

```
curl -X POST http://localhost:8000/api/v1/calculate/welding-full \
  -H "Content-Type: application/json" \
  -d '{
    "I_A": 150,
    "U_V": 25,
    "v_ms": 0.003,
    "h_m": 0.1,
    "delta_m": 0.004,
    "L_m": 0.5,
    "material_name": "Ст3",
    "n_points": 50
  }'
```

### 🧪 Тестирование

```
pytest tests/test_core.py -v
pytest tests/test_cooling.py -v
```

📁 Структура проекта

```
weldfoam/
├── core/
│   ├── physics.py      # solve_heating (прямой перебор)
│   ├── thermal.py      # temperature_profile_rykalin
│   ├── history.py      # cool_down, HistoryTracker
│   ├── material_db.py  # база материалов
│   └── models.py       # Pydantic модели
├── api/
│   └── routes.py       # FastAPI эндпоинты
├── tests/
│   ├── test_core.py    # 4 теста этапа 1
│   └── test_cooling.py # 2 теста этапа 2
├── app.py              # Streamlit UI
├── main.py             # FastAPI сервер
├── Dockerfile          # Docker конфигурация
└── requirements.txt    # зависимости
```

### 📚 Источники

- Окерблом Н.О. "Расчёт деформаций при сварке" - методология расчёта

- Рыкалин Н.Н. "Тепловые процессы при сварке" - температурные поля

### 📄 Лицензия
MIT

### 👨‍💻 Авторы
- Архитектор ПО
- Доктор технических наук

⭐ Если проект полезен, поставьте звезду на GitHub!