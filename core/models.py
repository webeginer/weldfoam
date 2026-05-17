# core/models.py — исправленный
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# ----------------------------------------------------------------------
# Материал (свойства)
# ----------------------------------------------------------------------

class MaterialProperties(BaseModel):
    name: str = "Ст3"
    E_GPa: float = Field(210.0, description="Модуль упругости (ГПа)")
    sigma_s0_MPa: float = Field(250.0, description="Предел текучести при 20°C (МПа)")
    alpha_1perC: float = Field(1.2e-5, description="Коэф. линейного расширения (1/°C)")
    lambda_W_mK: float = Field(50.0, description="Теплопроводность (Вт/(м·К))")
    a_m2s: float = Field(1.2e-5, description="Температуропроводность (м²/с)")
    eta: float = Field(0.75, description="КПД дуги")
    T0_C: float = Field(20.0, description="Начальная температура (°C)")
    T_melting_C: float = Field(1500.0, description="Температура плавления (°C)")

# ----------------------------------------------------------------------
# Входные данные: пошаговый режим (пользователь задаёт T(y))
# ----------------------------------------------------------------------

class DirectInput(BaseModel):
    """Прямой ввод — пользователь сам задаёт T(y) и λ(y)"""
    y_m: List[float]                    # координаты (м)
    T_C: List[float]                    # температура (°C)
    alpha: float = 1.2e-5               # 1/°C
    E_GPa: float = 210.0                # ГПа
    sigma_s0_MPa: float = 250.0         # МПа
    thickness_m: float = Field(0.004, ge=0.001, le=0.02, description="Толщина (м)")

# ----------------------------------------------------------------------
# Входные данные: расчёт по режиму сварки
# ----------------------------------------------------------------------

class WeldingInput(BaseModel):
    """Расчёт по режиму сварки — пользователь задаёт I, U, v"""
    I_A: float = Field(150.0, ge=50, le=500, description="Ток (А)")
    U_V: float = Field(25.0, ge=20, le=40, description="Напряжение (В)")
    v_ms: float = Field(0.003, ge=0.001, le=0.02, description="Скорость сварки (м/с)")  # 0.1-2.0 см/с
    h_m: float = Field(0.1, ge=0.01, le=0.5, description="Высота полосы (м)")
    delta_m: float = Field(0.004, ge=0.001, le=0.02, description="Толщина листа (м)")
    L_m: float = Field(0.5, ge=0.1, le=2.0, description="Длина полосы (м)")
    material_name: Literal["Ст3", "АМг6", "12Х18Н10Т"] = "Ст3"
    n_points: int = Field(50, ge=20, le=200, description="Количество точек по высоте")

# ----------------------------------------------------------------------
# Выходные данные: результат нагрева
# ----------------------------------------------------------------------

class HeatingResult(BaseModel):
    delta0: float
    deltah: float
    curvature_1pm: float
    stresses_MPa: List[float]
    plastic_strains_compression: List[float]
    y_coords_mm: List[float]
    iterations: int
    residual: float
    warning: Optional[str] = None  # предупреждение о перегреве

# ----------------------------------------------------------------------
# Выходные данные: полный результат
# ----------------------------------------------------------------------

class WeldingResult(BaseModel):
    heat_input_kJ_per_m: float
    T_max_C: float
    heating: HeatingResult
    n_points: int
    material: str
    deflection_mm: Optional[float] = None
    warning: Optional[str] = None

# ----------------------------------------------------------------------
# Выходные данные: полный расчёт с остыванием
# ----------------------------------------------------------------------

class FullWeldingResult(WeldingResult):
    """Результат с учётом остывания"""
    final_curvature_1pm: float
    residual_stresses_MPa: List[float]
    final_plastic_strains: List[float]
    deflection_mm: float
    cooling_steps: int
    warning: Optional[str] = None