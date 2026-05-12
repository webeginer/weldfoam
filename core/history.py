import numpy as np
from typing import List, Tuple
from dataclasses import dataclass

try:
    from numpy import trapezoid as trapz
except ImportError:
    from numpy import trapz


@dataclass
class FiberState:
    y: float
    T: float
    eps_total: float
    eps_plastic: float
    eps_elastic: float
    stress: float
    is_yield: bool


class HistoryTracker:
    def __init__(self, y: np.ndarray, T_initial: np.ndarray, alpha: float, E: float, sigma_s0: float):
        self.n = len(y)
        self.y = y
        self.alpha = alpha
        self.E = E
        self.sigma_s0 = sigma_s0
        self.fibers: List[FiberState] = []
        
        for i in range(self.n):
            self.fibers.append(FiberState(
                y=y[i],
                T=T_initial[i],
                eps_total=0.0,
                eps_plastic=0.0,
                eps_elastic=0.0,
                stress=0.0,
                is_yield=False
            ))
    
    def _yield_stress(self, T: float) -> float:
        if T < 500:
            return self.sigma_s0
        elif T <= 600:
            return self.sigma_s0 * (600 - T) / 100
        else:
            return 0.0
    
    def update(self, delta0: float, deltah: float, T_new: np.ndarray) -> np.ndarray:
        """Обновляет состояние волокон при заданных деформациях сечения."""
        h = self.y[-1] - self.y[0]
        if h <= 0:
            return np.zeros(self.n)
        
        stresses = np.zeros(self.n)
        
        for i, fiber in enumerate(self.fibers):
            eps_total_new = delta0 + (deltah - delta0) * fiber.y / h
            lambda_old = self.alpha * fiber.T
            lambda_new = self.alpha * T_new[i]
            
            # Пробное упругое решение
            stress_trial = fiber.stress + self.E * ((eps_total_new - lambda_new) - (fiber.eps_total - lambda_old))
            sigma_s = self._yield_stress(T_new[i])
            
            if abs(stress_trial) <= sigma_s + 1e-12:
                fiber.stress = stress_trial
                fiber.is_yield = False
            else:
                fiber.stress = np.sign(stress_trial) * sigma_s
                fiber.is_yield = True
            
            fiber.eps_total = eps_total_new
            fiber.T = T_new[i]
            fiber.eps_elastic = fiber.stress / self.E
            fiber.eps_plastic = fiber.eps_total - fiber.eps_elastic - lambda_new
            
            stresses[i] = fiber.stress
        
        return stresses
    
    def get_plastic_strains(self) -> np.ndarray:
        return np.array([f.eps_plastic for f in self.fibers])
    
    def get_stresses(self) -> np.ndarray:
        return np.array([f.stress for f in self.fibers])


def cool_down(
    y: np.ndarray,
    T_max: np.ndarray,
    alpha: float,
    E: float,
    sigma_s0: float,
    thickness: float = 1.0,
    n_steps: int = 40,
    verbose: bool = False,
) -> Tuple[np.ndarray, np.ndarray, List[float], List[float]]:
    """
    Пошаговое остывание с фиксированными деформациями сечения.
    Деформации сечения берутся из этапа нагрева и НЕ пересчитываются.
    """
    from core.physics import solve_heating
    
    h = y[-1] - y[0]
    T_min = 20.0
    T_steps = np.linspace(T_max[0], T_min, n_steps)
    
    # Начальные деформации сечения (из этапа нагрева)
    delta0, deltah, _, _, _, _ = solve_heating(
        y, T_max, alpha, E, sigma_s0, thickness, n_grid=30, verbose=False
    )
    
    initial_curvature = (deltah - delta0) / h
    
    if verbose:
        print(f"Начальные деформации: Δ0={delta0:.6f}, Δh={deltah:.6f}, C={initial_curvature:.3e}")
    
    tracker = HistoryTracker(y, T_max, alpha, E, sigma_s0)
    
    curvatures = []
    temperatures = []
    
    for step, T_curr in enumerate(T_steps):
        if T_max[0] > 20:
            scale = (T_curr - 20) / (T_max[0] - 20)
            scale = max(0.0, min(1.0, scale))
        else:
            scale = 0.0
        
        T_profile = 20 + scale * (T_max - 20)
        T_profile = np.maximum(T_profile, 20.0)
        
        # Обновляем состояния (деформации сечения НЕ меняются)
        stresses = tracker.update(delta0, deltah, T_profile)
        
        curvature = (deltah - delta0) / h
        curvatures.append(curvature)
        temperatures.append(T_curr)
        
        if verbose and step % 10 == 0:
            print(f"Шаг {step}: T={T_curr:.0f}°C, C={curvature:.3e}")
    
    final_stresses = tracker.get_stresses()
    final_plastic = tracker.get_plastic_strains()
    
    return final_stresses, final_plastic, curvatures, temperatures
