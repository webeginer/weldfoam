from fastapi import APIRouter, HTTPException
import numpy as np
import logging

from core.models import DirectInput, WeldingInput, HeatingResult, WeldingResult, FullWeldingResult
from core.material_db import get_material
from core.physics import solve_heating
from core.thermal import temperature_profile_rykalin
from core.history import cool_down

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["weldfoam"])


@router.post("/calculate/direct", response_model=HeatingResult)
async def calculate_direct(input_data: DirectInput):
    """Прямой расчёт по заданному T(y) (только нагрев)."""
    try:
        y_m = np.array(input_data.y_m)
        T = np.array(input_data.T_C)
        h_m = y_m[-1] - y_m[0]
        
        alpha = input_data.alpha
        E_Pa = input_data.E_GPa * 1e9
        sigma_s0_Pa = input_data.sigma_s0_MPa * 1e6
        thickness_m = input_data.thickness_m
        
        delta0, deltah, stresses, plastic_strains, iters, residual = solve_heating(
            y=y_m, T=T, alpha=alpha, E=E_Pa, sigma_s0=sigma_s0_Pa,
            thickness=thickness_m, n_grid=30, verbose=False
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
    """Расчёт по режиму сварки (только нагрев)."""
    try:
        material = get_material(input_data.material_name)
        
        q = material.eta * input_data.U_V * input_data.I_A
        v_ms = input_data.v_ms
        heat_input = q / v_ms
        heat_input_kJ_m = heat_input / 1000.0
        
        h_m = input_data.h_m
        y_m = np.linspace(0, h_m, input_data.n_points)
        
        material_dict = {
            'lambda': material.lambda_W_mK,
            'a': material.a_m2s,
            'eta': material.eta,
            'T0': material.T0_C,
            'T_max_allowed': 1500.0
        }
        delta_m = input_data.delta_m
        
        T_profile = temperature_profile_rykalin(
            y_m=y_m, I=input_data.I_A, U=input_data.U_V, v=v_ms,
            delta=delta_m, material=material_dict, x=0.0
        )
        
        T_max = float(np.max(T_profile))
        
        E_Pa = material.E_GPa * 1e9
        sigma_s0_Pa = material.sigma_s0_MPa * 1e6
        thickness_m = input_data.delta_m
        
        delta0, deltah, stresses, plastic_strains, iters, residual = solve_heating(
            y=y_m, T=T_profile, alpha=material.alpha_1perC,
            E=E_Pa, sigma_s0=sigma_s0_Pa, thickness=thickness_m,
            n_grid=30, verbose=False
        )
        
        curvature = (deltah - delta0) / h_m
        
        L_m = input_data.L_m
        deflection = curvature * L_m**2 / 8 if curvature != 0 else 0.0
        deflection_mm = deflection * 1000.0
        
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


@router.post("/calculate/welding-full", response_model=FullWeldingResult)
async def calculate_welding_full(input_data: WeldingInput):
    """
    Полный расчёт по режиму сварки (нагрев + остывание).
    Возвращает остаточные напряжения и финальную кривизну.
    """
    try:
        material = get_material(input_data.material_name)
        
        q = material.eta * input_data.U_V * input_data.I_A
        v_ms = input_data.v_ms
        heat_input = q / v_ms
        heat_input_kJ_m = heat_input / 1000.0
        
        h_m = input_data.h_m
        y_m = np.linspace(0, h_m, input_data.n_points)
        
        material_dict = {
            'lambda': material.lambda_W_mK,
            'a': material.a_m2s,
            'eta': material.eta,
            'T0': material.T0_C,
            'T_max_allowed': 1500.0
        }
        delta_m = input_data.delta_m
        
        T_profile = temperature_profile_rykalin(
            y_m=y_m, I=input_data.I_A, U=input_data.U_V, v=v_ms,
            delta=delta_m, material=material_dict, x=0.0
        )
        
        T_max = float(np.max(T_profile))
        
        E_Pa = material.E_GPa * 1e9
        sigma_s0_Pa = material.sigma_s0_MPa * 1e6
        thickness_m = input_data.delta_m
        L_m = input_data.L_m
        
        # Этап 1: нагрев
        delta0, deltah, stresses, plastic_strains, iters, residual = solve_heating(
            y=y_m, T=T_profile, alpha=material.alpha_1perC,
            E=E_Pa, sigma_s0=sigma_s0_Pa, thickness=thickness_m,
            n_grid=30, verbose=False
        )
        
        initial_curvature = (deltah - delta0) / h_m
        
        # Этап 2: остывание
        final_stresses, final_plastic, curvatures, temperatures = cool_down(
            y=y_m, T_max=T_profile, alpha=material.alpha_1perC,
            E=E_Pa, sigma_s0=sigma_s0_Pa, thickness=thickness_m,
            n_steps=40, verbose=False
        )
        
        final_curvature = curvatures[-1] if curvatures else initial_curvature
        deflection = final_curvature * L_m**2 / 8 if final_curvature != 0 else 0.0
        deflection_mm = deflection * 1000.0
        
        return FullWeldingResult(
            heat_input_kJ_per_m=heat_input_kJ_m,
            T_max_C=T_max,
            heating=HeatingResult(
                delta0=float(delta0),
                deltah=float(deltah),
                curvature_1pm=float(initial_curvature),
                stresses_MPa=(stresses / 1e6).tolist(),
                plastic_strains_compression=plastic_strains.tolist(),
                y_coords_mm=(y_m * 1000).tolist(),
                iterations=iters,
                residual=float(residual)
            ),
            n_points=input_data.n_points,
            material=material.name,
            deflection_mm=deflection_mm,
            final_curvature_1pm=float(final_curvature),
            residual_stresses_MPa=(final_stresses / 1e6).tolist(),
            final_plastic_strains=final_plastic.tolist(),
            cooling_steps=len(curvatures)
        )
        
    except Exception as e:
        logger.exception("Full welding calculation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "ok", "service": "WeldFOAM", "stage": "heating + cooling"}
