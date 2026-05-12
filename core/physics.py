import numpy as np
from typing import Tuple

try:
    from numpy import trapezoid as trapz
except ImportError:
    from numpy import trapz


def yield_stress(T: float, sigma_s0: float) -> float:
    if T < 500:
        return sigma_s0
    elif T <= 600:
        return sigma_s0 * (600 - T) / 100
    else:
        return 0.0


def compute_residuals(
    delta0: float,
    deltah: float,
    y: np.ndarray,
    T: np.ndarray,
    alpha: float,
    E: float,
    sigma_s0: float,
    thickness: float = 1.0,
):
    h = y[-1] - y[0]
    if h <= 0:
        return 1e12, 1e12, np.zeros_like(y), np.zeros_like(y)
    
    n = len(y)
    stresses = np.zeros(n)
    plastic = np.zeros(n)
    
    for i in range(n):
        delta_i = delta0 + (deltah - delta0) * y[i] / h
        lambda_i = alpha * T[i]
        eps_e = delta_i - lambda_i
        
        sigma_s = yield_stress(T[i], sigma_s0)
        eps_s = sigma_s / E if sigma_s > 0 else 0.0
        
        if abs(eps_e) <= eps_s + 1e-12:
            stresses[i] = E * eps_e
            plastic[i] = 0.0
        else:
            stresses[i] = np.sign(eps_e) * sigma_s
            plastic[i] = eps_e - np.sign(eps_e) * eps_s
    
    F1 = trapz(stresses, y) * thickness
    F2 = trapz(stresses * y, y) * thickness
    
    return F1, F2, stresses, plastic


def solve_heating_robust(
    y: np.ndarray,
    T: np.ndarray,
    alpha: float,
    E: float,
    sigma_s0: float,
    thickness: float = 1.0,
    n_grid: int = 30,
    verbose: bool = False,
) -> Tuple[float, float, np.ndarray, np.ndarray, int, float]:
    """
    Подбор Δ0, Δh прямым перебором с проверкой равновесия.
    """
    h = y[-1] - y[0]
    lam = alpha * T
    
    # Диапазон поиска: расширенный от мин до макс тепловой деформации
    lam_min = np.min(lam)
    lam_max = np.max(lam)
    lam_mean = np.mean(lam)
    
    # Расширяем диапазон на 100% для учёта пластики (увеличил с 20% до 100%)
    margin = (lam_max - lam_min) * 1.0
    delta_min = lam_min - margin
    delta_max = lam_max + margin
    
    if verbose:
        print(f"Поиск Δ0, Δh в диапазоне [{delta_min:.4f}, {delta_max:.4f}]")
    
    # Сетка перебора
    grid = np.linspace(delta_min, delta_max, n_grid)
    
    best_residual = np.inf
    best_delta0 = lam_mean
    best_deltah = lam_mean
    best_F1 = 0
    best_F2 = 0
    best_stresses = None
    best_plastic = None
    
    # Грубый перебор
    for delta0 in grid:
        for deltah in grid:
            F1, F2, stresses, plastic = compute_residuals(
                delta0, deltah, y, T, alpha, E, sigma_s0, thickness
            )
            residual = abs(F1) + abs(F2)
            
            if residual < best_residual:
                best_residual = residual
                best_delta0 = delta0
                best_deltah = deltah
                best_F1 = F1
                best_F2 = F2
                best_stresses = stresses.copy()
                best_plastic = plastic.copy()
                
                if residual < 100.0:  # Инженерная точность
                    if verbose:
                        print(f"  Ранний выход: residual={residual:.1f} Н")
                    break
        else:
            continue
        break
    
    if verbose:
        print(f"Результат: Δ0={best_delta0:.6f}, Δh={best_deltah:.6f}")
        print(f"  Невязка: F1={best_F1:.2f} Н, F2={best_F2:.2f} Н⋅м")
    
    curvature = (best_deltah - best_delta0) / h
    
    return best_delta0, best_deltah, best_stresses, best_plastic, n_grid * n_grid, best_residual


solve_heating = solve_heating_robust
