import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from core.physics import solve_heating

print("=" * 60)
print("ДИАГНОСТИКА ЗНАКА solve_heating")
print("=" * 60)

# Узкая полоса (50 мм) - ожидается delta0 < deltah (curvature > 0)
h_narrow = 0.05
y_narrow = np.linspace(0, h_narrow, 21)
T_narrow = 20 + 1180 * np.exp(-15 * y_narrow)

delta0_narrow, deltah_narrow, stresses_narrow, _, _, _ = solve_heating(
    y_narrow, T_narrow, 1.2e-5, 210e9, 250e6, 0.004, n_grid=30, verbose=False
)

curvature_narrow = (deltah_narrow - delta0_narrow) / h_narrow

print("\nУЗКАЯ ПОЛОСА (50 мм):")
print(f"  delta0 (y=0, горячая) = {delta0_narrow:.6f}")
print(f"  deltah (y=h, холодная) = {deltah_narrow:.6f}")
print(f"  Кривизна = {curvature_narrow:.3e} 1/м")

# Широкая полоса (150 мм) - ожидается delta0 > deltah (curvature < 0)
h_wide = 0.15
y_wide = np.linspace(0, h_wide, 41)
T_wide = 20 + 800 * (1 - y_wide / h_wide)

delta0_wide, deltah_wide, stresses_wide, _, _, _ = solve_heating(
    y_wide, T_wide, 1.2e-5, 210e9, 250e6, 0.004, n_grid=30, verbose=False
)

curvature_wide = (deltah_wide - delta0_wide) / h_wide

print("\nШИРОКАЯ ПОЛОСА (150 мм):")
print(f"  delta0 (y=0, горячая) = {delta0_wide:.6f}")
print(f"  deltah (y=h, холодная) = {deltah_wide:.6f}")
print(f"  Кривизна = {curvature_wide:.3e} 1/м")

print("\n" + "=" * 60)
print("ВЫВОД:")
print("=" * 60)

# Правильные проверки
narrow_correct = curvature_narrow > 0
wide_correct = curvature_wide < 0

if narrow_correct:
    print("✓ Узкая полоса (50 мм): curvature > 0 - ПРАВИЛЬНО!")
    print("  (горячая кромка короче холодной, выгиб в сторону валика)")
else:
    print("✗ Узкая полоса (50 мм): curvature < 0 - НЕПРАВИЛЬНО!")

if wide_correct:
    print("✓ Широкая полоса (150 мм): curvature < 0 - ПРАВИЛЬНО!")
    print("  (горячая кромка длиннее холодной, выгиб в противоположную сторону)")
else:
    print("✗ Широкая полоса (150 мм): curvature > 0 - НЕПРАВИЛЬНО!")

print("\n" + "=" * 60)

if narrow_correct and wide_correct:
    print("\n🎉 solve_heating работает КОРРЕКТНО!")
    print("   Знаки кривизны соответствуют Окерблому.")
    print("   Можно переходить к этапу 2 (остывание).")
else:
    print("\n⚠️ Требуется исправление physics.py")
