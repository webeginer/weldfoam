import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import matplotlib.pyplot as plt
from core.history import cool_down


def test_cooling_narrow_strip():
    """Тест остывания узкой полосы (50 мм)"""
    h = 0.05
    n = 21
    y = np.linspace(0, h, n)
    T_max = 20 + 1180 * np.exp(-15 * y)
    
    print("\n" + "=" * 60)
    print("ОСТЫВАНИЕ УЗКОЙ ПОЛОСЫ (50 мм)")
    print("=" * 60)
    
    alpha = 1.2e-5
    E = 210e9
    sigma_s0 = 250e6
    thickness = 0.004
    
    final_stresses, final_plastic, curvatures, temperatures = cool_down(
        y, T_max, alpha, E, sigma_s0, thickness,
        n_steps=40, verbose=True
    )
    
    print("\n" + "-" * 60)
    print("РЕЗУЛЬТАТЫ:")
    print("-" * 60)
    print(f"Начальная кривизна: {curvatures[0]:.3e} 1/м")
    print(f"Финальная кривизна: {curvatures[-1]:.3e} 1/м")
    print(f"Макс. остаточное напряжение: {np.max(final_stresses)/1e6:.1f} МПа")
    print(f"Мин. остаточное напряжение: {np.min(final_stresses)/1e6:.1f} МПа")
    print(f"Макс. пластическая деформация: {np.max(np.abs(final_plastic)):.2e}")
    
    if curvatures[-1] > 0:
        print(f"\n✓ Остаточная кривизна положительная: {curvatures[-1]:.3e} 1/м")
    else:
        print(f"\n⚠️ Остаточная кривизна = {curvatures[-1]:.3e} (ожидалось > 0)")
    
    # Графики
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0, 0].plot(temperatures, curvatures, 'o-', linewidth=2)
    axes[0, 0].set_xlabel("Температура (°C)")
    axes[0, 0].set_ylabel("Кривизна (1/м)")
    axes[0, 0].set_title("Изменение кривизны при остывании")
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    y_mm = y * 1000
    axes[0, 1].plot(final_stresses / 1e6, y_mm, linewidth=2)
    axes[0, 1].axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    axes[0, 1].set_xlabel("Остаточное напряжение σ (МПа)")
    axes[0, 1].set_ylabel("y (мм)")
    axes[0, 1].set_title("Эпюра остаточных напряжений")
    axes[0, 1].grid(True, alpha=0.3)
    
    axes[1, 0].plot(final_plastic, y_mm, linewidth=2)
    axes[1, 0].axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    axes[1, 0].set_xlabel("Пластическая деформация ε_pl")
    axes[1, 0].set_ylabel("y (мм)")
    axes[1, 0].set_title("Остаточные пластические деформации")
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].plot(range(len(curvatures)), curvatures, 'o-', linewidth=2)
    axes[1, 1].set_xlabel("Шаг остывания")
    axes[1, 1].set_ylabel("Кривизна (1/м)")
    axes[1, 1].set_title("Кривизна по шагам")
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig("cooling_narrow_strip.png", dpi=150)
    print("\n✓ График сохранён: cooling_narrow_strip.png")
    plt.show()
    
    return curvatures[-1]


def test_cooling_wide_strip():
    """Тест остывания широкой полосы (150 мм)"""
    h = 0.15
    n = 41
    y = np.linspace(0, h, n)
    T_max = 20 + 800 * (1 - y/h)
    
    print("\n" + "=" * 60)
    print("ОСТЫВАНИЕ ШИРОКОЙ ПОЛОСЫ (150 мм)")
    print("=" * 60)
    
    alpha = 1.2e-5
    E = 210e9
    sigma_s0 = 250e6
    thickness = 0.004
    
    final_stresses, final_plastic, curvatures, temperatures = cool_down(
        y, T_max, alpha, E, sigma_s0, thickness,
        n_steps=40, verbose=True
    )
    
    print("\n" + "-" * 60)
    print("РЕЗУЛЬТАТЫ:")
    print("-" * 60)
    print(f"Начальная кривизна: {curvatures[0]:.3e} 1/м")
    print(f"Финальная кривизна: {curvatures[-1]:.3e} 1/м")
    
    if curvatures[-1] < 0:
        print(f"\n✓ Остаточная кривизна отрицательная: {curvatures[-1]:.3e} 1/м")
    else:
        print(f"\n⚠️ Остаточная кривизна = {curvatures[-1]:.3e} (ожидалось < 0)")
    
    return curvatures[-1]


if __name__ == "__main__":
    curvature_narrow = test_cooling_narrow_strip()
    curvature_wide = test_cooling_wide_strip()
    
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ВЕРДИКТ:")
    print("=" * 60)
    if curvature_narrow > 0:
        print("✓ Узкая полоса: остаточная кривизна > 0 (выгиб в сторону валика)")
    else:
        print("✗ Узкая полоса: требуется доработка")
    
    if curvature_wide < 0:
        print("✓ Широкая полоса: остаточная кривизна < 0 (выгиб в противоположную сторону)")
    else:
        print("✗ Широкая полоса: требуется доработка")
