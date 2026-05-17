# core/thermal.py
import numpy as np
from scipy.special import kn
from typing import Dict, Tuple

def temperature_profile_rykalin(
    y_m: np.ndarray,      # координаты по ширине (м), от 0 (кромка шва) до h
    I: float,             # ток (А)
    U: float,             # напряжение (В)
    v: float,             # скорость сварки (м/с) 
    delta: float,         # толщина листа (м)
    material: Dict,       # свойства: {'lambda': 50, 'a': 1.2e-5, 'eta': 0.75, 'T0': 20, 'T_melting': 1500}
    x: float = 0.0,       # расстояние от дуги вдоль шва (м)
) -> np.ndarray:
    """
    Рассчитывает температуру T(y) для сечения, отстоящего на x позади дуги.
    Формула для тонкого листа (движущийся линейный источник).
    Источник: Рыкалин, Окерблом.
    
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
    
    # Извлечение свойств материала
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
    T_melting = material.get('T_melting', 1500.0)
    T_max_limit = T_melting - 10  # ограничение чуть ниже температуры плавления
    
    # Тепловая мощность дуги (Вт)
    q = eta * U * I
    
    # Коэффициент перед K0 (формула Рыкалина в СИ)
    coeff = q / (2 * np.pi * lam * delta)
    
    # Аргумент функции Бесселя K0
    r = np.abs(y_m)
    
    if v > 0:
        arg = (v * r) / (2 * a)
    else:
        arg = np.zeros_like(r)
    
    # Вычисление температуры
    with np.errstate(divide='ignore', invalid='ignore'):
        exp_factor = np.exp(-v * x / (2 * a)) if v > 0 else 1.0
        k0_val = kn(0, np.maximum(arg, 1e-12))
        T = coeff * exp_factor * k0_val
    
    # Добавляем начальную температуру
    T = T + T0
    
    # Ограничение максимальной температуры (чуть ниже плавления)
    T = np.minimum(T, T_max_limit)
    
    # Обработка NaN и Inf
    T = np.nan_to_num(T, nan=T_max_limit, posinf=T_max_limit)
    
    return T