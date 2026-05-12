# core/material_db.py
from .models import MaterialProperties

# База данных свойств материалов
MATERIALS_DB = {
    "Ст3": MaterialProperties(
        name="Ст3",
        E_GPa=210.0,
        sigma_s0_MPa=250.0,
        alpha_1perC=1.2e-5,
        lambda_W_mK=50.0,
        a_m2s=1.2e-5,
        eta=0.75,
        T0_C=20.0
    ),
    "АМг6": MaterialProperties(
        name="АМг6",
        E_GPa=71.0,
        sigma_s0_MPa=150.0,
        alpha_1perC=2.4e-5,
        lambda_W_mK=120.0,
        a_m2s=7.5e-5,
        eta=0.70,  # для MIG/MAG
        T0_C=20.0
    ),
    "12Х18Н10Т": MaterialProperties(
        name="12Х18Н10Т",
        E_GPa=193.0,
        sigma_s0_MPa=205.0,
        alpha_1perC=1.6e-5,
        lambda_W_mK=15.0,
        a_m2s=4.0e-6,
        eta=0.75,
        T0_C=20.0
    )
}

def get_material(name: str) -> MaterialProperties:
    if name not in MATERIALS_DB:
        raise ValueError(f"Material '{name}' not found. Available: {list(MATERIALS_DB.keys())}")
    return MATERIALS_DB[name]