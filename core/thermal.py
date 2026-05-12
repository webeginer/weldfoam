# core/thermal.py
import numpy as np
from scipy.special import kn
from typing import Dict, Optional

def temperature_profile_rykalin(
    y_m: np.ndarray,      # координаты по ширине (м), от 0 (кромка шва) до h
    I: float,             # ток (А)
    U: float,             # напряжение (В)
    v: float,             # скорость сварки (м/с) 
    delta: float,         # толщина листа (м)
    material: Dict,       # свойства: {'lambda': 50, 'a': 1.2e-5, 'eta': 0.75, 'T0': 20, 'T_max_allowed': 1500}
    x: float = 0.0,       # расстояние от дуги вдоль шва (м)
) -> np.ndarray:
    """
    Рассчитывает температуру T(y) для сечения, отстоящего на x позади дуги.
    Формула для тонкого листа (движущийся линейный источник, предельное состояние).
    
    Источник: Рыкалин, Окерблом (стр. 31).
    
    Параметры:
        y_m: координаты по ширине (м)
        I: ток (А)
        U: напряжение (В)
        v: скорость сварки (м/с)
        delta: толщина листа (м)
        material: словарь с ключами:
            'lambda' - теплопроводность (Вт/(м·К))
            'a' - температуропроводность (м²/с)
            'eta' - КПД дуги
            'T0' - начальная температура (°C)
            'T_max_allowed' - макс. температура (опционально, по умолчанию 1500)
        x: расстояние от дуги (м)
    
    Возвращает:
        T: массив температур (°C)
    """
    # Проверка входных данных
    if len(y_m) == 0:
        raise ValueError("Массив y_m не может быть пустым")
    if I <= 0:
        raise ValueError(f"Ток I должен быть положительным: {I}")
    if U <= 0:
        raise ValueError(f"Напряжение U должно быть положительным: {U}")
    if v <= 0:
        raise ValueError(f"Скорость v должна быть положительной: {v}")
    if delta <= 0:
        raise ValueError(f"Толщина delta должна быть положительной: {delta}")
    
    # Извлечение свойств материала с проверкой
    lam = material.get('lambda')
    if lam is None:
        raise KeyError("material должен содержать ключ 'lambda'")
    if lam <= 0:
        raise ValueError(f"Теплопроводность lambda должна быть положительной: {lam}")
    
    a = material.get('a')
    if a is None:
        raise KeyError("material должен содержать ключ 'a'")
    if a <= 0:
        raise ValueError(f"Температуропроводность a должна быть положительной: {a}")
    
    eta = material.get('eta')
    if eta is None:
        raise KeyError("material должен содержать ключ 'eta'")
    if not 0 < eta < 1:
        raise ValueError(f"КПД eta должен быть в диапазоне (0,1): {eta}")
    
    T0 = material.get('T0', 20.0)
    T_max_allowed = material.get('T_max_allowed', 1500.0)
    
    # Тепловая мощность дуги (Вт)
    q = eta * U * I
    
    # Коэффициент перед K0 (формула Рыкалина, коэффициент 0.24 - убран)
    coeff = q / (2 * np.pi * lam * delta)
    
    # Аргумент функции Бесселя K0
    r = np.abs(y_m)  # расстояние от оси шва (м)
    
    # Защита от деления на ноль при v=0 (статический источник)
    if v > 0:
        arg = (v * r) / (2 * a)
    else:
        arg = np.zeros_like(r)
    
    # Вычисление температуры
    with np.errstate(divide='ignore', invalid='ignore'):
        # Экспоненциальный множитель для x (влияние расстояния от дуги)
        exp_factor = np.exp(-v * x / (2 * a)) if v > 0 else 1.0
        
        # Функция Бесселя K0 (при arg=0 уходит в бесконечность)
        k0_val = kn(0, np.maximum(arg, 1e-12))
        
        T = coeff * exp_factor * k0_val
    
    # Ограничение максимальной температуры
    T = np.minimum(T, T_max_allowed)
    
    # Добавляем начальную температуру
    T = T + T0
    
    # Обработка NaN и Inf
    T = np.nan_to_num(T, nan=T_max_allowed, posinf=T_max_allowed)
    
    return T