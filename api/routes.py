# api/routes.py
from fastapi import APIRouter, HTTPException
import numpy as np
import logging

from core.models import DirectInput, WeldingInput, HeatingResult, WeldingResult
from core.material_db import get_material
from core.physics import solve_heating  # исправлено: physics, не solver
from core.thermal import temperature_profile_rykalin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["weldfoam"])


@router.post("/calculate/direct", response_model=HeatingResult)
async def calculate_direct(input_data: DirectInput):
    """
    Эндпоинт 1: Прямой расчёт по заданному T(y).
    Используется для отладки и верификации.
    """
    try:
        # DirectInput уже в метрах (y_m, thickness_m)
        y_m = np.array(input_data.y_m)
        T = np.array(input_data.T_C)
        h_m = y_m[-1] - y_m[0]
        
        alpha = input_data.alpha
        E_Pa = input_data.E_GPa * 1e9
        sigma_s0_Pa = input_data.sigma_s0_MPa * 1e6
        thickness_m = input_data.thickness_m
        
        delta0, deltah, stresses, plastic_strains, iters, residual = solve_heating(
            y=y_m,
            T=T,
            alpha=alpha,
            E=E_Pa,
            sigma_s0=sigma_s0_Pa,
            thickness=thickness_m,
            verbose=False
        )
        
        curvature = (deltah - delta0) / h_m
        
        return HeatingResult(
            delta0=float(delta0),
            deltah=float(deltah),
            curvature_1pm=float(curvature),
            stresses_MPa=(stresses / 1e6).tolist(),
            plastic_strains_compression=plastic_strains.tolist(),
            y_coords_mm=(y_m * 1000).tolist(),
            iterations=iters,
            residual=float(residual)
        )
        
    except Exception as e:
        logger.exception("Direct calculation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate/welding", response_model=WeldingResult)
async def calculate_welding(input_data: WeldingInput):
    """
    Эндпоинт 2: Расчёт по режиму сварки (I, U, v).
    Рекомендуемый для пользователей.
    """
    try:
        # 1. Получаем свойства материала
        material = get_material(input_data.material_name)
        
        # 2. Тепловложение (кДж/м)
        q = material.eta * input_data.U_V * input_data.I_A  # Вт
        v_ms = input_data.v_ms  # уже м/с, без перевода!
        heat_input = q / v_ms  # Дж/м
        heat_input_kJ_m = heat_input / 1000.0
        
        # 3. Расчёт T(y) по Рыкалину
        h_m = input_data.h_m  # уже метры, без перевода!
        y_m = np.linspace(0, h_m, input_data.n_points)
        
        material_dict = {
            'lambda': material.lambda_W_mK,
            'a': material.a_m2s,
            'eta': material.eta,
            'T0': material.T0_C,
            'T_max_allowed': 1500.0  # можно добавить в material_db позже
        }
        delta_m = input_data.delta_m  # уже метры, без перевода!
        
        T_profile = temperature_profile_rykalin(
            y_m=y_m,
            I=input_data.I_A,
            U=input_data.U_V,
            v=v_ms,
            delta=delta_m,
            material=material_dict,
            x=0.0
        )
        
        T_max = float(np.max(T_profile))
        
        # 4. Решение задачи нагрева (без lam, solve_heating сам вычислит alpha*T)
        E_Pa = material.E_GPa * 1e9
        sigma_s0_Pa = material.sigma_s0_MPa * 1e6
        thickness_m = input_data.delta_m  # уже метры
        
        delta0, deltah, stresses, plastic_strains, iters, residual = solve_heating(
            y=y_m,
            T=T_profile,
            alpha=material.alpha_1perC,
            E=E_Pa,
            sigma_s0=sigma_s0_Pa,
            thickness=thickness_m,
            verbose=False
        )
        
        curvature = (deltah - delta0) / h_m
        
        # 5. Прогиб (предварительный, без учёта остывания)
        L_m = input_data.L_m  # уже метры
        deflection = curvature * L_m**2 / 8 if curvature != 0 else 0.0
        deflection_mm = deflection * 1000.0
        
        # 6. Формирование ответа
        return WeldingResult(
            heat_input_kJ_per_m=heat_input_kJ_m,
            T_max_C=T_max,
            heating=HeatingResult(
                delta0=float(delta0),
                deltah=float(deltah),
                curvature_1pm=float(curvature),
                stresses_MPa=(stresses / 1e6).tolist(),
                plastic_strains_compression=plastic_strains.tolist(),
                y_coords_mm=(y_m * 1000).tolist(),
                iterations=iters,
                residual=float(residual)
            ),
            n_points=input_data.n_points,
            material=material.name,
            deflection_mm=deflection_mm
        )
        
    except Exception as e:
        logger.exception("Welding calculation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "ok", "service": "WeldFOAM", "stage": "heating"}